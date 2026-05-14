# Kutay Smart CV AI

Production-style AI-powered recruiter assistant and conversational digital twin built with FastAPI, LangGraph, hybrid RAG retrieval, streaming LLM workflows, evaluation pipelines, and observability tooling.

Designed to simulate a real-world AI backend platform focused on:
- retrieval quality
- conversational orchestration
- AI safety
- production backend architecture
- operational reliability
- observability
- evaluation-driven development

---

# Live Demo
Try the live demo: https://kutayural.com

---
# Overview

Kutay Smart CV AI is an AI-powered backend system that allows recruiters, hiring managers, and engineers to interact conversationally with a structured professional knowledge base.

The project was intentionally designed as a production-oriented AI backend rather than a simple chatbot demo.

The system combines:

- Retrieval-Augmented Generation (RAG)
- Hybrid semantic + sparse retrieval
- LangGraph conversational workflows
- Streaming LLM responses (SSE)
- Multi-stage AI guardrails
- Redis conversation memory
- Google Calendar scheduling workflows
- Evaluation pipelines
- Observability instrumentation
- Production-style infrastructure patterns

The goal of the project is to demonstrate how modern AI-enabled backend systems are architected, evaluated, monitored, and operated in production environments.

---

# Features

## AI & Retrieval
- Hybrid Retrieval (Dense + Sparse)
- Semantic Vector Search using Qdrant
- BM25 Sparse Retrieval
- Reciprocal Rank Fusion
- Context Reranking
- Intent-aware retrieval boosting
- Query rewriting
- Retrieval-Augmented Generation (RAG)
- LangGraph orchestration workflows
- Streaming token responses (SSE)
- Conversation memory & contextual continuity

## AI Safety & Guardrails
- Prompt injection detection
- Jailbreak detection
- Input validation
- Output validation
- Scope classification
- Out-of-scope refusal handling
- Context restriction policies

## Backend Engineering
- FastAPI async backend architecture
- Structured logging
- Rate limiting
- Redis-backed conversation state
- Health & readiness probes
- Dockerized infrastructure
- Production-style service organization

## Scheduling & Tooling
- Google Calendar integration
- Availability lookup workflows
- Conversational meeting scheduling
- Slot negotiation workflows
- Multi-step scheduling confirmation flows

## Evaluation & Observability
- Retrieval evaluation pipeline
- Answer quality evaluation
- Token usage tracking
- Workflow timing instrumentation
- Retrieval timing instrumentation
- Structured event logging
- Error tracking

---

# Full System Architecture

text                          ┌───────────────────────┐                          │       Frontend        │                          │  Recruiter Interface  │                          └──────────┬────────────┘                                     │                                     ▼                       ┌──────────────────────────┐                      │     FastAPI Backend      │                      │  Streaming SSE Endpoint  │                      └──────────┬───────────────┘                                 │                                 ▼                      ┌───────────────────────────┐                     │     LangGraph Workflow    │                     └──────────┬────────────────┘                                │          ┌──────────────────────┼─────────────────────────┐         │                      │                         │         ▼                      ▼                         ▼  ┌────────────────┐   ┌──────────────────┐   ┌──────────────────┐ │ Input Guardrail│   │ Intent Detection │   │ Conversation Mem │ │                │   │                  │   │ Redis-backed     │ │ - Jailbreak    │   │ - Query Rewrite  │   │ Multi-turn state │ │ - Prompt Inject│   │ - Intent Class   │   │                  │ │ - Scope Check  │   │ - Entity Tracking│   │                  │ └────────────────┘   └──────────────────┘   └──────────────────┘                                │                                ▼                      ┌────────────────────┐                     │ Query Rewriting    │                     └─────────┬──────────┘                               │                ┌───────────────┴────────────────┐               │                                │               ▼                                ▼     ┌────────────────────┐         ┌────────────────────┐    │ Qdrant Vector Search│         │ BM25 Retrieval     │    │ Semantic Retrieval  │         │ Sparse Retrieval   │    └──────────┬──────────┘         └──────────┬─────────┘               │                               │               └──────────────┬────────────────┘                              ▼                   ┌─────────────────────┐                  │ Hybrid Rank Fusion  │                  └──────────┬──────────┘                             ▼                ┌────────────────────────────┐               │ Intent-Aware Source Boost  │               └──────────┬─────────────────┘                          ▼                  ┌─────────────────────┐                 │ Cross-Encoder       │                 │ Reranking           │                 └──────────┬──────────┘                            ▼                   ┌────────────────────┐                  │ Prompt Construction│                  └──────────┬─────────┘                             ▼                    ┌───────────────────┐                   │ OpenAI LLM Stream │                   └──────────┬────────┘                              ▼                   ┌────────────────────┐                  │ Output Guardrails  │                  └──────────┬─────────┘                             ▼                   ┌────────────────────┐                  │ SSE Token Streaming│                  └────────────────────┘ 

---

# Retrieval & RAG Architecture

The retrieval pipeline is designed as a production-oriented hybrid retrieval system focused on:

- semantic understanding
- keyword precision
- retrieval robustness
- grounding quality
- hallucination reduction
- conversational relevance

Instead of relying purely on vector similarity search, the system combines multiple retrieval strategies and post-processing stages.

---

# Retrieval Pipeline Overview

text User Query    │    ▼ Input Guardrails    │    ▼ Intent Understanding    │    ▼ Question Rewriting    │    ▼ Hybrid Retrieval    ├── Dense Vector Search (Qdrant)    └── Sparse BM25 Retrieval    │    ▼ Reciprocal Rank Fusion    │    ▼ Intent-Aware Source Boosting    │    ▼ Cross-Encoder Reranking    │    ▼ Context Selection    │    ▼ Prompt Construction    │    ▼ Streaming LLM Response 

---

# 1. Multi-Stage Guardrails

Before retrieval begins, the system first validates incoming requests.

The guardrail layer checks for:
- jailbreak attempts
- prompt injection attempts
- malicious instructions
- out-of-scope requests
- unsafe conversational patterns

Only validated requests continue into the retrieval pipeline.

This prevents:
- prompt hijacking
- hidden instruction injection
- context manipulation
- unsafe LLM behaviour

---

# 2. Intent Understanding

The system performs conversational intent classification before retrieval.

The classifier determines:
- whether the request is allowed
- whether the question is in scope
- what type of information is requested
- whether scheduling workflows should activate
- whether the question should be rewritten

Supported intents include:
- projects
- skills
- experience
- visa
- education
- role_fit
- meeting_scheduling
- meeting_confirmation
- personal_context

Intent classification allows retrieval behaviour to dynamically adapt to conversational goals.

---

# 3. Query Rewriting

Natural conversational questions are rewritten into retrieval-optimized semantic queries.

Example:

text Original: "What fintech stuff has he worked on?"  Rewritten: "What fintech systems and payment infrastructure projects has Ahmet Kutay Ural worked on?" 

This improves:
- embedding quality
- retrieval recall
- keyword overlap
- reranking precision

---

# 4. Dense Vector Retrieval (Semantic Search)

The system uses:
- OpenAI embeddings
- Qdrant vector search

## Embedding Model
- text-embedding-3-small

## Vector Database
- Qdrant

Each chunk is embedded with metadata:
- source file
- section
- subsection
- chunk title
- chunk index

This stage captures:
- semantic relationships
- conceptual similarity
- paraphrased recruiter questions
- domain similarity

Example:
A query mentioning:
- "payment infrastructure"

can retrieve:
- transaction routing
- merchant systems
- checkout infrastructure
- fraud prevention pipelines

even without exact keyword overlap.

---

# 5. Sparse Retrieval (BM25)

Alongside vector retrieval, the system performs BM25 sparse retrieval.

BM25 is particularly useful for:
- exact technology names
- project names
- acronyms
- libraries
- company names
- stack references

Examples:
- FastAPI
- Kubernetes
- LangGraph
- Redis
- APIException
- Qdrant

This compensates for one of the weaknesses of pure vector retrieval:
loss of lexical precision.

---

# 6. Hybrid Retrieval Fusion

Dense and sparse retrieval results are merged using reciprocal-rank-style fusion.

The system:
- retrieves candidates from both pipelines
- assigns rank-based scores
- merges duplicates
- fuses rankings into a unified candidate list

This improves:
- retrieval stability
- semantic grounding
- exact-match precision
- overall recall quality

---

# 7. Intent-Aware Source Boosting

After fusion, retrieval scores are adjusted using intent-aware source prioritisation.

Examples:

## Visa Questions
Prefer:
- visa.md

## Skills Questions
Prefer:
- skills.md
- experience.md

## Project Questions
Prefer:
- projects.md
- achievements.md

This reduces retrieval noise and improves factual grounding.

---

# 8. Keyword Overlap Scoring

The system also applies lightweight lexical overlap scoring between:
- rewritten queries
- chunk content
- metadata
- section titles

This improves:
- stack alignment
- exact technology matching
- project relevance scoring

---

# 9. Cross-Encoder Reranking

After retrieval, candidate chunks are reranked using a dedicated reranking stage.

The reranker:
- evaluates query-document relevance directly
- filters weak semantic matches
- improves contextual ordering
- prioritizes highly grounded chunks

Only the strongest candidates are selected for prompt construction.

This significantly improves:
- answer precision
- factual grounding
- retrieval quality
- hallucination reduction

---

# 10. Streaming Generation

The final prompt is streamed to the LLM using Server-Sent Events (SSE).

The streaming pipeline supports:
- incremental token streaming
- low perceived latency
- partial output validation
- output guardrails
- conversational UX improvements

---

# Calendar & Scheduling Workflow Architecture

The project includes an AI-assisted scheduling workflow integrated with Google Calendar.

Scheduling is implemented as a dedicated LangGraph conversational flow.

---

# Scheduling Flow

text User Request    │    ▼ Intent Detection    │    ▼ Availability Workflow    │    ▼ Calendar Availability Query    │    ▼ Candidate Slot Generation    │    ▼ User Confirmation    │    ▼ Meeting Creation    │    ▼ Google Calendar Event 

---

# Scheduling Features

The scheduling workflow supports:
- availability lookup
- working-hour restrictions
- timezone-aware scheduling
- conversational slot negotiation
- multi-turn scheduling flows
- meeting confirmation workflows
- Redis-backed conversation persistence
- Google Calendar event creation

Conversation state stores:
- selected meeting slots
- active scheduling state
- user selections
- scheduling progress

This enables reliable multi-turn scheduling interactions.

---

# Streaming Architecture

Responses are streamed incrementally using Server-Sent Events (SSE).

Streaming pipeline:
- Retrieval
- Prompt construction
- Incremental LLM streaming
- Output validation
- SSE token emission

This reduces perceived latency and improves conversational responsiveness.

---

# Evaluation System

The project includes automated evaluation pipelines.

## Retrieval Evaluation
Measures:
- Hit Rate
- Mean Reciprocal Rank (MRR)

## Answer Evaluation
Measures:
- Expected keyword presence
- Forbidden content checks
- Final pass/fail scoring

Run evaluations:

bash make eval 

Example output:

text FINAL RESULTS Hit Rate: 1.0 MRR: 1.0  FINAL ANSWER EVAL Pass Rate: 1.0 

---

# Observability

The system includes production-style observability instrumentation.

Tracked metrics include:
- embedding latency
- Qdrant latency
- reranking latency
- workflow timing
- token usage
- retrieval metrics
- answer evaluation
- structured event logging
- error tracking

Example logs:

text embedding_query_timing qdrant_query_timing rerank_timing retrieval_pipeline_completed llm_token_usage chat_workflow_completed 

---

# Tech Stack

## Backend
- Python
- FastAPI
- AsyncIO
- Pydantic

## AI Engineering
- OpenAI
- LangGraph
- RAG
- Hybrid Retrieval
- BM25
- Semantic Search
- Qdrant

## Infrastructure
- Docker
- Docker Compose
- Redis
- Qdrant

## Observability
- Structured Logging
- Timing Instrumentation
- Token Usage Tracking

## Evaluation
- Retrieval Evaluation
- Answer Evaluation
- Automated Eval Runner

---

# Project Structure

text app/   ai/     evals/     guardrails/     rag/     workflows/    api/   core/   integrations/   observability/   schemas/   services/  tests/ 

---

# Local Development

## Requirements
- Python 3.12+
- Docker
- OpenAI API Key

---

# Environment Setup

Create a .env file:

env OPENAI_API_KEY=your_key_here 

---

# Install Dependencies

bash uv sync 

---

# Start Infrastructure

bash docker compose up -d 

---

# Ingest Knowledge Base

bash make ingest 

---

# Run API

bash make run 

API:
text http://localhost:8000 

Swagger:
text http://localhost:8000/docs 

---

# Docker

Run full stack:

bash make docker 

---

# API Example

## Streaming Chat Endpoint

http POST /api/v1/chat/stream 

Request:

json {   "message": "What fintech systems has Kutay built?" } 

---

# Example Questions

- What payment systems has Kutay worked on?
- Does Kutay require visa sponsorship?
- What AI systems has Kutay built?
- Has Kutay worked with Kubernetes?
- What open-source work has Kutay done?
- What experience does Kutay have in fraud detection?
- Can I schedule a meeting with Kutay?

---

# Production-Oriented Design Goals

This project intentionally focuses on:

- production-minded backend architecture
- AI reliability
- retrieval quality
- observability
- evaluation-driven development
- conversational workflow orchestration
- operational maintainability
- scalable AI backend design

The goal is to simulate how modern AI-enabled backend systems are designed and operated in production environments.

---

# Author

Ahmet Kutay Ural

Backend Engineer focused on:
- AI Engineering
- Backend Platform Engineering
- FinTech Infrastructure
- Intelligent Systems
- Production AI Applications