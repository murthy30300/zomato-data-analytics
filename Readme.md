🍽️ Zomato AI Data Engineering — End-to-End Data Pipeline

An end-to-end Data Engineering and AI Analytics project that processes Zomato-style food delivery data from raw CSV files into a cloud-based data warehouse and delivers business insights using AWS S3, Snowflake, dbt, Apache Airflow, OpenAI, and Streamlit.

The project demonstrates a modern data engineering architecture using a Medallion Architecture (Bronze → Silver → Gold) along with AI-powered capabilities such as LLM-based review enrichment, RAG, and Text-to-SQL.

---

📌 Project Overview

This project builds a complete batch data pipeline for a food delivery platform.

The pipeline takes raw datasets containing restaurants, customers, food items, menus, orders, order items, and reviews and processes them through multiple stages:

Raw CSV Data
     │
     ▼
 Amazon S3
     │
     ▼
 Snowflake RAW
   (Bronze)
     │
     ▼
     dbt
     │
     ▼
 Snowflake STAGING
   (Silver)
     │
     ▼
 Snowflake MARTS
    (Gold)
     │
     ├───────────────┐
     ▼               ▼
 OpenAI AI Layer   Analytics
     │
     ├── Review Enrichment
     ├── RAG Chat
     └── Text-to-SQL
             │
             ▼
         Streamlit

Apache Airflow orchestrates the complete pipeline.

---

🏗️ Architecture

"Architecture" (docs/architecture.png)

High-Level Architecture

                   ┌─────────────────────┐
                   │   Source CSV Files  │
                   │                     │
                   │ Restaurants         │
                   │ Users               │
                   │ Food                │
                   │ Menu                │
                   │ Orders              │
                   │ Order Items         │
                   │ Reviews             │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │     Amazon S3       │
                   │     Data Lake       │
                   └──────────┬──────────┘
                              │
                     Storage Integration
                              │
                              ▼
                   ┌─────────────────────┐
                   │     Snowflake       │
                   │                     │
                   │ RAW / Bronze        │
                   └──────────┬──────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │        dbt          │
                   │                     │
                   │ STAGING / Silver    │
                   │ MARTS / Gold        │
                   └──────────┬──────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
       ┌─────────────────┐       ┌─────────────────┐
       │     AI Layer    │       │    BI / Data    │
       │                 │       │    Analytics    │
       │ LLM Enrichment  │       │                 │
       │ RAG             │       │ Business Marts  │
       │ Text-to-SQL     │       │                 │
       └────────┬────────┘       └─────────────────┘
                │
                ▼
       ┌─────────────────┐
       │    Streamlit    │
       │   AI Apps       │
       └─────────────────┘

                 ▲
                 │
       ┌─────────────────┐
       │ Apache Airflow  │
       │  Orchestration  │
       └─────────────────┘

---

🛠️ Technology Stack

Technology| Purpose
Python| Data processing and AI applications
Pandas| Data manipulation
Amazon S3| Cloud data lake
Snowflake| Cloud data warehouse
dbt| Data transformation and testing
Apache Airflow| Pipeline orchestration
Docker| Containerization
OpenAI API| LLM-powered analytics
Streamlit| Interactive AI applications
SQL| Data transformation and analytics
Git/GitHub| Version control

---

📊 Dataset

The project works with Zomato-style food delivery data consisting of:

- Restaurants
- Customers / Users
- Food items
- Menus
- Orders
- Order items
- Customer reviews

The dataset contains large-scale fact data to demonstrate real-world data engineering concepts.

Approximate Data Volume

Dataset| Approximate Records
Orders| 10 Million
Order Items| 23 Million
Reviews| 300,000
Restaurants| Dimension data
Users| Dimension data
Food| Dimension data
Menu| Dimension data

«Large CSV files are intentionally excluded from Git to avoid committing multi-GB datasets.»

---

🗂️ Repository Structure

zomato-ai-data-engineering/
│
├── airflow/
│   ├── dags/
│   │   └── zomato_batch.py
│   ├── Dockerfile
│   ├── docker-compose.yaml
│   └── example.env
│
├── ai/
│   ├── enrich_reviews.py
│   ├── rag_chat.py
│   ├── text_to_sql.py
│   └── example.env
│
├── aws/
│   └── iam/
│       ├── s3-read-policy.json
│       ├── snowflake-role-trust-policy-initial.json
│       └── snowflake-role-trust-policy-final.json
│
├── snowflake/
│   ├── 01_setup.sql
│   ├── 02_storage_integration.sql
│   ├── 03_stage_and_formats.sql
│   ├── 04_raw_tables.sql
│   └── 05_copy_into.sql
│
├── zomato/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── macros/
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── docs/
│   └── architecture.png
│
├── data/
│   └── *.csv
│
├── .gitignore
└── README.md

---

🔄 End-to-End Data Pipeline

1. 📥 Data Ingestion

The pipeline starts with raw CSV files containing Zomato-style food delivery data.

The datasets are organized by table:

data/
├── restaurants.csv
├── users.csv
├── food.csv
├── menu.csv
├── orders.csv
├── order_items.csv
└── reviews.csv

The files are uploaded to Amazon S3.

---

☁️ 2. Amazon S3 Data Lake

Amazon S3 acts as the project's cloud data lake.

Files are organized using a table-based folder structure:

s3://<BUCKET>/raw/
│
├── restaurants/
├── users/
├── food/
├── menu/
├── orders/
├── order_items/
└── reviews/

This provides a scalable and centralized location for raw data.

---

❄️ 3. Snowflake Data Warehouse

Snowflake is used as the central analytical data warehouse.

The project creates the following schemas:

ZOMATO
│
├── RAW
├── STAGING
├── MARTS
├── SNAPSHOTS
└── AI

RAW — Bronze Layer

Raw data is loaded from Amazon S3 into Snowflake using:

COPY INTO

The Snowflake-S3 connection uses a Storage Integration and AWS IAM Role, avoiding the need to store AWS access keys inside the project.

---

🥉 4. Bronze Layer — RAW

The Bronze layer contains data as it arrives from the source.

Example:

ZOMATO.RAW.ORDERS
ZOMATO.RAW.ORDER_ITEMS
ZOMATO.RAW.RESTAURANTS
ZOMATO.RAW.USERS
ZOMATO.RAW.FOOD
ZOMATO.RAW.MENU
ZOMATO.RAW.REVIEWS

The objective of this layer is to preserve the original source data.

---

🥈 5. Silver Layer — STAGING

dbt is used to transform the RAW data into clean and standardized staging models.

Examples of transformations include:

- Data type conversion
- Column renaming
- Null handling
- Email standardization
- Currency cleanup
- Deriving delivery status
- Cleaning restaurant attributes
- Standardizing source values

Example:

RAW
 ↓
STAGING
 ↓
Clean and standardized data

The staging layer primarily uses dbt views.

---

🥇 6. Gold Layer — MARTS

The Gold layer contains business-ready analytical datasets.

Dimension Models

dim_restaurants
dim_customer
dim_food
dim_date

Fact Models

fct_orders
fact_order_items

Fact tables use dbt's incremental materialization with a MERGE strategy.

This avoids rebuilding millions of records every time the pipeline runs.

---

📈 Business Analytics Marts

The project creates business-focused marts to answer important questions.

Daily City Revenue

Provides metrics such as:

- GMV
- Revenue
- Average Order Value
- Cancellation Rate
- Daily performance

Restaurant Performance

Helps analyze:

- Restaurant revenue
- Order volume
- Customer activity
- Restaurant performance

Delivery SLA

Analyzes delivery performance using:

- Median delivery time
- P50 delivery time
- P90 delivery time
- City-level performance
- Hour-level performance

Review Insights

Combines customer reviews with AI-generated information for review analysis.

---

🔧 7. dbt

dbt is responsible for:

- Data transformation
- Model dependency management
- Incremental loading
- Data quality testing
- Documentation
- Business logic

dbt Tests

The project includes tests such as:

unique
not_null
relationships
accepted_values

A custom reconciliation test is also included to validate data consistency.

Run dbt with:

cd zomato

dbt debug

dbt build --exclude tag:ai

---

⚙️ 8. Apache Airflow

Apache Airflow orchestrates the entire batch pipeline.

The main DAG is:

zomato_batch

Pipeline DAG

┌───────────────┐
│  reload_raw   │
└───────┬───────┘
        │
        ▼
┌────────────────────┐
│ dbt_build_core     │
│                    │
│ dbt build + tests  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ enrich_reviews     │
│                    │
│ OpenAI enrichment  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ dbt_build_ai       │
│                    │
│ AI marts           │
└────────────────────┘

Airflow provides:

- Scheduling
- Dependency management
- Task execution
- Logging
- Failure handling
- Pipeline monitoring

---

🤖 9. AI Layer

One of the key components of this project is the AI layer.

The AI functionality consists of three major components.

---

🧠 A. LLM Review Enrichment

The "enrich_reviews.py" script uses an OpenAI model to analyze customer reviews.

Raw review text:

"The food was amazing but delivery was very late."

The LLM converts the review into structured information such as:

{
  "sentiment": "negative",
  "topic": "delivery"
}

The enriched information is stored in:

ZOMATO.AI.REVIEW_ENRICHED

This allows unstructured customer feedback to become queryable analytical data.

---

🔎 B. RAG — Chat With Reviews

The RAG application allows users to ask questions about customer reviews.

Example questions:

What are customers complaining about most?

What do customers like about the food?

Which restaurants have the most positive reviews?

What are the major delivery-related complaints?

The application:

User Question
      ↓
Create Embedding
      ↓
Retrieve Similar Reviews
      ↓
LLM Context
      ↓
Generate Answer
      ↓
Display Sources

This provides answers grounded in the actual review dataset.

The application is built using Streamlit.

Run:

streamlit run ai/rag_chat.py

---

💬 C. Text-to-SQL

The Text-to-SQL application allows users to query the Snowflake warehouse using natural language.

Example:

Which city generated the highest revenue last month?

The AI converts the question into SQL:

SELECT
    city,
    SUM(revenue) AS total_revenue
FROM mart_daily_city_revenue
GROUP BY city
ORDER BY total_revenue DESC
LIMIT 1;

The generated SQL is validated using a SELECT-only safety guard before execution.

Run:

streamlit run ai/text_to_sql.py

---

🔐 Security

Credentials are not hard-coded into the source code.

Environment variables are used for:

SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_PASSWORD
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
SNOWFLAKE_WAREHOUSE
OPENAI_API_KEY

For local development:

cp airflow/example.env airflow/.env

Then configure the required credentials.

«Never commit ".env" files, passwords, API keys, AWS credentials, or Snowflake credentials to GitHub.»

---

🚀 Setup & Installation

Prerequisites

Install the following:

- Python 3.x
- Docker
- Docker Compose
- Git
- Snowflake account
- AWS account
- OpenAI API key
- dbt with Snowflake adapter

---

1️⃣ Clone the Repository

git clone <YOUR_REPOSITORY_URL>

cd zomato-ai-data-engineering

---

2️⃣ Configure AWS

Create an S3 bucket and upload the datasets under:

raw/restaurants/
raw/users/
raw/food/
raw/menu/
raw/orders/
raw/order_items/
raw/reviews/

Configure the required IAM policy and role using:

aws/iam/

---

3️⃣ Configure Snowflake

Execute the SQL scripts in the following order:

snowflake/01_setup.sql
snowflake/02_storage_integration.sql
snowflake/03_stage_and_formats.sql
snowflake/04_raw_tables.sql
snowflake/05_copy_into.sql

Important

The S3 → Snowflake integration uses a keyless IAM-based authentication mechanism.

The trust relationship must use the IAM user ARN and external ID provided by Snowflake's storage integration.

---

4️⃣ Configure dbt

Navigate to:

cd zomato

Configure your Snowflake credentials.

Then run:

dbt debug

If everything is configured correctly:

Connection test: OK

Run the transformation:

dbt build --exclude tag:ai

---

5️⃣ Start Airflow

Navigate to:

cd airflow

Create the environment file:

cp example.env .env

Configure:

SNOWFLAKE_*
OPENAI_API_KEY
SAMPLE_N

Build the Docker environment:

docker compose build

Start Airflow:

docker compose up -d

Open:

http://localhost:8080

Then:

1. Open the Airflow UI
2. Locate "zomato_batch"
3. Unpause the DAG
4. Trigger the pipeline

---

6️⃣ Run AI Review Enrichment

Set the OpenAI API key:

export OPENAI_API_KEY=sk-...

Run:

python ai/enrich_reviews.py

---

7️⃣ Run RAG Application

streamlit run ai/rag_chat.py

---

8️⃣ Run Text-to-SQL Application

streamlit run ai/text_to_sql.py

---

📊 Key Data Engineering Concepts Demonstrated

This project demonstrates several real-world data engineering concepts:

Data Engineering

- Batch data processing
- ETL / ELT
- Data lake architecture
- Cloud data warehouse
- Large-scale datasets
- Incremental processing
- MERGE strategy

AWS

- Amazon S3
- IAM
- IAM policies
- IAM roles
- Trust relationships
- Snowflake Storage Integration

Snowflake

- Warehouses
- Databases
- Schemas
- External stages
- File formats
- COPY INTO
- Storage integrations
- Role-based access

dbt

- Staging models
- Dimension models
- Fact models
- Incremental models
- Snapshots
- Macros
- Tests
- Dependency management

Airflow

- DAGs
- Task dependencies
- Scheduling
- Docker deployment
- Pipeline orchestration
- Failure handling

AI / GenAI

- LLM data enrichment
- Structured output generation
- Embeddings
- Retrieval-Augmented Generation
- Natural Language → SQL
- SQL validation
- AI-powered analytics

---

📌 Key Features

✅ End-to-end cloud data pipeline

✅ Amazon S3 data lake

✅ Snowflake cloud data warehouse

✅ Medallion architecture

✅ dbt transformations

✅ Incremental fact loading

✅ Data quality testing

✅ Apache Airflow orchestration

✅ Dockerized Airflow environment

✅ OpenAI-powered review enrichment

✅ RAG-based review chatbot

✅ Natural language Text-to-SQL

✅ Streamlit AI applications

✅ Secure environment-based credentials

---

🔮 Future Enhancements

Potential improvements include:

- Real-time streaming using Kafka
- AWS Glue integration
- AWS Lambda-based ingestion
- CI/CD using GitHub Actions
- Data observability
- Great Expectations integration
- Snowflake Dynamic Tables
- More advanced AI agents
- Role-based Streamlit authentication
- Automated data quality monitoring
- Power BI / Tableau dashboards
- Production deployment on AWS

---

🎯 Project Outcome

This project demonstrates how raw food delivery data can be transformed into a scalable analytical platform:

Raw Data
   ↓
Amazon S3
   ↓
Snowflake Bronze
   ↓
dbt Silver
   ↓
dbt Gold
   ↓
Business Analytics
   ↓
AI Enrichment
   ↓
RAG + Text-to-SQL
   ↓
Interactive Applications

The combination of traditional data engineering and Generative AI makes the platform capable of both structured analytics and natural-language exploration of data.

---

👨‍💻 Skills Demonstrated

Python
SQL
Pandas
AWS S3
AWS IAM
Snowflake
dbt
Apache Airflow
Docker
OpenAI API
RAG
Embeddings
Text-to-SQL
Streamlit
Git/GitHub
Data Modeling
ETL / ELT
Data Quality
Cloud Data Engineering

---

📄 License

This project is intended for educational and portfolio purposes.

---

⭐ Acknowledgements

This project was developed as a hands-on implementation of an end-to-end modern data engineering and AI analytics architecture.

If you find this project useful, consider giving the repository a ⭐.
