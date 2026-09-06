# AI-Powered Food Data Platform

> An end-to-end **Data Engineering + AI hobby project** exploring how structured and unstructured food-delivery data can be transformed into business-ready analytics and natural-language experiences.

## Overview

What if you could simply ask a food platform what you want instead of manually filtering, scrolling, and searching?

This project explores that idea by building a complete data platform that moves from **raw data → cloud storage → data warehouse → transformations → orchestration → AI**.

The platform works with:

- **10M+ orders**
- **~23M order items**
- **300K customer reviews**
- Restaurant, customer, food, and menu dimensions

The goal was not just to build an AI chatbot, but to understand the **data engineering foundation required to make AI useful and reliable**.

---

## Architecture

```text
                    ┌──────────────────────┐
                    │      Local Data      │
                    │ CSV + Generated Data │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │       AWS S3         │
                    │     Raw Data Lake    │
                    └──────────┬───────────┘
                               │
                         COPY INTO
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Snowflake       │
                    │       RAW Layer      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │        dbt           │
                    │  Staging / Silver    │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      Snowflake       │
                    │   Gold / Marts       │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴───────────┐
                    │                      │
                    ▼                      ▼
          ┌──────────────────┐   ┌──────────────────┐
          │     Analytics    │   │    AI Layer      │
          │ Revenue / SLA /  │   │ Reviews / RAG /  │
          │ Performance      │   │   Text-to-SQL    │
          └──────────────────┘   └────────┬─────────┘
                                          │
                                          ▼
                                  Natural Language
                                      Interface

                    ┌──────────────────────┐
                    │       Airflow        │
                    │    Orchestration     │
                    └──────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Programming | Python |
| Querying | SQL |
| Cloud Storage | Amazon S3 |
| Data Warehouse | Snowflake |
| Transformation | dbt |
| Orchestration | Apache Airflow |
| AI / LLM | Hugging Face ecosystem |
| Embeddings | `BAAI/bge-small-en-v1.5` |
| LLMs | Qwen / Llama instruction models |
| Retrieval | RAG |
| AI Analytics | Natural Language → SQL |
| Infrastructure | Docker |
| Version Control | Git / GitHub |

---

## Data Engineering Pipeline

### 1. Source Data

The project starts with local CSV datasets containing dimensions such as:

- Restaurants
- Users
- Food
- Menu

Large fact datasets are generated to simulate a realistic production workload:

- 10M+ orders
- ~23M order items
- 300K free-text reviews

---

### 2. Data Lake — Amazon S3

Raw datasets are uploaded to S3 using a table-oriented structure:

```text
raw/
├── restaurants/
├── users/
├── food/
├── menu/
├── orders/
├── order_items/
└── reviews/
```

S3 acts as the raw landing zone before warehouse ingestion.

---

### 3. Data Warehouse — Snowflake

Snowflake is organized into separate layers:

```text
ZOMATO
├── RAW
├── STAGING
├── MARTS
└── AI
```

Raw data is loaded from S3 into Snowflake using `COPY INTO` through a storage integration.

---

### 4. Transformation — dbt

dbt is used to transform raw warehouse data into clean and business-ready datasets.

The transformation flow follows:

```text
RAW
 ↓
STAGING
 ↓
CORE / DIMENSIONS + FACTS
 ↓
BUSINESS MARTS
```

The project includes concepts such as:

- Staging models
- Fact tables
- Dimension tables
- Incremental models
- MERGE-based loading
- Business marts
- SCD Type 2 snapshots

---

### 5. Orchestration — Airflow

The complete workflow is orchestrated using Apache Airflow running in Docker.

The daily pipeline follows:

```text
reload_raw
     ↓
dbt_build_core
     ↓
enrich_reviews
     ↓
dbt_build_ai
```

This connects the data engineering and AI layers into a repeatable workflow.

---

# AI Layer

The AI layer explores three different use cases.

## 1. AI Review Enrichment

Customer reviews contain valuable information that is difficult to analyze using traditional structured columns.

The pipeline enriches reviews with AI-generated metadata such as:

- Sentiment
- Topic / category

This makes unstructured customer feedback easier to analyze alongside structured business data.

---

## 2. RAG — Chat with Customer Reviews

The project uses Retrieval-Augmented Generation to allow natural-language interaction with review data.

High-level flow:

```text
Customer Question
       ↓
Embedding
       ↓
Vector Retrieval
       ↓
Relevant Reviews
       ↓
LLM
       ↓
Answer
```

This allows questions to be answered using relevant customer-review context rather than relying only on the model's internal knowledge.

---

## 3. Text-to-SQL

The project also explores asking analytical questions in natural language.

Example:

```text
"Which city has the highest revenue?"
```

The system translates the question into SQL:

```text
Natural Language
       ↓
LLM
       ↓
Generated SQL
       ↓
Validation
       ↓
Snowflake
       ↓
Result
```

The generated query is restricted to read-only analytical operations before being executed against the warehouse.

---

# Project Structure

```text
.
├── ai/
│   ├── enrich_reviews.py
│   ├── hf_worker.py
│   ├── rag_chat.py
│   └── text_to_sql.py
│
├── airflow/
│   └── dags/
│
├── data/
│   ├── restaurants.csv
│   ├── users.csv
│   ├── food.csv
│   └── menu.csv
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   └── snapshots/
│
├── snowflake/
│   ├── 01_setup.sql
│   ├── 02_*.sql
│   ├── 03_*.sql
│   ├── 04_*.sql
│   └── 05_copy_into.sql
│
├── aws/
│   ├── iam/
│   └── policies/
│
├── docker/
│
└── README.md
```

> Directory names may vary slightly depending on the current project version.

---

# Key Data Models

The Gold layer contains analytical models for areas such as:

### Daily City Revenue

Provides city-level business metrics including revenue, order volume, cancellation rate, and average order value.

### Restaurant Performance

Combines restaurant information with order activity and customer ratings to evaluate restaurant-level performance.

### Delivery SLA

Provides delivery-performance metrics for monitoring delivery times and late orders.

### SCD Type 2

A snapshot is used to preserve historical changes to dimensional data rather than overwriting previous values.

---

# Running the Project

## Prerequisites

You'll need:

- Python
- Docker
- AWS account
- Snowflake account
- dbt
- Airflow
- Git

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install project dependencies:

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file with the required credentials and configuration for:

```text
AWS
Snowflake
Hugging Face
```

**Do not commit credentials or secrets to GitHub.**

Add `.env` to `.gitignore`:

```text
.env
```

---

## Run dbt

From the dbt project directory:

```bash
dbt debug
dbt run
dbt test
```

---

## Run Airflow

Start the Airflow environment using Docker Compose:

```bash
docker compose up
```

Then trigger the project DAG from the Airflow UI.

---

## Run the AI Components

The AI scripts can be run independently depending on the use case:

```bash
python ai/enrich_reviews.py
python ai/rag_chat.py
python ai/text_to_sql.py
```

The exact commands may depend on your configured environment and project version.

---

# What I Learned

This project started as a simple idea around making food discovery easier, but the engineering challenges quickly became more interesting.

Some of the main areas I explored:

- Designing an end-to-end data pipeline
- Working with large synthetic datasets
- Separating raw, staging, and business-ready warehouse layers
- Building incremental dbt models
- Using MERGE-based loading
- Managing historical dimension changes with SCD Type 2
- Orchestrating data + AI workflows with Airflow
- Working with structured and unstructured data together
- Building RAG pipelines
- Converting natural-language questions into SQL
- Validating AI-generated SQL before execution

The biggest takeaway:

> **Good AI experiences depend on good data foundations.**

---

# Future Improvements

Some areas I plan to explore next:

- More robust data quality checks
- Better SQL validation and query planning
- Improved retrieval and ranking for RAG
- More analytical marts
- Real-time / streaming ingestion
- Monitoring and observability
- CI/CD for the data platform
- Better evaluation of AI-generated answers and SQL

---

# Disclaimer

This is a **personal hobby / learning project** created to explore data engineering, cloud data platforms, analytics engineering, and AI.

It is inspired by common food-delivery data and business scenarios and is **not affiliated with or endorsed by any food-delivery company**.

---

## Author

**Vishnu Nukala**

Data Engineering • Cloud • DevOps • AI

Building projects, experimenting with technologies, and documenting what I learn.

---

⭐ If you find the project interesting, feel free to explore the code and follow along with the **Data Engineering Demos** series.
