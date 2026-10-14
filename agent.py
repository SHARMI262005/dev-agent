import asyncio, os, sys, time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options=types.HttpOptions(timeout=60000),
)
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
MAX_STEPS = 10

SYSTEM = """You are a DevOps agent. Use the tools to build, run, check and fix deployments.
Rules:
- Container names must start with 'agent-'.
- Apps listen on port 8000 inside the container. Use host_port 8001.
- After run_container, call health_check on http://localhost:8001/health.
- If health_check fails, call get_logs, explain the cause, then fix or stop the container.
- Never invent tool results. Give a short summary at the end."""

def generate(contents, config):
    for attempt in range(4):
        try:
            return client.models.generate_content(
                model=MODEL, contents=contents, config=config
            )
        except ServerError:
            print(f"  (model busy, retry {attempt + 1})")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("Model unavailable, try later")

async def main():
    params = StdioServerParameters(command=sys.executable, args=["deploy_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools

            declarations = [
                types.FunctionDeclaration(
                    name=t.name,
                    description=t.description,
                    parameters_json_schema=t.inputSchema,
                )
                for t in tools
            ]
            config = types.GenerateContentConfig(
                system_instruction=SYSTEM,
                tools=[types.Tool(function_declarations=declarations)],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            )

            user_msg = input("You: ")
            contents = [types.Content(role="user", parts=[types.Part(text=user_msg)])]

            for step in range(MAX_STEPS):
                resp = generate(contents, config)
                calls = resp.function_calls
                if not calls:
                    print("\nAGENT:", resp.text)
                    return
                contents.append(resp.candidates[0].content)
                parts = []
                for fc in calls:
                    args = dict(fc.args or {})
                    print(f"TOOL  {fc.name}({args})")
                    result = await session.call_tool(fc.name, args)
                    text = result.content[0].text if result.content else ""
                    print(f"      -> {text[:150]!r}")
                    parts.append(
                        types.Part.from_function_response(
                            name=fc.name, response={"result": text}
                        )
                    )
                contents.append(types.Content(role="user", parts=parts))
            print("Stopped: max steps reached")

asyncio.run(main())