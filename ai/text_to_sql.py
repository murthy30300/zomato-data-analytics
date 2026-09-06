import os
import json
import time
import re
import subprocess
import sys

import pandas as pd
import streamlit as st
import snowflake.connector

from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

MODEL = "Qwen/Qwen2.5-7B-Instruct"

FORBIDDEN_WORDS = {
    "drop",
    "delete",
    "truncate",
    "alter",
    "update",
    "insert",
    "create",
    "replace",
    "grant",
    "revoke",
}

EXAMPLE_QUESTIONS = [
    "Top 10 cities by GMV",
    "Which cuisine has the most orders?",
    "Average delivery time by city, worst first",
    "Cancel rate by payment method",
]


# ============================================================
# STREAMLIT CONFIG
# ============================================================

st.set_page_config(
    page_title="Chat with Zomato Data",
    page_icon="🍴",
    layout="wide",
)


# ============================================================
# SNOWFLAKE SCHEMA
# ============================================================
SCHEMA = """
Tables available (Snowflake). Use bare table names, no database or schema prefix.
 
FCT_ORDERS(order_id, order_date, customer_id, restaurant_id, city, cuisine,
           payment_method, order_status, is_delivered, sales_amount, discount,
           delivery_fee, gst, customer_rating, delivery_time_min)
DIM_RESTAURANT(restaurant_id, restaurant_name, city, cuisine, rating, cost_for_two)
DIM_CUSTOMER(customer_id, customer_name, age, age_segment, gender, city)
MART_DAILY_CITY_REVENUE(order_date, city, orders, cancel_rate, gmv, aov)
MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine,
                            orders, revenue, avg_customer_rating, cancel_rate)
MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50_delivery_min, late_rate)

 
Note: gmv means delivered revenue. Prefer the MART_ tables when they fit the question.
"""


# ============================================================
# GENERATE SQL THROUGH SEPARATE WORKER PROCESS
# ============================================================

def generate_sql(question):
    """
    Run hf_worker.py in a completely separate Python process.

    This prevents the Hugging Face SDK from running inside
    the Streamlit process.
    """

    print("\n" + "=" * 60)
    print("[DEBUG] generate_sql()")
    print("=" * 60)

    print(f"[DEBUG] Question: {question}")
    print(f"[DEBUG] Model: {MODEL}")

    # --------------------------------------------------------
    # Locate worker
    # --------------------------------------------------------

    worker_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "hf_worker.py",
    )

    print(
        f"[DEBUG] Worker path: {worker_path}"
    )

    if not os.path.exists(worker_path):

        raise FileNotFoundError(
            f"hf_worker.py was not found at:\n"
            f"{worker_path}"
        )

    # --------------------------------------------------------
    # Run worker
    # --------------------------------------------------------

    start = time.time()

    print(
        "[DEBUG] Starting HF worker process..."
    )

    try:

        result = subprocess.run(
            [
                sys.executable,
                worker_path,
                question,
            ],
            capture_output=True,
            text=True,
            timeout=45,
            cwd=os.path.dirname(
                os.path.abspath(__file__)
            ),
        )

    except subprocess.TimeoutExpired as e:

        elapsed = time.time() - start

        print(
            f"[DEBUG] HF worker timed out "
            f"after {elapsed:.2f}s"
        )

        raise TimeoutError(
            "Hugging Face worker timed out after 45 seconds."
        ) from e

    elapsed = time.time() - start

    print(
        f"[DEBUG] HF worker finished "
        f"in {elapsed:.2f}s"
    )

    # --------------------------------------------------------
    # Show worker logs
    # --------------------------------------------------------

    if result.stderr:

        print(
            "[DEBUG] Worker stderr:"
        )

        print(
            result.stderr
        )

    # --------------------------------------------------------
    # Check exit status
    # --------------------------------------------------------

    if result.returncode != 0:

        error_message = (
            result.stdout.strip()
            or result.stderr.strip()
            or "HF worker failed."
        )

        print(
            f"[DEBUG] Worker exit code: "
            f"{result.returncode}"
        )

        raise RuntimeError(
            error_message
        )

    # --------------------------------------------------------
    # Parse worker stdout
    # --------------------------------------------------------

    output = result.stdout.strip()

    print(
        f"[DEBUG] Worker stdout: {output}"
    )

    try:

        data = json.loads(output)

    except json.JSONDecodeError as e:

        raise ValueError(
            "HF worker returned invalid JSON.\n\n"
            f"Output:\n{output}"
        ) from e

    # --------------------------------------------------------
    # Worker error
    # --------------------------------------------------------

    if "error" in data:

        raise RuntimeError(
            data["error"]
        )

    # --------------------------------------------------------
    # SQL
    # --------------------------------------------------------

    if "sql" not in data:

        raise ValueError(
            "HF worker response does not contain 'sql'."
        )

    sql = data["sql"]

    if not isinstance(sql, str):

        raise ValueError(
            "The SQL returned by HF worker is not a string."
        )

    sql = sql.strip().rstrip(";")

    print(
        f"[DEBUG] Generated SQL: {sql}"
    )

    return sql


# ============================================================
# SQL SAFETY
# ============================================================

def is_safe(sql):

    print(
        "[DEBUG] Checking SQL safety..."
    )

    sql = sql.strip()

    lowered = sql.lower()

    # --------------------------------------------------------
    # Must start with SELECT or WITH
    # --------------------------------------------------------

    if not (
        lowered.startswith("select")
        or lowered.startswith("with")
    ):

        print(
            "[DEBUG] Safety FAILED: "
            "query is not SELECT/WITH"
        )

        return False

    # --------------------------------------------------------
    # Remove single-line comments
    # --------------------------------------------------------

    cleaned = re.sub(
        r"--.*",
        "",
        lowered,
    )

    # --------------------------------------------------------
    # Extract SQL words
    # --------------------------------------------------------

    tokens = set(
        re.findall(
            r"\b[a-z_]+\b",
            cleaned,
        )
    )

    forbidden_found = (
        tokens.intersection(
            FORBIDDEN_WORDS
        )
    )

    if forbidden_found:

        print(
            "[DEBUG] Safety FAILED: "
            f"forbidden keywords = "
            f"{sorted(forbidden_found)}"
        )

        return False

    print(
        "[DEBUG] Safety PASSED"
    )

    return True


# ============================================================
# SNOWFLAKE PRIVATE KEY
# ============================================================

def get_private_key():

    key_path = os.getenv(
        "SNOWFLAKE_PRIVATE_KEY_PATH"
    )

    if not key_path:

        raise ValueError(
            "SNOWFLAKE_PRIVATE_KEY_PATH is not set."
        )

    print(
        f"[DEBUG] Loading private key: "
        f"{key_path}"
    )

    with open(
        key_path,
        "rb",
    ) as key_file:

        p_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

    print(
        "[DEBUG] Private key loaded"
    )

    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():

    print(
        "[DEBUG] Opening Snowflake connection..."
    )

    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=get_private_key(),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema="MARTS",
        role="DBT_ROLE",
    )

    print(
        "[DEBUG] Snowflake connection established"
    )

    return conn


# ============================================================
# RUN QUERY
# ============================================================

def run_query(sql):

    print("\n" + "=" * 60)
    print("[DEBUG] run_query()")
    print("=" * 60)

    print(
        f"[DEBUG] SQL: {sql}"
    )

    start = time.time()

    conn = get_connection()

    cursor = conn.cursor()

    try:

        df = cursor.execute(
            sql
        ).fetch_pandas_all()

        elapsed = time.time() - start

        print(
            f"[DEBUG] Snowflake query completed "
            f"in {elapsed:.2f}s"
        )

        print(
            f"[DEBUG] Rows returned: "
            f"{len(df)}"
        )

        return df

    finally:

        cursor.close()


# ============================================================
# UI
# ============================================================

st.title(
    "🍴 Chat with your Zomato data"
)

st.caption(
    f"Ask in English → {MODEL} generates SQL → "
    "Snowflake executes it"
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "Example questions"
    )

    for q in EXAMPLE_QUESTIONS:

        st.markdown(
            f"- {q}"
        )


# ============================================================
# INPUT FORM
# ============================================================

with st.form(
    "question_form"
):

    question = st.text_input(
        "Enter your question",
        placeholder=(
            "e.g. Top 10 restaurants by revenue in Bangalore"
        ),
    )

    submitted = st.form_submit_button(
        "Ask"
    )


# ============================================================
# PROCESS QUESTION
# ============================================================

if submitted and question.strip():

    question = question.strip()

    # --------------------------------------------------------
    # Generate SQL
    # --------------------------------------------------------

    try:

        with st.spinner(
            "Generating SQL..."
        ):

            sql = generate_sql(
                question
            )

    except Exception as e:

        print(
            f"[DEBUG] generate_sql() failed: "
            f"{type(e).__name__}: {e}"
        )

        st.error(
            f"Error generating SQL: {e}"
        )

        st.stop()

    # --------------------------------------------------------
    # Display SQL
    # --------------------------------------------------------

    st.subheader(
        "Generated SQL"
    )

    st.code(
        sql,
        language="sql",
    )

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if not is_safe(sql):

        st.error(
            "The generated SQL failed the safety check."
        )

        st.stop()

    st.success(
        "SQL passed the safety check."
    )

    # --------------------------------------------------------
    # Run Snowflake
    # --------------------------------------------------------

    try:

        with st.spinner(
            "Running query in Snowflake..."
        ):

            df = run_query(sql)

    except Exception as e:

        print(
            f"[DEBUG] run_query() failed: "
            f"{type(e).__name__}: {e}"
        )

        st.error(
            f"Error running query: {e}"
        )

        st.stop()

    # --------------------------------------------------------
    # Results
    # --------------------------------------------------------

    st.success(
        f"{len(df)} rows returned"
    )

    st.subheader(
        "Results"
    )

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # Chart
    # --------------------------------------------------------

    if (
        len(df.columns) == 2
        and len(df) > 0
        and pd.api.types.is_numeric_dtype(
            df.iloc[:, 1]
        )
    ):

        st.subheader(
            "Chart"
        )

        st.bar_chart(
            df,
            x=df.columns[0],
            y=df.columns[1],
        )