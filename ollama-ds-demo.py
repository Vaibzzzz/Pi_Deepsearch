import mysql.connector
import requests
import matplotlib.pyplot as plt

# 🔌 Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="vaibhav1",
    database="pi"
)
cursor = conn.cursor(dictionary=True)

# 🧠 User question
user_query = input("Ask your question about transactions: ")

# 🧾 Prompt sent to Ollama
sql_prompt = f"""
You are an AI that translates natural language into SQL queries.
The SQL table is called `transactions` and has the following columns:
- ref_id (VARCHAR)
- timestamp (DATETIME)
- currency (VARCHAR)
- location (VARCHAR) (contains only city names, not countries)
- amount (DECIMAL)
- payment_service (VARCHAR)

Note:
If a user refers to a country like "India", assume cities such as:
Delhi, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune, Ahmedabad, Jaipur, Surat.

User's question:
\"{user_query}\"

Only return the SQL query.
Do not include any explanation, markdown, code formatting, or comments.
Return only the raw SQL string.
"""

# ⚙️ Function to query Ollama locally
def query_ollama(prompt):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "deepseek-r1:1.5b",
            "prompt": prompt,
            "stream": False
        }
    )

    try:
        data = response.json()
        print("\n🔍 Raw Ollama Response:\n", data)
        if "response" in data:
            return data["response"].strip()
        elif "message" in data:
            return data["message"].strip()
        else:
            raise ValueError("No 'response' field in Ollama output.")
    except Exception as e:
        print("\n❌ Failed to parse Ollama response:", e)
        print("📦 Full JSON response:", response.text)
        return ""

# 🧠 Run LLM
sql_query = query_ollama(sql_prompt)
print("\n🧠 LLM-generated SQL:\n", sql_query)

# 🧮 Run SQL
try:
    cursor.execute(sql_query)
    results = cursor.fetchall()

    print("\n📊 Query Results:")
    for row in results:
        print(row)

    # 💾 Store query in history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS query_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question TEXT,
            sql_query TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT INTO query_history (question, sql_query) VALUES (%s, %s)", (user_query, sql_query))
    conn.commit()

    # 📈 Visualize if query is chartable
    if results and any(col in sql_query.lower() for col in ['group by', 'sum', 'count', 'amount', 'payment_service', 'location', 'currency']):
        first_row = results[0]
        if len(first_row) >= 2:
            x_key, y_key = list(first_row.keys())[:2]
            x = [row[x_key] for row in results]
            y = [row[y_key] for row in results]

            plt.bar(x, y, color='skyblue')
            plt.xlabel(x_key)
            plt.ylabel(y_key)
            plt.title(f"{y_key} by {x_key}")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.show()

except Exception as e:
    print("\n❌ SQL execution error:", e)

# 🔒 Cleanup
cursor.close()
conn.close()
