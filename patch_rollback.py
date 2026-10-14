s = open("deploy_server.py", encoding="utf-8").read()

assert "import subprocess\n" in s
s = s.replace("import subprocess\n", "import json\nimport subprocess\n", 1)

old = 'return run(["docker", "run", "-d", "-p", f"{host_port}:8000", "--name", name, image])'
assert old in s
new = '''out = run(["docker", "run", "-d", "-p", f"{host_port}:8000", "--name", name, image])
    record_deploy(name, image, host_port)
    return out'''
s = s.replace(old, new, 1)

EXTRA = '''
HISTORY_FILE = "deployments.json"

def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def record_deploy(name, image, host_port):
    h = load_history()
    h.append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "name": name, "image": image, "host_port": host_port})
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(h[-50:], f, indent=2)

@mcp.tool()
def deployment_history(name: str) -> str:
    """Show the recent deployments (image, port, time) for a container name."""
    check_name(name)
    rows = [r for r in load_history() if r["name"] == name]
    return json.dumps(rows[-5:], indent=2) if rows else "no history"

@mcp.tool()
def rollback(name: str) -> str:
    """Roll back a container to the previous different image deployed under this name."""
    check_name(name)
    rows = [r for r in load_history() if r["name"] == name]
    if len(rows) < 2:
        return "no previous deployment to roll back to"
    current = rows[-1]
    previous = None
    for r in reversed(rows[:-1]):
        if r["image"] != current["image"]:
            previous = r
            break
    if not previous:
        return "no different previous image found"
    run(["docker", "rm", "-f", name])
    out = run(["docker", "run", "-d", "-p", f"{previous['host_port']}:8000", "--name", name, previous["image"]])
    record_deploy(name, previous["image"], previous["host_port"])
    return f"rolled back to {previous['image']}: {out}"

'''
marker = 'if __name__ == "__main__":'
assert marker in s
s = s.replace(marker, EXTRA + marker, 1)
open("deploy_server.py", "w", encoding="utf-8").write(s)

a = open("agent.py", encoding="utf-8").read()
old1 = 'NEEDS_APPROVAL = {"write_file", "stop_container"}'
assert old1 in a
a = a.replace(old1, 'NEEDS_APPROVAL = {"write_file", "stop_container", "rollback"}', 1)

old2 = "- Never claim success unless health_check returned 200 on /health."
assert old2 in a
new2 = """- If get_logs is empty, say so, and state which tool output (for example the run_container error) the root cause came from.
- After a human denies an action, do NOT try other edits to work around it. Stop and report.
- If the user asks to roll back: call deployment_history, then rollback, then health_check.
- Never claim success unless health_check returned 200 on /health."""
a = a.replace(old2, new2, 1)
open("agent.py", "w", encoding="utf-8").write(a)

print("patched deploy_server.py and agent.py")