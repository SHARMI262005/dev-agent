import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=30000),
)

print("Sending request...")
r = client.models.generate_content(
    model="gemini-3.8-flash",
    contents="Say hi in Tamil in one line",
)
print(r.text)