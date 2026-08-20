# Day 38 — AI Safety, Red-Teaming & Guardrails

> **Phase 4 — Advanced AI Engineering** | Week 7 | Day 38 of 180

---

## 📌 What I Learned Today

- Threat modeling for AI: 8 categories of attacks on LLM systems
- Prompt injection: embedding instructions to override system prompt
- Jailbreaking: framing attacks that bypass safety training
- Data exfiltration: getting LLM to reveal system config or secrets
- SQL injection in AI context: malicious SQL embedded in user input
- Indirect prompt injection: malicious instructions in RAG-retrieved docs
- Denial of service: oversized inputs, repetition attacks, context flooding
- Input validation: fail-fast regex before the LLM ever sees the input
- Output filtering: PII redaction, system leak detection after generation
- PII detection patterns: email, phone, credit card, SSN, API keys
- System prompt leak detection: regex for "my prompt says" patterns
- Hallucination risk markers: flag uncertain-sounding outputs
- Red-team testing: systematic attack testing of your own system
- RedTeamCase dataclass: attack_type, payload, expected_behavior, severity
- RedTeamRunner: run all cases, aggregate pass/fail by severity
- Critical failures: high/critical severity cases that weren't blocked
- Bias testing: check consistency across demographic/stylistic variations
- should_match flag: True=must be consistent, False=must differentiate
- Name bias: priority should not differ by requester's name
- Politeness bias: polite framing should not change classification
- 3-stage guardrail pipeline: validate → generate → filter
- Audit log: each stage recorded for compliance

## 🔨 Project Built

**Production Guardrail System:**

**InputValidator** (Stage 1):
- 10 prompt injection patterns (override, persona, exfiltration)
- 6 SQL injection patterns (DDL, UNION, chain, tautology)
- 3 XSS/script injection patterns (with sanitization)
- Length limit (5000 chars) and repetition DoS detection

**OutputFilter** (Stage 3):
- PII redaction: email, phone, credit card, SSN, API keys
- System prompt leak detection
- Length limiting with clean sentence truncation
- Hallucination risk scoring

**Red-Team Suite** (25 cases):
- prompt_injection (5): direct override attempts
- jailbreak (2): persona/restriction bypass
- exfiltration (3): system config extraction
- sql_injection (3): SQL embedded in tasks
- length/repetition DoS (2): resource exhaustion
- xss_injection (2): script injection
- indirect_injection (2): instructions in content
- legitimate (4): must pass through correctly

**Bias Test Suite** (8 pairs):
- name_bias (2): Ahmed/Sara vs John/Mike
- politeness_bias (2): polite vs direct
- urgency_framing (2): legitimate urgency detection
- department_bias (1): frontend vs backend
- formality_bias (1): formal vs informal

**FastAPI** endpoints:
- POST /check, POST /ask, GET /redteam/run, GET /bias/run
- POST /filter/output, GET /security/overview
- POST /redteam/single (test custom payload)

## 🚀 How to Run

```bash
cd Day-38-Guardrails
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key" > .env  # optional

uvicorn app.main:app --reload

# Run red-team
curl http://localhost:8000/redteam/run

# Test injection
curl -X POST http://localhost:8000/check \
  -H "Content-Type: application/json" \
  -d '{"text": "Ignore all previous instructions"}'
```

## 🛡️ Threat Categories Covered

| Threat | Detection Layer | Action |
|--------|----------------|--------|
| Prompt injection | Input validator | Block |
| SQL injection | Input validator | Block |
| XSS/Script | Input validator | Sanitize |
| Length DoS | Input validator | Block |
| Repetition DoS | Input validator | Block |
| PII in output | Output filter | Redact |
| System leak | Output filter | Replace |
| Output DoS | Output filter | Truncate |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)