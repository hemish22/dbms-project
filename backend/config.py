# Database and API configuration
# Copy .env.example to .env and fill in your values

import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")       # set in .env
DB_NAME     = os.getenv("DB_NAME", "Cloud_Cost_Optimization")

GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")   # get from console.groq.com
GROQ_MODEL_FAST = os.getenv("GROQ_MODEL_FAST", "llama-3.1-8b-instant")
GROQ_MODEL_CHAT = os.getenv("GROQ_MODEL_CHAT", "llama-3.3-70b-versatile")
