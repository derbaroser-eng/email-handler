#!/usr/bin/env python3
"""
handler.py — deterministic email reply classifier.

Reads JSON from stdin, writes JSON to stdout.
No external calls, no file I/O, no secrets in output.
"""
import json
import sys

KEYWORDS = {
    "escalation": ["escalate", "escalated", "manager", "director", "vp", "legal", "compliance", "urgent", "asap"],
    "rejection": ["reject", "rejected", "decline", "declined", "no", "cannot", "can't", "won't", "not interested", "pass"],
    "approval": ["approve", "approved", "agree", "agreed", "yes", "proceed", "go ahead", "confirmed", "looks good", "accepted"],
    "question": ["what", "why", "how", "when", "where", "who", "?", "question", "clarify", "explain"],
    "noise": ["out of office", "auto-reply", "automatic reply", "unsubscribe", "spam", "promo"],
}

PRIORITY = ["escalation", "rejection", "approval", "question", "noise"]

ACTIONS = {
    "approval": "proceed",
    "rejection": "stop",
    "question": "respond",
    "escalation": "escalate",
    "noise": "ignore",
}


def classify(text):
    """Classify email text into a bucket."""
    text_lower = text.lower()
    for bucket in PRIORITY:
        for kw in KEYWORDS[bucket]:
            if kw in text_lower:
                confidence = 0.9 if kw == text_lower else 0.7
                return bucket, confidence
    return "noise", 0.3


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("error: invalid JSON", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("error: input must be a JSON object", file=sys.stderr)
        return 1

    if "text" not in data:
        print("error: missing 'text' field", file=sys.stderr)
        return 1

    if not isinstance(data["text"], str):
        print("error: 'text' must be a string", file=sys.stderr)
        return 1

    bucket, confidence = classify(data["text"])
    result = {
        "bucket": bucket,
        "confidence": confidence,
        "action": ACTIONS[bucket],
    }
    json.dump(result, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
