import asyncio, json, os, queue, threading, time
import streamlit as st
from agent_core import run_agent

st.set_page_config(page_title="Deployer", layout="wide")
ss = st.session_state
ss.setdefault("events", [])
ss.setdefault("running", False)
ss.setdefault("pending", None)
ss.setdefault("q", queue.Queue())
ss.setdefault("answers", queue.Queue())

def read_jsonl(path):
    rows = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows

def start(msg):
    q, answers = ss.q, ss.answers
    ss.events = [{"type": "user", "text": msg}]
    ss.pending = None
    ss.running = True

    def emit(e):
        q.put(e)

    def ask(name, args):
        q.put({"type": "approval", "name": name, "args": args})
        return answers.get()

    def worker():
        try:
            asyncio.run(run_agent(msg, emit, ask))
        except BaseException as ex:
            q.put({"type": "error", "text": str(ex)[:500]})
        q.put({"type": "done"})

    threading.Thread(target=worker, daemon=True).start()

def answer(ok):
    p = ss.pending
    ss.events.append({"type": "decision", "ok": ok, "name": p["name"]})
    ss.pending = None
    ss.answers.put(ok)

prompt = st.chat_input("Ask the agent to deploy, fix or roll back...", disabled=ss.running)
if prompt:
    start(prompt.strip())

while True:
    try:
        e = ss.q.get_nowait()
    except queue.Empty:
        break
    if e["type"] == "approval":
        ss.pending = e
    elif e["type"] == "done":
        ss.running = False
    else:
        ss.events.append(e)

audit_rows = read_jsonl("audit.jsonl")
deploys = []
if os.path.exists("deployments.json"):
    try:
        deploys = json.load(open("deployments.json", encoding="utf-8"))
    except Exception:
        pass

st.title("Deployer")
st.caption("AI DevOps agent: Gemini + MCP + Docker")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Deployments", len(deploys))
c2.metric("Tool calls", sum(1 for r in audit_rows if r["event"] == "tool_call"))
c3.metric("Denied actions", sum(1 for r in audit_rows if r["event"] == "denied"))
c4.metric("Agent", "Working" if ss.running else "Idle")

tab1, tab2, tab3 = st.tabs(["Agent", "Audit log", "Deployments"])

with tab1:
    for e in ss.events:
        t = e["type"]
        if t == "user":
            with st.chat_message("user"):
                st.write(e["text"])
        elif t == "tool":
            with st.chat_message("assistant"):
                st.markdown(f"**{e['name']}**  `{json.dumps(e['args'], ensure_ascii=False)[:200]}`")
        elif t == "result":
            st.code(e["text"], language=None)
        elif t == "decision":
            if e["ok"]:
                st.success(f"You approved: {e['name']}")
            else:
                st.error(f"You rejected: {e['name']}")
        elif t == "summary":
            with st.chat_message("assistant"):
                st.success(e["text"])
        elif t == "notice":
            st.caption(e["text"])
        elif t == "error":
            st.error(e["text"])

    if ss.pending:
        p = ss.pending
        with st.container(border=True):
            st.warning(f"Approval needed: **{p['name']}**")
            st.code(json.dumps(p["args"], indent=2, ensure_ascii=False), language="json")
            b1, b2, _ = st.columns([1, 1, 4])
            b1.button("Approve", type="primary", on_click=answer, args=(True,))
            b2.button("Reject", on_click=answer, args=(False,))

with tab2:
    if audit_rows:
        st.dataframe(
            [{"time": r["time"], "event": r["event"], "tool": r.get("tool", ""),
              "args": json.dumps(r.get("args", ""), ensure_ascii=False)[:120]}
             for r in reversed(audit_rows)],
            width="stretch",
        )
    else:
        st.info("No audit entries yet.")

with tab3:
    if deploys:
        st.dataframe(list(reversed(deploys)), width="stretch")
    else:
        st.info("No deployments yet.")

if ss.running and not ss.pending:
    time.sleep(0.5)
    st.rerun()