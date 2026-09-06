import os
import time
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

MODEL = "Qwen/Qwen2.5-7B-Instruct"

client = InferenceClient(
    provider="together",
    api_key=os.getenv("HF_ZOM"),
    timeout=30
)

SCHEMA = """
Tables available (Snowflake).

FCT_ORDERS(order_id, order_date, customer_id, restaurant_id, city, cuisine,
           payment_method, order_status, is_delivered, sales_amount, discount,
           delivery_fee, gst, customer_rating, delivery_time_min)

DIM_RESTAURANT(restaurant_id, restaurant_name, city, cuisine, rating, cost_for_two)

DIM_CUSTOMER(customer_id, customer_name, age, age_segment, gender, city)

MART_DAILY_CITY_REVENUNE(order_date, city, orders, cancel_rate, gmv, aov)

MART_RESTAURANT_PERFORMANCE(restaurant_id, restaurant_name, city, cuisine,
                            orders, revenue, avg_customer_rating, cancel_rate)

MART_DELIVERY_SLA(city, order_hour, delivered_orders, p50_delivery_min, late_rate)
"""

SYSTEM_PROMPT = f"""
You are a Snowflake SQL expert. Write ONE SELECT query that answers the question.

Rules:
- SELECT queries only, never modify data.
- Use bare table names.
- Add a LIMIT of 100 or less, unless the question asks for a single total.
- Reply as JSON in this exact format: {{"sql": "your query here"}}

{SCHEMA}
"""

question = "Average delivery time by city, worst first"

print("Starting...")
print("API key exists:", bool(os.getenv("HF_ZOM")))
print("Model:", MODEL)
print("Prompt length:", len(SYSTEM_PROMPT))

start = time.time()

try:
    print("Calling Hugging Face...")

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": question
            }
        ]
    )

    print(f"Done in {time.time() - start:.2f}s")
    print("Response:")
    print(response)

    print("\nCONTENT:")
    print(response.choices[0].message.content)

except Exception as e:
    print(f"FAILED after {time.time() - start:.2f}s")
    print(type(e).__name__)
    print(repr(e))