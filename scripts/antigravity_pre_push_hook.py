import json
import os
import subprocess
import sys

# Ensure UTF-8 I/O
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            print(json.dumps({"decision": "allow"}))
            return

        payload = json.loads(raw_input)
        tool_call = payload.get("toolCall", {})
        tool_name = tool_call.get("name", "")
        args = tool_call.get("args", {})
        command_line = args.get("CommandLine", "")

        # Check if this tool invocation is a git push
        if tool_name == "run_command" and "git push" in command_line.lower():
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            test_script = os.path.join(root_dir, "scripts", "run_local_tests.py")
            python_bin = sys.executable

            venv_win = os.path.join(root_dir, ".venv", "Scripts", "python.exe")
            if os.path.exists(venv_win):
                python_bin = venv_win

            # Run test pipeline
            res = subprocess.run([python_bin, test_script], cwd=root_dir)

            if res.returncode != 0:
                output = {
                    "decision": "deny",
                    "reason": "Antigravity CI Gate: Local test suite failed! You must fix failing tests before pushing."
                }
            else:
                output = {
                    "decision": "allow",
                    "reason": "Antigravity CI Gate: All local tests passed! Allowing git push."
                }
            print(json.dumps(output))
            return

        # For any other command, allow normally
        print(json.dumps({"decision": "allow"}))
    except Exception as e:
        # In case of any error in hook itself, output allow to prevent blocking
        print(json.dumps({"decision": "allow", "reason": f"Hook exception handled: {e}"}))


if __name__ == "__main__":
    main()
