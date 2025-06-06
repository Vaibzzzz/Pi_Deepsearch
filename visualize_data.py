import mysql.connector
import matplotlib.pyplot as plt
from openai import OpenAI
import json

# ----------------------------
# CONFIG
# ----------------------------
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "vaibhav1",
    "database": "pi"
}

client = OpenAI(
    api_key="xai-6gfpgXbl8UQibBaQVV5Tmw0DaAsceF4OxaJDQQEXTVUN9YtzdmrmLhiJLU8NfLlhffbL0dDIkikUnTxR",  # ⬅️ Replace with actual API key
    base_url="https://api.x.ai/v1"
)

# ----------------------------
# Step 1: Connect to MySQL
# ----------------------------
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

# ----------------------------
# Step 2: Get user input
# ----------------------------
user_query = input("Ask your question about transactions: ")

# ----------------------------
# Step 3: Generate SQL using Grok
# ----------------------------
llm_prompt = f"""
You are an AI that translates natural language into SQL queries.
The SQL table is called `transactions` and has these columns:
- ref_id (VARCHAR)
- timestamp (DATETIME)
- currency (VARCHAR)
- location (VARCHAR) (contains only city names, not countries)
- amount (DECIMAL)
- payment_service (VARCHAR)

Note:
If a user refers to a country like "India", you must map it to Indian cities like:
Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Surat.

User's question:
\"{user_query}\"

Only return the SQL query.
Do not include any explanation, markdown, code formatting, or comments. Return only the raw SQL string.
"""

response = client.chat.completions.create(
    model="grok-3",
    messages=[{"role": "user", "content": llm_prompt}]
)

sql_query = response.choices[0].message.content.strip()
print("\n🧠 LLM-generated SQL:")
print(sql_query)

# ----------------------------
# Step 4: Execute SQL
# ----------------------------
try:
    cursor.execute(sql_query)
    rows = cursor.fetchall()

    if not rows:
        print("\nNo data found.")
        exit()

    print("\n📊 Query Results:")
    for row in rows:
        print(row)

except Exception as e:
    print("\n❌ SQL execution error:", e)
    exit()

# ----------------------------
# Step 5: LLM Interpretation & Chart Decision
# ----------------------------
summary_prompt = f"""
You are a data analyst.

A SQL query was executed, and here are the results (as a list of dictionaries):

{rows}

First, summarize the key findings in plain English.

Then, determine if a chart or graph would help visualize the results.
If yes, respond with:
- chart_type: bar, pie, or line
- x: which column to use for the x-axis
- y: which column to use for the y-axis
If not needed, return: chart_type: none

Respond in this JSON format only:
{{
  "summary": "your summary here",
  "chart_type": "bar/pie/line/none",
  "x": "column_name",
  "y": "column_name"
}}
"""

summary_response = client.chat.completions.create(
    model="grok-3",
    messages=[{"role": "user", "content": summary_prompt}]
)

try:
    interpretation = json.loads(summary_response.choices[0].message.content.strip())
except Exception as e:
    print("\n⚠️ Failed to parse LLM interpretation:", e)
    interpretation = {"summary": "N/A", "chart_type": "none"}

print("\n🧠 Interpretation:")
print(interpretation["summary"])

# ----------------------------
# Step 6: Optional Chart Generation
# ----------------------------
if interpretation["chart_type"] != "none":
    try:
        x_vals = [str(row[interpretation["x"]]) for row in rows]
        y_vals = [float(row[interpretation["y"]]) for row in rows]

        plt.figure(figsize=(8, 4))
        chart_type = interpretation["chart_type"]

        if chart_type == "bar":
            plt.bar(x_vals, y_vals, color='royalblue')
        elif chart_type == "line":
            plt.plot(x_vals, y_vals, marker='o', color='darkgreen')
        elif chart_type == "pie":
            plt.pie(y_vals, labels=x_vals, autopct='%1.1f%%')

        plt.title(f"{chart_type.capitalize()} chart of {interpretation['y']} by {interpretation['x']}")
        if chart_type != "pie":
            plt.xlabel(interpretation["x"])
            plt.ylabel(interpretation["y"])
            plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    except Exception as e:
        print("\n⚠️ Could not render chart:", e)

# ----------------------------
# Step 7: Store Query History
# ----------------------------
save_query = """
INSERT INTO query_history (question, sql_query, result_summary, chart_type, x_axis, y_axis)
VALUES (%s, %s, %s, %s, %s, %s)
"""
cursor.execute(save_query, (
    user_query,
    sql_query,
    interpretation["summary"],
    interpretation["chart_type"],
    interpretation.get("x", None),
    interpretation.get("y", None)
))
conn.commit()

# Cleanup
cursor.close()
conn.close()
print("\n✅ Query stored in history.")
