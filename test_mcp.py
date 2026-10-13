import asyncio, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(command=sys.executable, args=["deploy_server.py"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            r = await session.call_tool("build_image", {"path": "sample-app", "tag": "sample-app:v1"})
            print("BUILD:", r.content[0].text[-300:])

            r = await session.call_tool("run_container", {"image": "sample-app:v1", "host_port": 8001, "name": "agent-sample"})
            print("RUN:", r.content[0].text)

            await asyncio.sleep(3)
            r = await session.call_tool("health_check", {"url": "http://localhost:8001/health"})
            print("HEALTH:", r.content[0].text)

            r = await session.call_tool("get_logs", {"name": "agent-sample"})
            print("LOGS:", r.content[0].text)

            r = await session.call_tool("stop_container", {"name": "agent-sample"})
            print("STOP:", r.content[0].text)

asyncio.run(main())