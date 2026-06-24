from openai import OpenAI

client = OpenAI(
  base_url = "env.OPENAI_BASE_URL",
  api_key = "env.OPENAI_API_KEY"
)

completion = client.chat.completions.create(
  model="env.OPENAI_MODEL",
  messages=[{"role":"user","content":""}],
  temperature=1,
  top_p=1,
  max_tokens=4096,
  stream=False
)

reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
if reasoning:
  print(reasoning)
print(completion.choices[0].message.content)