#!/usr/bin/env python3
"""
test_email_handler.py — failing tests for email-handler.

Run: python workspace/products/email-handler/test_email_handler.py
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "handler.py"

results: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, cond, detail))


def run_handler(payload: dict) -> dict:
    r = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if r.returncode != 0:
        return {"error": f"exit={r.returncode}", "stderr": r.stderr[:200]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"error": "invalid_json", "stdout": r.stdout[:200]}


# --- test 1: approval ---
out = run_handler({"text": "I approve this. Let's proceed."})
check("approval: bucket", isinstance(out, dict) and out.get("bucket") == "approval", str(out)[:100])
check("approval: action", out.get("action") == "proceed", str(out))
check("approval: confidence >= 0.7", out.get("confidence", 0) >= 0.7, str(out))

# --- test 2: rejection ---
out = run_handler({"text": "I reject this proposal. Not interested."})
check("rejection: bucket", out.get("bucket") == "rejection", str(out))
check("rejection: action", out.get("action") == "stop", str(out))

# --- test 3: question ---
out = run_handler({"text": "What is the timeline for this?"})
check("question: bucket", out.get("bucket") == "question", str(out))
check("question: action", out.get("action") == "respond", str(out))

# --- test 4: escalation ---
out = run_handler({"text": "This needs to be escalated to my manager ASAP."})
check("escalation: bucket", out.get("bucket") == "escalation", str(out))
check("escalation: action", out.get("action") == "escalate", str(out))

# --- test 5: noise ---
out = run_handler({"text": "Out of office until Monday."})
check("noise: bucket", out.get("bucket") == "noise", str(out))
check("noise: action", out.get("action") == "ignore", str(out))

# --- test 6: escalation priority over approval ---
out = run_handler({"text": "I approve but this needs to be escalated to legal."})
check("priority: escalation wins", out.get("bucket") == "escalation", str(out))

# --- test 7: rejection priority over approval ---
out = run_handler({"text": "I agree with the idea but I must reject this."})
check("priority: rejection wins", out.get("bucket") == "rejection", str(out))

# --- test 8: invalid input (missing text) ---
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input=json.dumps({"foo": "bar"}),
    capture_output=True, text=True, timeout=10,
)
check("invalid: exit 1", r.returncode == 1, f"rc={r.returncode}")

# --- test 9: invalid input (non-string text) ---
r = subprocess.run(
    [sys.executable, str(SCRIPT)],
    input=json.dumps({"text": 123}),
    capture_output=True, text=True, timeout=10,
)
check("wrongtype: exit 1", r.returncode == 1, f"rc={r.returncode}")

# --- test 10: no secrets in output ---
out = run_handler({"text": "I approve. My password is secret123."})
if isinstance(out, dict):
    check("no secrets: password not in output", "secret123" not in json.dumps(out), str(out))

# --- test 11: deterministic ---
out1 = run_handler({"text": "I approve this."})
out2 = run_handler({"text": "I approve this."})
check("deterministic: same output", out1 == out2, f"{out1} vs {out2}")

# --- test 12: fallback (no keyword match) ---
out = run_handler({"text": "Hello, I have a thought about the weather."})
check("fallback: bucket is noise", out.get("bucket") == "noise", str(out))
check("fallback: confidence is 0.3", out.get("confidence") == 0.3, str(out))

# --- report ---
passed = sum(1 for _, ok, _ in results if ok)
failed = [(n, d) for n, ok, d in results if not ok]
print(f"\n{passed}/{len(results)} assertions passed")
if failed:
    print("\nFAILED:")
    for n, d in failed:
        print(f"  {n}  ({d})")
    sys.exit(1)
print("ALL TESTS GREEN")
