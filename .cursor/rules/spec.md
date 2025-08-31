# Risk Agent API - Spec

## Goal
Build an OpenAI-compatible API service (`/v1/chat/completions`) with an integrated **Risk Detection + Mitigation Agent**.  
Clients can connect their own database, and responses are sanitized before and after LLM usage.  

## Components
1. **FastAPI Service**
   - Endpoint: `/v1/chat/completions`
   - Middleware pipeline:
     1. Input → Sanitize (mask PII: emails, phones, SSNs, credit cards)
     2. Bias/Adversarial check
     3. Decide if DB is needed → run query via db_connector
     4. Call LLM with safe input
     5. Sanitize output
     6. Return response

2. **Risk Detection Engine (`risk_agent.py`)**
   - Functions:
     - `sanitize_text(text)` → return masked text + entities
     - `detect_bias(text)` → True/False
     - `detect_hallucination(input, output)` → score
     - `risk_score(entities, bias, hallucination)` → 0-10

3. **Database Connector (`db_connector.py`)**
   - Support Postgres, MySQL, MongoDB, REST
   - Load client DB config from Supabase
   - Run queries safely, return sanitized results

4. **Dashboard (Next.js + Supabase)**
   - Login (Supabase Auth)
   - Connect DB (save encrypted credentials)
   - Logs page:
     - user input (masked)
     - risks detected
     - mitigation applied
     - final response
   - Settings page:
     - Strictness levels (High/Medium/Low)
     - Choose which risks to block

## Data Flow
User → API → Risk Detection → (DB if needed) → LLM → Risk Detection → User  
Logs → Supabase → Dashboard

## Tech Stack
- Backend: FastAPI (Python)
- Risk Agent: Python (regex + ML models)
- Dashboard: Next.js + Tailwind + Supabase
- Storage: Supabase (logs, configs)
- LLM: OpenAI API (replaceable later)
