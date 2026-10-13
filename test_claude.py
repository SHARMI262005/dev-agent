import os
from dotenv import load_dotenv
import anthropic

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=200,
    messages=[{"role": "user", "content": "Say hi in Tamil in one line"}],
)
print(response.content[0].text)