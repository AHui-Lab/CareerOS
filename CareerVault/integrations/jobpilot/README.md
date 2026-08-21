# JobPilot integration

CareerVault is the source of truth for career facts. JobPilot is the consumer that matches a JD, generates a targeted resume, and fills application forms.

Default local service: `http://127.0.0.1:8766`

## API contract

- `GET /api/jobpilot/profile`
- `GET /api/jobpilot/experiences?resume_ready=true`
- `POST /api/jobpilot/context`

Example request:

```json
{
  "jd": "LLM application engineer, Python, FastAPI, RAG, Agent",
  "limit": 6
}
```

The response contains a merged local profile plus ranked `resume_ready` experiences. JobPilot should treat returned material as factual source data and may rewrite wording, but should never invent new facts.

## Recommended JobPilot behavior

1. Try CareerVault `/api/health`.
2. If available, call `/api/jobpilot/context` for every new JD.
3. Generate the targeted resume from returned experiences.
4. Use the same canonical profile/experience fields for browser autofill.
5. Never auto-submit forms; final submission remains under human control.
