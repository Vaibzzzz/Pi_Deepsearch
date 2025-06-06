from langchain_xai import ChatXAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import FileChatMessageHistory
from sqlalchemy import create_engine

# === Step 1: Load Grok API Key ==
with open("XAI_API_KEY.txt", "r") as file:
    api_key = file.read().strip()

# === Step 2: Initialize Grok LLM ===
llm = ChatXAI(
    model="grok-3",
    api_key=api_key,
    temperature=0.3
)

# === Step 3: Setup MySQL Connection ===
db_user = "root"
db_password = "vaibhav1"
db_host = "localhost"
db_name = "pi"

engine = create_engine(f"mysql+mysqlconnector://{db_user}:{db_password}@{db_host}/{db_name}")
db = SQLDatabase(engine)

# === Step 4: Setup Persistent Memory (JSON-based) ===
chat_history = FileChatMessageHistory("memory.json")
memory = ConversationBufferMemory(
    memory_key="chat_history",
    chat_memory=chat_history,
    return_messages=True
)

# === Step 5: Custom Prompt Prefix ===
custom_prefix = """
You are a SQL expert AI. You answer questions about a SQL database.
If user query is not matching the database format, use inbuilt knowledge to find best query.

Important Guidelines:
- Translate natural language into SQL queries.
- Use correct SQL syntax.
- Return only what's needed for the answer.
"""

# === Step 6: Initialize Agent with SQL Toolkit and Prompt ===
toolkit = SQLDatabaseToolkit(db=db, llm=llm)
agent_executor = initialize_agent(
    tools=toolkit.get_tools(),
    llm=llm,
    memory=memory,
    agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    agent_kwargs={"prefix": custom_prefix}
)

# === Step 7: Run interactive loop ===
print("Ask any question about the transactions table. Type 'exit' to quit.\n")

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("👋 Exiting. Conversation saved to memory.json.")
        break

    try:
        response = agent_executor.invoke({"input": user_input})
        print("\nGrok:", response["output"])
    except Exception as e:
        print("❌ Error:", e)
