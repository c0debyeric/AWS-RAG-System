# Teams SharePoint RAG Chatbot

AWS-based RAG chatbot that indexes SharePoint content and serves answers through Microsoft Teams.

## Project Overview

| Item | Decision |
|---|---|
| **Purpose** | Internal knowledge assistant for Royal Caribbean teams |
| **Data Source** | SharePoint (mixed: docs, spreadsheets, PDFs) |
| **Architecture** | Hybrid — Bedrock KB ingestion + LangGraph orchestration |
| **LLM** | Claude (Anthropic) via Amazon Bedrock |
| **Interface** | Microsoft Teams bot (personal chat → channel) |
| **Auth Model** | No per-user filtering; all indexed content available to all bot users |
| **IaC** | Terraform |
| **Timeline** | 1–2 months production-ready |

---

## Phased Implementation Plan

### Phase A — MVP (Weeks 1–3)

> Goal: Working end-to-end chatbot in Teams with basic RAG

| Week | Deliverable |
|---|---|
| 1 | Terraform foundation: VPC, Bedrock KB with SharePoint connector, S3 bucket for metadata |
| 2 | Teams bot registration (Azure Bot Service) + Lambda/ECS handler wired to Bedrock KB RetrieveAndGenerate API |
| 3 | Integration testing, prompt tuning, deploy to dev Teams tenant |

**Exit criteria:** User can DM the bot in Teams, ask a question, get an answer sourced from SharePoint docs.

---

### Phase B — Advanced RAG (Weeks 4–6)

> Goal: Hybrid search, reranking, eval pipeline (aligns with Phase 1 coursework)

| Week | Deliverable |
|---|---|
| 4 | Add hybrid search (semantic + keyword) via OpenSearch Serverless or Bedrock KB hybrid mode |
| 5 | Add reranking (Cohere reranker via Bedrock or custom Lambda) |
| 6 | Eval pipeline with DeepEval/Ragas — measure retrieval quality, answer faithfulness |

**Exit criteria:** Measurable improvement in answer quality. Eval dashboard tracking precision/recall/faithfulness.

---

### Phase C — LangGraph Agent (Weeks 7–9, aligns with Phase 2)

> Goal: Multi-step reasoning, query routing, tool use

| Week | Deliverable |
|---|---|
| 7 | Replace simple retrieve-generate with LangGraph agent. Add query classification node (simple lookup vs. multi-step) |
| 8 | Add tool nodes: SharePoint search, follow-up retrieval, summarization |
| 9 | Conversation memory (DynamoDB), channel bot support, production hardening |

**Exit criteria:** Bot handles complex multi-turn questions, routes between retrieval strategies, maintains context.

---

## Architecture (High Level)

```
┌─────────────────┐     HTTPS/Bot Framework     ┌──────────────────────┐
│  Microsoft Teams │ ──────────────────────────▶ │  Azure Bot Service   │
│  (User)          │                             │  (message routing)   │
└─────────────────┘                             └──────────┬───────────┘
                                                           │
                                                           ▼
                                                ┌──────────────────────┐
                                                │  AWS API Gateway     │
                                                │  + Lambda / ECS      │
                                                │  (Bot Handler)       │
                                                └──────────┬───────────┘
                                                           │
                                          ┌────────────────┼────────────────┐
                                          ▼                ▼                ▼
                                ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
                                │ Bedrock KB   │ │ LangGraph    │ │ DynamoDB     │
                                │ (Ingestion   │ │ Orchestrator │ │ (Conversation│
                                │  + Retrieval)│ │ (Phase C)    │ │  Memory)     │
                                └──────┬───────┘ └──────────────┘ └──────────────┘
                                       │
                              ┌────────┼────────┐
                              ▼        ▼        ▼
                        ┌─────────┐ ┌──────┐ ┌────────────────┐
                        │ Aurora   │ │  S3  │ │ SharePoint     │
                        │PostgreSQL│ │      │ │ (via MS Graph  │
                        │(pgvector)│ │      │ │  connector)    │
                        └─────────┘ └──────┘ └────────────────┘
```

---

## Folder Structure

```
cis-tool-teams-rag-chatbot/
├── README.md                    ← You are here
├── docs/
│   └── ARCHITECTURE.md          ← Detailed architecture decisions
├── terraform/
│   ├── environments/
│   │   ├── dev/                 ← Dev workspace config
│   │   └── prod/                ← Prod workspace config
│   └── modules/
│       ├── bedrock-kb/          ← Knowledge Base + data source + vector store
│       ├── bot-service/         ← API Gateway + Lambda + Bot config
│       └── networking/          ← VPC, security groups, endpoints
├── src/
│   ├── bot/                     ← Teams bot handler (Python)
│   └── orchestrator/            ← LangGraph agent (Phase C)
└── tests/                       ← Eval pipeline + integration tests
```

---

## Prerequisites

- AWS account with Bedrock model access (Claude) enabled
- Azure AD app registration (for Teams bot)
- SharePoint site with Graph API permissions granted
- Terraform >= 1.5
- Python >= 3.13

---

## Quick Start

```bash
# 1. Deploy infrastructure
cd terraform/environments/dev
terraform init && terraform apply

# 2. Register Teams bot in Azure portal (see docs/ARCHITECTURE.md)

# 3. Run bot locally for testing
cd src/bot
pip install -r requirements.txt
python app.py
```

---

## Key AWS Services

| Service | Purpose |
|---|---|
| Amazon Bedrock (Knowledge Bases) | Document ingestion, chunking, embedding, retrieval |
| Amazon Bedrock (Claude) | Answer generation |
| Aurora PostgreSQL + pgvector | Vector store for embeddings |
| API Gateway + Lambda | Bot webhook endpoint |
| DynamoDB | Conversation history (Phase C) |
| S3 | Metadata, logs, eval datasets |
| CloudWatch | Monitoring, logging |

---

## Related Docs

- [Architecture Decisions](docs/ARCHITECTURE.md)
- [AI Engineer Transition Plan](file:///C:/Users/123re/Documents/_IMPORTANT/biz-workspace/_vault/career/ai-engineer-transition-plan-2026.md)
