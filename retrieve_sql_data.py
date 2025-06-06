import mysql.connector
from openai import OpenAI

# Step 1: Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="vaibhav1",
    database="pi"
)

cursor = conn.cursor(dictionary=True)

# Step 2: Initialize LLM client (Grok)
client = OpenAI(
    api_key="xai-6gfpgXbl8UQibBaQVV5Tmw0DaAsceF4OxaJDQQEXTVUN9YtzdmrmLhiJLU8NfLlhffbL0dDIkikUnTxR",
    base_url="https://api.x.ai/v1"
)

# Step 3: Initialize conversation memory
chat_history = [
    {
        "role": "system",
        "content": """
You are an AI that translates natural language into MySQL queries.
The SQL table is called `transactions` and has these columns:
- ref_id (VARCHAR)
- timestamp (DATETIME)
- currency (VARCHAR)
- location (VARCHAR) (contains only city names, not countries)
- amount (DECIMAL)
- payment_service (VARCHAR)

Note:
If a user refers to a country like "India", you must map it to known Indian cities such as:
Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Surat.

Only return the SQL query.
Do not include any explanation, markdown, code formatting, or comments. Return only the raw SQL string.
"""
    }
]

# Conversation loop
while True:
    user_query = input("\nAsk your question about transactions (or type 'exit' to quit): ")
    if user_query.lower() == "exit":
        break

    # Add user message to chat history
    chat_history.append({"role": "user", "content": user_query})

    # Get SQL query from LLM
    response = client.chat.completions.create(
        model="grok-3",
        messages=chat_history
    )

    sql_query = response.choices[0].message.content.strip()
    print("\n🧠 LLM-generated SQL:")
    print(sql_query)

    # Add assistant SQL to chat history
    chat_history.append({"role": "assistant", "content": sql_query})

    # Step 4: Run SQL and show results
    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        print("\n📊 Query Results:")
        if rows:
            for row in rows:
                print(row)
        else:
            print("No data found.")

        # Optional: Add results to memory as well
        chat_history.append({"role": "assistant", "content": str(rows)})

    except Exception as e:
        print("\n❌ SQL execution error:", e)
        chat_history.append({"role": "assistant", "content": f"SQL error: {e}"})

cursor.close()
conn.close()
