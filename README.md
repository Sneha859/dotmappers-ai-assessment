# DotMappers AI Support Ticket Intelligence

An AI-powered support-ticket analytics system that converts natural-language questions into safe SQL queries and detects data-driven anomalies in support-ticket data.

The system uses a local LLM through Ollama for natural-language-to-SQL generation, validates the generated SQL before execution, queries the dataset using DuckDB, and provides deterministic anomaly detection.

## Features

* Natural-language querying over support-ticket data
* Local LLM-based SQL generation using Ollama and Qwen3 4B
* SQL parsing and safety validation using SQLGlot
* In-memory DuckDB analytics
* REST API using FastAPI
* Interactive UI using Streamlit
* IQR-based resolution-time anomaly detection
* Weekly resolution-time anomaly detection
* Detection of unresolved High/Critical tickets older than 24 hours
* Automated tests using Pytest
* No paid APIs

## Architecture

```text
                    ┌──────────────────────┐
                    │    Streamlit UI      │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │      FastAPI         │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
    ┌────────────────────┐            ┌────────────────────┐
    │   Ollama / Qwen3   │            │ Anomaly Detector   │
    │      4B Local      │            │   Deterministic   │
    └─────────┬──────────┘            └────────────────────┘
              │
              ▼
    ┌────────────────────┐
    │   SQL Validator    │
    │      SQLGlot       │
    └─────────┬──────────┘
              │
              ▼
    ┌────────────────────┐
    │       DuckDB       │
    │    tickets table   │
    └────────────────────┘
```

## Data

The application uses:

```text
data/support_tickets.csv
```

The dataset contains 500 support tickets with the following columns:

```text
ticket_id
created_at
category
priority
status
response_time_hrs
resolution_time_hrs
agent_id
customer_rating
issue_summary
```

## Natural-Language Querying

A user enters a question such as:

```text
How many tickets are currently open?
```

The processing flow is:

```text
Natural-language question
        ↓
Qwen3 4B via Ollama
        ↓
Generated DuckDB SQL
        ↓
SQLGlot validation
        ↓
DuckDB execution
        ↓
Verified result
        ↓
User-facing answer
```

The LLM is used for understanding the user's request and generating SQL. The final numerical result is calculated directly from the dataset by DuckDB rather than being invented by the LLM.

## Supported Example Queries

### Count open tickets

```text
How many tickets are currently open?
```

Result on the supplied dataset:

```text
111
```

### Agent with the most resolutions this month

```text
Which agent resolved the most tickets this month?
```

Result on the supplied dataset:

```text
AGT-01
15 resolved tickets
```

For historical relative dates, the application uses the maximum `created_at` value in the dataset as the reference timestamp rather than the real-world current date.

### Critical tickets not resolved within 12 hours

```text
Show me all Critical tickets not resolved within 12 hours.
```

This is interpreted as:

```text
Critical tickets that are either unresolved
OR
required more than 12 hours to resolve.
```

### Average Technical-category customer rating

```text
What is the average customer rating for Technical category tickets?
```

Result on the supplied dataset:

```text
3.74
```

### Highest-volume category

```text
Which category has the most tickets?
```

Result on the supplied dataset:

```text
General
189 tickets
```

## Anomaly Detection

Resolution-time anomalies use a deterministic IQR-based rule.

Only resolved tickets with a non-null `resolution_time_hrs` are considered.

The threshold is:

```text
Q1  = 25th percentile
Q3  = 75th percentile
IQR = Q3 - Q1

Upper Bound = Q3 + 1.5 × IQR
```

A resolved ticket is considered an unusually long resolution-time anomaly when:

```text
resolution_time_hrs > Upper Bound
```

For the supplied dataset:

```text
Q1          = 6.15 hours
Q3          = 22.95 hours
IQR         = 16.80 hours
Upper Bound = 48.15 hours
```

This produces:

```text
21 overall resolution-time anomalies
3 resolution-time anomalies in the latest seven-day period
```

The latest seven-day period is determined from the maximum `created_at` timestamp in the dataset.

## Stale High/Critical Tickets

The system also detects tickets that satisfy all of the following:

```text
status != Resolved
priority is High or Critical
ticket age > 24 hours
```

Ticket age is calculated relative to the dataset's reference timestamp:

```text
MAX(created_at)
```

The supplied dataset contains:

```text
80 stale High/Critical tickets
```

## REST API

The FastAPI backend provides:

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "healthy",
  "dataset_rows": 500,
  "llm_model": "qwen3:4b-instruct"
}
```

### Natural-language query

```http
POST /query
```

Example request:

```json
{
  "question": "How many tickets are currently open?"
}
```

The response contains:

* original question
* generated SQL
* explanation
* formatted answer
* structured query results

### Anomaly detection

```http
GET /anomalies
```

The response contains:

* overall resolution-time anomalies
* weekly resolution-time anomalies
* stale High/Critical tickets
* dataset reference time
* total unique anomaly tickets

### Interactive API documentation

When the backend is running:

```text
http://127.0.0.1:8000/docs
```

## Streamlit UI

When the application is running:

```text
http://127.0.0.1:8501
```

The UI provides:

* dataset and model status
* natural-language question input
* generated answer
* explanation
* generated SQL
* query result table
* anomaly summary
* anomaly detail tables

## Project Structure

```text
dotmappers_ai_assessment/
│
├── app/
│   ├── api/
│   │   ├── routes_anomaly.py
│   │   ├── routes_health.py
│   │   └── routes_query.py
│   │
│   ├── anomaly/
│   │   └── detector.py
│   │
│   ├── data/
│   │   └── loader.py
│   │
│   ├── llm/
│   │   ├── client.py
│   │   └── prompts.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── query/
│   │   ├── engine.py
│   │   └── validator.py
│   │
│   └── main.py
│
├── data/
│   └── support_tickets.csv
│
├── tests/
│   ├── conftest.py
│   ├── test_anomaly.py
│   ├── test_api.py
│   └── test_query.py
│
├── ui/
│   └── streamlit_app.py
│
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## Requirements

* Python 3.12+
* Ollama
* Qwen3 4B model
* Git

The application is designed to run with a local LLM so that no paid external API is required.

## Setup

### 1. Clone the project

```bash
git clone <repository-url>
cd dotmappers_ai_assessment
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and prepare Ollama

Install Ollama according to the Ollama documentation for the operating system.

Start the Ollama service:

```bash
ollama serve
```

In another terminal, pull the model:

```bash
ollama pull qwen3:4b-instruct
```

Verify that the model is available:

```bash
ollama list
```

The application expects the local Ollama API at:

```text
http://127.0.0.1:11434
```

## Running the Application

After the initial setup and with Ollama running, start the application with:

```bash
python run.py
```

This starts:

```text
FastAPI    → http://127.0.0.1:8000
Swagger    → http://127.0.0.1:8000/docs
Streamlit  → http://127.0.0.1:8501
```

Press:

```text
Ctrl+C
```

to stop the application.

## Testing

The project includes automated tests for:

* SQL validation
* query result formatting
* DuckDB query execution
* anomaly detection
* IQR calculations
* weekly anomaly filtering
* stale High/Critical ticket detection
* FastAPI health endpoint
* FastAPI query endpoint
* FastAPI anomaly endpoint

Run all tests with:

```bash
pytest -q
```

Expected result for the current test suite:

```text
14 passed
```

## SQL Safety

Generated SQL is validated before execution.

The validator requires:

* exactly one SQL statement
* read-only SELECT or WITH ... SELECT queries
* references only to the `tickets` table and defined CTEs
* no INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, TRUNCATE, COPY, ATTACH, DETACH, MERGE, GRANT, or REVOKE operations
* no undefined tables or helper views
* no invented database columns

This prevents the LLM from directly modifying the dataset.

## Design Notes and Limitations

### Historical reference time

The supplied dataset is historical. Relative expressions such as:

```text
this month
this week
older than 24 hours
```

are interpreted relative to:

```text
MAX(created_at)
```

rather than the actual current date.

### Resolved timestamp

The dataset does not contain an explicit `resolved_at` field.

When the resolved timestamp is required, it is derived as:

```text
created_at + resolution_time_hrs * INTERVAL '1 hour'
```

for tickets with a non-null resolution time.

### Anomaly definition

Resolution-time anomalies use the deterministic IQR threshold described above.

Natural-language anomaly queries and the dedicated anomaly detector use the same anomaly definition.

### Local LLM

The system depends on a local Ollama installation and the Qwen3 4B model. Model availability and inference performance depend on the local machine.

## Technology Stack

```text
Python
FastAPI
Streamlit
Ollama
Qwen3 4B
DuckDB
Pandas
SQLGlot
Pytest
```

## Assessment Scope

The implementation focuses on the requested support-ticket intelligence workflow:

```text
CSV ingestion
    ↓
Natural-language understanding
    ↓
Safe SQL generation
    ↓
Query execution
    ↓
Structured answers
    ↓
Anomaly detection
    ↓
REST API + UI
```
