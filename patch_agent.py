s = open("agent.py", encoding="utf-8").read()

TEXT = '''You are a DevOps agent. Use the tools to build, run, check and fix deployments.
Rules:
- Container names must start with 'agent-'.
- Apps listen on port 8000 inside the container. Use host_port 8001.
- After run_container, call health_check on http://localhost:8001/health.
- If health_check fails: call get_logs, explain the root cause, read the relevant files with read_file, fix them with write_file, stop the old container, rebuild with a NEW image tag, run again and re-check.
- Make at most 2 fix attempts. If still failing, stop the container and report clearly.
- Never claim success unless health_check returned 200 on /health.
- Reply in English, short summary at the end.'''

start = s.index('SYSTEM = """')
end = s.index('"""', start + 12) + 3
s = s[:start] + 'SYSTEM = """' + TEXT + '"""' + s[end:]
s = s.replace("MAX_STEPS = 10", "MAX_STEPS = 20")

open("agent.py", "w", encoding="utf-8").write(s)
print("agent.py patched")