# Cloud Resource Usage & Cost Optimization System

A full-stack DBMS project with AI integration.

**Stack:** MySQL 8, Python/Flask, Groq (Llama 3), scikit-learn, Bootstrap 5, Chart.js

---

## Setup

### 1. MySQL — Run SQL files in order

```bash
mysql -u root -p < sql/schema.sql
mysql -u root -p < sql/seed.sql
mysql -u root -p < sql/views.sql
mysql -u root -p < sql/triggers.sql
mysql -u root -p < sql/procedures.sql
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

Edit `config.py`:
- Set `DB_PASSWORD` to your MySQL root password
- Set `GROQ_API_KEY` — get a free key at [console.groq.com](https://console.groq.com)

```bash
python app.py
# Flask runs on http://localhost:5000
```

### 3. Frontend

Open `frontend/index.html` directly in a browser (no build step needed).
All pages use `http://localhost:5000/api` for data.

---

## Project Structure

```
cloud_cost_project/
├── backend/
│   ├── app.py          # 32 Flask API endpoints
│   ├── db.py           # MySQL connection helper
│   ├── ai.py           # Groq/Llama 3 AI features
│   ├── ml.py           # scikit-learn anomaly detection
│   ├── config.py       # DB + API credentials
│   └── requirements.txt
├── frontend/
│   ├── index.html      # Dashboard + charts
│   ├── users.html      # User CRUD
│   ├── resources.html  # Resource CRUD + filters
│   ├── usage.html      # Usage logs + trigger demo + anomaly detection
│   ├── billing.html    # Billing + triggers + stored procedure
│   ├── suggestions.html# Suggestions + AI analysis
│   ├── reports.html    # Views + custom SQL + NL-to-SQL
│   ├── transactions.html # 5 transaction demos with before/after
│   ├── css/style.css
│   └── js/
│       ├── common.js   # API helpers, toasts, utilities
│       └── chatbot.js  # Floating AI chat widget
└── sql/
    ├── schema.sql      # 6 tables
    ├── seed.sql        # Initial data
    ├── views.sql       # High_Cost, Low_CPU
    ├── triggers.sql    # 3 triggers
    └── procedures.sql  # show_billing()
```

---

## Features

| Chapter | Feature | Demo Location |
|---------|---------|---------------|
| Ch 2 | CRUD on all 6 tables | Users, Resources, Usage, Billing pages |
| Ch 3 | Views | Reports → High Cost / Low CPU |
| Ch 3 | Triggers | Usage (low_cpu), Billing (calc_total_cost, check_usage_hours) |
| Ch 3 | Stored Procedure | Billing → Run show_billing() |
| Ch 5 | Transactions | Transactions page (5 demos) |
| AI | NL-to-SQL | Reports → Ask in English |
| AI | Resource Recommendations | Suggestions → Generate |
| AI | Anomaly Detection (ML) | Usage Logs → Detect Anomalies |
| AI | Chatbot | Floating bubble on all pages |

---

## API Endpoints (32 total)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/dashboard/stats | Dashboard stats + chart data |
| GET/POST/PUT/DELETE | /api/users[/id] | User CRUD |
| GET/POST/PUT/DELETE | /api/resources[/id] | Resource CRUD |
| GET/POST/DELETE | /api/usage-logs[/id] | Usage log CRUD |
| GET/POST/DELETE | /api/billing[/id] | Billing CRUD |
| GET | /api/suggestions | List suggestions |
| GET | /api/views/high-cost | High_Cost view |
| GET | /api/views/low-cpu | Low_CPU view |
| POST | /api/procedures/show-billing | Call show_billing() |
| POST | /api/custom-sql | Execute custom SELECT |
| POST | /api/transactions/1-5 | Transaction demos |
| POST | /api/ai/nl-to-sql | English → SQL → result |
| POST | /api/ai/suggest/:id | AI recommendation for resource |
| POST | /api/ai/suggest-all | Bulk AI recommendations |
| POST | /api/ml/detect-anomalies | IsolationForest anomaly detection |
| POST/GET/DELETE | /api/ai/chat[/history] | Chatbot |
