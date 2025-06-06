from openai import OpenAI
    
client = OpenAI(
  api_key="xai-6gfpgXbl8UQibBaQVV5Tmw0DaAsceF4OxaJDQQEXTVUN9YtzdmrmLhiJLU8NfLlhffbL0dDIkikUnTxR",
  base_url="https://api.x.ai/v1",
)

completion = client.chat.completions.create(
  model="grok-3",
  messages=[
    {"role": "user", "content": "What is the meaning of life?"}
  ]
)
print(completion.choices[0].message.content)