import os
from dotenv import load_dotenv
from openai import OpenAI
from cadence import config

load_dotenv()
client = OpenAI(base_url=config.NVIDIA_BASE_URL, api_key=os.environ["NVIDIA_API_KEY"])
resp = client.chat.completions.create(
    model=config.NEMOTRON_MODEL,
    messages=[
        {"role": "system", "content": "detailed thinking off"},
        {"role": "user", "content": 'Reply with exactly this JSON and nothing else: {"ok": true}'},
    ],
    temperature=config.LLM_TEMPERATURE,
)
print(resp.choices[0].message.content)
