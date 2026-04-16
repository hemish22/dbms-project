"""
AI helpers — wraps Groq API calls.
All prompt templates live here.
"""
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL_FAST, GROQ_MODEL_CHAT

client = Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------------------------
# Schema context injected into every prompt
# ---------------------------------------------------------------------------
SCHEMA_CONTEXT = """
DATABASE: Cloud_Cost_Optimization (MySQL 8)

TABLES:
- User(user_id PK, name, email, organization, created_at)
- Cloud_Resource(resource_id PK, user_id FK→User, resource_type ENUM('VM','Storage','Database','Network'), instance_type, region, status ENUM('Running','Stopped','Idle'), created_at)
- Usage_Log(log_id PK, resource_id FK→Cloud_Resource, cpu_usage DECIMAL, memory_usage DECIMAL, storage_used DECIMAL, timestamp)
- Billing(bill_id PK, resource_id FK→Cloud_Resource, usage_hours DECIMAL, cost_per_hour DECIMAL, total_cost DECIMAL, billing_date DATE)
- Optimization_Suggestion(suggestion_id PK, resource_id FK→Cloud_Resource, suggestion_type ENUM('Stop','Resize','Schedule','Migrate'), reason TEXT, estimated_savings DECIMAL, created_at, ai_recommendation TEXT, ai_generated_at TIMESTAMP)
- Chat_History(chat_id PK, user_question TEXT, ai_response TEXT, created_at)

VIEWS:
- High_Cost — resources with total billing > 150, columns: resource_id, resource_type, instance_type, region, status, owner_name, total
- Low_CPU  — resources with avg CPU < 5%, columns: resource_id, resource_type, instance_type, region, status, owner_name, avg_cpu

CURRENCY: Indian Rupees (₹). All cost columns are in ₹.
"""

# Dangerous SQL keywords to block
BLOCKED_KEYWORDS = [
    "drop", "delete", "update", "insert", "alter",
    "truncate", "grant", "revoke", "create", "replace",
    "rename", "lock", "unlock", "call", "exec",
]


def natural_language_to_sql(question: str) -> dict:
    """
    Convert a natural-language question to a safe SELECT query.
    Returns {sql, explanation, error}.
    """
    prompt = f"""{SCHEMA_CONTEXT}

TASK: Convert the user's question into a single MySQL SELECT statement.
RULES:
- Only SELECT queries (no data modifications)
- Use table aliases: u=User, cr=Cloud_Resource, ul=Usage_Log, b=Billing, s=Optimization_Suggestion
- Return ONLY the SQL — no markdown, no backticks, no explanation
- End with a semicolon

USER QUESTION: {question}"""

    resp = client.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=400,
    )
    raw = resp.choices[0].message.content.strip()

    # Strip markdown fences if the model added them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lower().startswith("sql"):
            raw = raw[3:]
        raw = raw.strip()

    sql = raw.rstrip(";") + ";"

    # Safety check
    sql_lower = sql.lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in sql_lower.split():
            return {"error": f"Generated SQL contains blocked keyword '{kw}'. Only SELECT is allowed."}

    if not sql_lower.strip().startswith("select"):
        return {"error": "Generated query is not a SELECT statement. Refused for safety."}

    # Get a brief explanation
    exp_resp = client.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[{
            "role": "user",
            "content": f"In one sentence, explain what this SQL query does: {sql}"
        }],
        temperature=0.3,
        max_tokens=100,
    )
    explanation = exp_resp.choices[0].message.content.strip()

    return {"sql": sql, "explanation": explanation}


def generate_resource_recommendation(resource_data: dict) -> str:
    """
    Given a dict of resource info + recent usage + billing,
    return a 2-3 sentence AI recommendation.
    """
    prompt = f"""{SCHEMA_CONTEXT}

You are a cloud cost optimization expert. Analyze the following resource and give a concise 2-3 sentence recommendation.
Include: what's wrong, what to do, and estimated monthly savings in ₹.

RESOURCE DATA:
{resource_data}

Respond in plain text only. Be specific and actionable."""

    resp = client.chat.completions.create(
        model=GROQ_MODEL_FAST,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()


def chat(user_message: str, history: list) -> str:
    """
    Chatbot turn. history is a list of {role, content} dicts (last 5 turns).
    Returns the assistant's response string.
    """
    system = f"""You are CloudBot, an AI assistant for the Cloud Resource Usage & Cost Optimization System.
{SCHEMA_CONTEXT}

You can answer:
1. Questions about cloud data (costs, usage, resources) — reason from the schema context
2. DBMS concepts (triggers, views, stored procedures, transactions, normalization)
3. General cloud computing questions

Be concise, friendly, and use ₹ for costs. If asked about specific data you cannot see, explain you need a database query."""

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    resp = client.chat.completions.create(
        model=GROQ_MODEL_CHAT,
        messages=messages,
        temperature=0.6,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()
