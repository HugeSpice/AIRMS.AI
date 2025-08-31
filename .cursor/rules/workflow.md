User Input
   │
   ▼
Risk Detection Layer (Agent)
   • PII Detection (Presidio, Regex)
   • Bias/Fairness Analysis
   • Adversarial Prompt Detection
   • Toxicity & Safety Filters
   │
   ▼
Mitigation Layer
   • Replace tokens
   • Block unsafe
   • Escalate/report
   │
   ▼
LLM Provider (Groq, OpenAI, Anthropic, etc.)
   │
   ▼
Does LLM require external data?
   ├── No → continue to Output Post-Processing
   │
   └── Yes
        │
        ▼
   Data Access Layer (Secure/Trusted Zone)
        • Query client DB (via connectors: Postgres, Supabase, MySQL, API, etc.)
        • All results sanitized again (no raw PII)
        ▼
   Risk Detection + Mitigation (on fetched data)
        ▼
   Feed sanitized data back to LLM
        ▼
   Loop back until task is resolved
   │
   ▼
Output Post-Processing
   • Hallucination check
   • PII leak check
   • Risk score assignment
   │
   ▼
Risk Report + Dashboard Logs
   │
   ▼
Final Response to User
