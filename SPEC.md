# SPEC — Email Reply Handler

## What it does

Takes a plain-text email reply and classifies it into exactly one bucket:

| bucket | meaning |
|---|---|
| `approval` | Sender approves or agrees to the request |
| `rejection` | Sender rejects or declines the request |
| `question` | Sender asks a question that needs an answer |
| `escalation` | Sender escalates to a higher authority |
| `noise` | Not actionable (spam, auto-reply, out of office) |

Outputs structured JSON ready for workflow automation.

## What it does NOT do

- Does not connect to any email service
- Does not use an LLM
- Does not store email data
- Does not send replies

## Input

```json
{
  "text": "Hi, I've reviewed the proposal and I'm happy to approve it. Let's proceed."
}
```

## Output

```json
{
  "bucket": "approval",
  "confidence": 0.9,
  "action": "proceed"
}
```

## Exit codes

- `0` — success, email classified
- `1` — invalid input (missing `text` field, non-string)
- `2` — no classification possible

## Rules (deterministic, no ML)

### Classification keywords

| bucket | keywords |
|---|---|
| `approval` | approve, approved, agree, agreed, yes, proceed, go ahead, confirmed, confirmed, looks good, accepted |
| `rejection` | reject, rejected, decline, declined, no, cannot, can't, won't, not interested, pass |
| `question` | what, why, how, when, where, who, ?, question, clarify, explain |
| `escalation` | escalate, escalated, manager, director, vp, legal, compliance, urgent, asap |
| `noise` | out of office, auto-reply, automatic reply, unsubscribe, spam, promo |

### Priority order
1. `escalation` (highest priority — always flag urgent issues)
2. `rejection`
3. `approval`
4. `question`
5. `noise` (lowest priority — only if no other match)

### Confidence scoring
- Exact keyword match: 0.9
- Partial match (keyword is substring): 0.7
- Fallback (no keyword matched): 0.3

### Action mapping
- `approval` → `proceed`
- `rejection` → `stop`
- `question` → `respond`
- `escalation` → `escalate`
- `noise` → `ignore`

## Constraints

- No external API calls
- No file I/O beyond reading stdin and writing stdout
- No secrets in output
- Deterministic: same input → same output
