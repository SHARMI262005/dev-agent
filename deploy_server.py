import subprocess
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("deploy-mcp")

def run(cmd):
    p = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    out = (p.stdout or "") + (p.stderr or "")
    return out.strip()[-3000:]

def check_name(name):
    if not name.startswith("agent-"):
        raise ValueError("container name must start with 'agent-'")

@mcp.tool()
def build_image(path: str, tag: str) -> str:
    """Build a Docker image from a folder that contains a Dockerfile."""
    return run(["docker", "build", "-t", tag, path])

@mcp.tool()
def run_container(image: str, host_port: int, name: str) -> str:
    """Run a container in the background. App must listen on port 8000 inside."""
    check_name(name)
    return run(["docker", "run", "-d", "-p", f"{host_port}:8000", "--name", name, image])

@mcp.tool()
def get_logs(name: str) -> str:
    """Get the last 50 log lines of a container."""
    check_name(name)
    return run(["docker", "logs", "--tail", "50", name])

@mcp.tool()
def stop_container(name: str) -> str:
    """Stop and remove a container."""
    check_name(name)
    return run(["docker", "rm", "-f", name])

@mcp.tool()
def health_check(url: str) -> str:
    """HTTP GET a URL and report the status."""
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            body = r.read().decode("utf-8", errors="replace")[:200]
            return f"{r.status} {body}"
    except Exception as e:
        return f"FAIL: {e}"

if __name__ == "__main__":
    mcp.run()