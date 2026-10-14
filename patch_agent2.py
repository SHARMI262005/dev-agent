s = open("agent.py", encoding="utf-8").read()

s = s.replace(
    "from google.genai.errors import ServerError",
    "from google.genai.errors import ServerError, ClientError",
)

NEW = '''MODELS = [MODEL, "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-2.5-flash-lite"]

def generate(contents, config):
    for model in dict.fromkeys(MODELS):
        for attempt in range(2):
            try:
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except ServerError:
                print(f"  ({model} busy, retry {attempt + 1})")
                time.sleep(4)
            except ClientError as e:
                print(f"  ({model} error {e.code}, trying next model)")
                break
    raise RuntimeError("All models unavailable, try again in a few minutes")'''

start = s.index("def generate(")
marker = 'raise RuntimeError("Model unavailable, try later")'
end = s.index(marker) + len(marker)
s = s[:start] + NEW + s[end:]

open("agent.py", "w", encoding="utf-8").write(s)
print("agent.py patched")