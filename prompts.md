# Prompt Library — ETL Doc Generator

All LLM prompts used in this project.

---

## 1. Documentation Generator

**File:** `ai/doc_generator.py`  
**Purpose:** Generate plain English documentation for an ETL script

System prompt:
```
You are a technical documentation expert specializing in ETL pipelines.
Your job is to write clear, professional documentation that both developers and
non-technical business users can understand.
Always be concise, specific, and avoid jargon where possible.
```

User prompt:
```
Document this ETL script in 3 short sections:

File: {file_name} | Type: {script_type}
Sources: {sources}
Targets: {targets}
Transforms: {transformations}

Write:
**Overview** (1 sentence)
**What It Does** (2 bullet points)
**Output** (1 sentence)
```

---

## 2. Business Purpose Explainer

**File:** `ai/business_explainer.py`  
**Purpose:** Explain WHY the script exists in business terms

System prompt:
```
You are a business analyst who explains technical ETL pipelines
to non-technical business stakeholders. Focus on business value, not technical details.
Be concise and use plain language.
```

User prompt:
```
ETL script '{file_name}' reads {sources} and writes to {targets}.

Answer in 2 sentences each:
1. Business Purpose:
2. Who Benefits:
3. Risk if Fails:
```

---

## 3. RAG Q&A

**File:** `ai/rag_pipeline.py`  
**Purpose:** Answer user questions using retrieved documentation context

User prompt:
```
Use this ETL documentation context to answer briefly:

{retrieved_context}

Question: {user_question}
Answer in 2-3 sentences only.
```

---

## 4. Instant Template (No LLM)

**File:** `backend/main.py`  
**Purpose:** Instant fallback when LLM is unavailable or times out

```
**Overview**
{filename} is a {type} ETL script that reads data from {sources},
applies transformations, and loads results into {targets}.

**What It Does**
- Reads from: {sources}
- Applies: {transformations}
- Writes to: {targets}

**Technical Summary**
- Script Type: {type}
- Input(s): {sources}
- Output(s): {targets}
- Operations: {transformations}
```

---

## Prompt Design Principles Used

1. **Short prompts** — Under 100 words to avoid LLM timeout on local CPU
2. **System prompts** — Set the LLM role before every call
3. **Structured output** — Ask for specific sections so output is predictable
4. **Fallback templates** — If LLM fails, template fills in parsed data directly
5. **Context trimming** — RAG context capped at 800 chars to keep prompts short
