import os
import sys
import json

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


MODEL = "Qwen/Qwen2.5-7B-Instruct"

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

SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.
 
Rules:
- SELECT queries only, never modify data.
- Use bare table names (FCT_ORDERS, not ZOMATO.MARTS.FCT_ORDERS).
- Add a LIMIT of 100 or less, unless the question asks for a single total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}
 
{SCHEMA}
"""


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print(json.dumps({"error": "No question supplied"}))
        sys.exit(1)

    question = sys.argv[1]

    api_key = os.getenv("HF_ZOM")

    if not api_key:
        print(json.dumps({"error": "HF_ZOM is not set"}))
        sys.exit(1)

    try:
        print("[WORKER] Creating HF client...", file=sys.stderr)

        client = InferenceClient(
            provider="auto",
            api_key=api_key,
            timeout=30,
        )

        print("[WORKER] Calling Hugging Face...", file=sys.stderr)

        response = client.chat.completions.create(
            model=MODEL,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
        )

        print("[WORKER] HF response received", file=sys.stderr)

        answer = response.choices[0].message.content

        parsed = json.loads(answer)

        if "sql" not in parsed:
            raise ValueError("Model response does not contain 'sql'")

        sql = parsed["sql"]

        if not isinstance(sql, str):
            raise ValueError("'sql' must be a string")

        sql = sql.replace("ZOMATO.MARTS.", "")
        sql = sql.replace("ZOMATO.MARTS", "")
        sql = sql.replace("ZOMATO.", "")
        sql = sql.strip().rstrip(";")

        # stdout is reserved for machine-readable JSON.
        print(json.dumps({"sql": sql}))

    except Exception as e:
        print(
            json.dumps(
                {
                    "error": f"{type(e).__name__}: {str(e)}"
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
