s = open("agent.py", encoding="utf-8").read()
old = 'user_msg = input("You: ")'
assert old in s
new = '''user_msg = input("You: ").strip()
            if not user_msg:
                print("Empty request, exiting.")
                return'''
s = s.replace(old, new, 1)
open("agent.py", "w", encoding="utf-8").write(s)
print("patched")