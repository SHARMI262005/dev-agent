import os
import subprocess
import time
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("deploy-mcp")

ALLOWED_DIRS = [os.path.abspath("sample-app"), os.path.abspath("broken-app")]

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

def check_path(path):
    full = os.path.abspath(path)
    for d in ALLOWED_DIRS:
        if full == d or full.startswith(d + os.sep):
            return full
    raise ValueError("path not allowed: only sample-app and broken-app")

@mcp.tool()
def build_image(path: str, tag: str) -> str:
    """Build a Docker image from a folder that contains a Dockerfile."""
    check_path(path)
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
def health_check(url: str, retries: int = 5, delay: int = 2) -> str:
    """HTTP GET a URL, retrying while the app starts. Reports the final status."""
    last = ""
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                body = r.read().decode("utf-8", errors="replace")[:200]
                return f"{r.status} {body}"
        except Exception as e:
            last = str(e)
            time.sleep(delay)
    return f"FAIL after {retries} tries: {last}"

@mcp.tool()
def read_file(path: str) -> str:
    """Read a text file inside sample-app or broken-app."""
    full = check_path(path)
    with open(full, "r", encoding="utf-8") as f:
        return f.read()[:5000]

@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Overwrite a text file inside sample-app or broken-app."""
    full = check_path(path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} chars to {path}"

if __name__ == "__main__":
    mcp.run()