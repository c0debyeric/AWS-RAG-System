<div align="center">

# 🤖 Enterprise RAG Chatbot

### AI-Powered Knowledge Assistant for Microsoft Teams

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://python.org)
[![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)](https://terraform.io)
[![AWS](https://img.shields.io/badge/AWS-Bedrock%20%7C%20Aurora%20%7C%20Lambda-FF9900?logo=amazonwebservices&logoColor=white)](https://aws.amazon.com/bedrock/)
[![Teams](https://img.shields.io/badge/Microsoft%20Teams-Bot-6264A7?logo=microsoftteams&logoColor=white)](https://www.microsoft.com/en-us/microsoft-teams)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production **Retrieval-Augmented Generation (RAG)** chatbot that indexes internal documentation from SharePoint, generates accurate answers with source citations using Amazon Bedrock (Claude), and delivers them natively inside Microsoft Teams — reducing information retrieval time from **15–30 minutes to under 10 seconds**.

[Architecture](#architecture) · [Features](#features) · [Tech Stack](#tech-stack) · [Getting Started](#getting-started) · [How It Works](#how-it-works) · [Roadmap](#roadmap)

</div>

---

## 💡 The Problem

Documentation scattered across SharePoint, wikis, runbooks, and repos creates a painful knowledge discovery experience:

- **Employees spend 15–30 minutes** searching for answers that already exist somewhere
- **SMEs become bottlenecks** answering the same questions repeatedly
- **Onboarding takes longer** than it should — new hires can't find key docs
- **No single search** spans all internal sources effectively

> *"I know we documented this somewhere, but I can't find it."*

## ✅ The Solution

An AI chatbot that **reads your team's documentation** — so your engineers don't have to hunt for it.

```
You:  "How do I provision an EC2 instance using Terraform in our HCP workspace?"

Bot:  "Use the non-prod HCP Terraform workspace for your service. Open a PR with
       the EC2 module variables (instance type, subnet, SG, tags), run plan in HCP,
       then apply after approval. Do not launch from the AWS Console unless
       break-glass is approved."

       📎 Sources: aws-account-onboarding.md, deployment-checklist.md
```

**Every answer is grounded in your indexed documents and includes source citations.**

---

## Architecture

```
┌──────────────┐                         ┌───────────────────┐
│  MS Teams    │── Bot Framework ───────▶│ Azure Bot Service │
│  (Users)     │                         └────────┬──────────┘
└──────────────┘                                  │ HTTPS
                                                  ▼
                                       ┌──────────────────────┐
                                       │ AWS API Gateway      │
                                       │ + Bot Lambda         │
                                       └──────────┬───────────┘
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        ▼                         ▼                         ▼
              ┌──────────────────┐      ┌──────────────────────┐  ┌────────────────┐
              │ Bedrock Runtime  │      │ Aurora PostgreSQL    │  │ CloudWatch     │
              │ Claude + Titan   │      │ + pgvector (HNSW)    │  │ Structured Logs│
              └──────────────────┘      └──────────────────────┘  └────────────────┘

┌──────────────┐   MS Graph API   ┌──────────────────────┐     ┌──────────────┐
│ SharePoint   │ ───────────────▶ │ SharePoint Sync      │ ──▶ │ S3 Documents │
│ + Team Docs  │                  │ Lambda (EventBridge) │     └──────┬───────┘
└──────────────┘                  └──────────────────────┘            │
                                                                     ▼
                                                      ┌────────────────────────┐
                                                      │ Ingest Lambda          │
                                                      │ Parse → Chunk → Embed  │
                                                      │ → Store (pgvector)     │
                                                      └────────────────────────┘
```

### Query Flow

```
User Question → Bot Lambda → embed_query() (Titan) → pgvector top-k search
                                                            ↓
Teams Response ← format + cite ← generate_answer() (Claude) ← retrieved chunks
                                                            ↓
                                                   log_query() → CloudWatch
```

### Ingestion Flow

```
SharePoint ──(Graph API)──▶ S3 ──(event)──▶ Ingest Lambda
                                                  ├→ parse_file()     (PDF, DOCX, XLSX, PPTX, MD, HTML, CSV)
                                                  ├→ chunk()          (recursive, token-aware, boundary-respecting)
                                                  ├→ embed_texts()    (Titan Embed v2, 1024-dim)
                                                  └→ store_chunks()   (Aurora pgvector + HNSW index)
```

---

## Features

| Feature | Description |
|---|---|
| **🔍 Semantic Search** | HNSW cosine similarity search over 1024-dim Titan embeddings via pgvector |
| **🤖 Grounded Answers** | Claude generates responses constrained to retrieved context only — no hallucination |
| **📎 Source Citations** | Every answer links back to the original source document |
| **📄 Multi-Format Ingestion** | PDF, DOCX, XLSX, PPTX, Markdown, HTML, CSV, and plain text |
| **🔄 Auto-Syncing** | EventBridge triggers SharePoint sync every 6 hours via Microsoft Graph API |
| **💬 Teams Native** | Chat in DMs, channels, or group chats — no new tools to learn |
| **🧩 Token-Aware Chunking** | Recursive text splitter respects paragraph/sentence boundaries with tiktoken sizing |
| **📊 Structured Logging** | JSON CloudWatch logs with latency, token counts, sources — queryable via Logs Insights |
| **🔒 Secure by Default** | VPC-isolated Lambdas, encrypted S3, Secrets Manager for all credentials |
| **⚡ Serverless** | Aurora Serverless v2 (0.5–2 ACU) + Lambda — scales to zero, pay per use |
| **🏗️ Infrastructure as Code** | 100% Terraform — reproducible, version-controlled, modular |

---

## Tech Stack

<table>
<tr><td><b>Category</b></td><td><b>Technology</b></td><td><b>Purpose</b></td></tr>
<tr><td rowspan="2"><b>AI / LLM</b></td><td>Claude 3.5 Sonnet (Bedrock)</td><td>Answer generation via Converse API</td></tr>
<tr><td>Titan Embed Text v2 (Bedrock)</td><td>1024-dim document & query embeddings</td></tr>
<tr><td rowspan="2"><b>Vector Store</b></td><td>Aurora PostgreSQL + pgvector</td><td>Serverless v2 vector database</td></tr>
<tr><td>HNSW Index</td><td>Cosine similarity (m=16, ef_construction=200)</td></tr>
<tr><td rowspan="5"><b>AWS</b></td><td>Lambda (Python 3.13)</td><td>Bot handler, ingestion, SharePoint sync, DB setup</td></tr>
<tr><td>API Gateway (HTTP API)</td><td>HTTPS endpoint for Teams webhook</td></tr>
<tr><td>S3</td><td>Encrypted document storage</td></tr>
<tr><td>EventBridge Scheduler</td><td>Automated SharePoint sync (every 6h)</td></tr>
<tr><td>Secrets Manager</td><td>Database & SharePoint credentials</td></tr>
<tr><td rowspan="3"><b>Azure</b></td><td>Azure Bot Service</td><td>Teams message routing</td></tr>
<tr><td>Microsoft Graph API</td><td>SharePoint document access (MSAL)</td></tr>
<tr><td>Microsoft Teams</td><td>End-user chat interface</td></tr>
<tr><td rowspan="3"><b>Tooling</b></td><td>Terraform</td><td>Infrastructure as Code (modular)</td></tr>
<tr><td>Docker (pgvector:pg16)</td><td>Local development database</td></tr>
<tr><td>pytest + ruff</td><td>Testing & linting</td></tr>
</table>

---

## Project Structure

```
├── src/
│   ├── bot/
│   │   └── app.py                    # Teams bot Lambda handler (RAG pipeline)
│   ├── ingestion/
│   │   ├── chunker.py                # Recursive token-aware text splitter
│   │   ├── embedder.py               # Bedrock Titan embedding wrapper
│   │   ├── loader.py                 # Ingestion orchestrator (local + S3)
│   │   ├── store.py                  # pgvector storage operations
│   │   └── parsers/                  # Multi-format document parsers
│   │       ├── pdf_parser.py         #   ├── PDF (pdfplumber)
│   │       ├── docx_parser.py        #   ├── Word (python-docx)
│   │       ├── xlsx_parser.py        #   ├── Excel (openpyxl)
│   │       ├── pptx_parser.py        #   ├── PowerPoint (python-pptx)
│   │       ├── html_parser.py        #   ├── HTML (BeautifulSoup)
│   │       ├── csv_parser.py         #   ├── CSV
│   │       └── markdown_parser.py    #   └── Markdown
│   ├── retrieval/
│   │   ├── search.py                 # pgvector cosine similarity search
│   │   └── generator.py             # Bedrock Claude answer generation
│   ├── sharepoint_sync/
│   │   └── sync.py                   # SharePoint → S3 sync (Graph API + MSAL)
│   ├── conversation_logging/
│   │   └── logger.py                 # Structured CloudWatch JSON logging
│   └── common/
│       ├── config.py                 # Centralized env-based configuration
│       ├── db.py                     # pgvector connection pool (singleton)
│       └── aws_clients.py           # Cached boto3 client factories
├── lambdas/
│   ├── ingest_handler.py            # S3 event → parse → chunk → embed → store
│   └── setup_handler.py             # One-time pgvector schema initialization
├── scripts/
│   ├── setup_pgvector.py            # DB schema + HNSW index creation
│   ├── ingest.py                    # CLI batch ingestion tool
│   ├── query.py                     # Interactive RAG testing REPL
│   └── package_lambdas.py           # Lambda deployment zip builder
├── terraform/
│   ├── environments/
│   │   └── dev/                     # Dev workspace (remote S3 state)
│   └── modules/
│       ├── bedrock-kb/              # Aurora + S3 + Secrets Manager
│       ├── bot-service/             # Lambda + API Gateway + IAM
│       └── sharepoint-sync/         # Sync Lambda + EventBridge schedule
├── teams-app/
│   └── manifest.json               # Teams app manifest (bot config)
├── tests/                           # pytest unit & integration tests
├── data/sample_docs/                # Sample documentation for testing
├── docker-compose.yml               # Local pgvector (PostgreSQL 16)
├── Makefile                         # Dev workflow commands
└── pyproject.toml                   # Dependencies & tool config
```

---

## Getting Started

### Prerequisites

- **AWS Account** with Bedrock model access enabled (Claude 3.5 Sonnet + Titan Embed v2)
- **Azure AD / Entra ID** app registration (for Teams bot + SharePoint access)
- **Terraform** >= 1.5
- **Python** >= 3.13
- **Docker** (for local development)

### 1. Clone & Install

```bash
git clone https://github.com/c0debyeric/enterprise-rag-chatbot.git
cd enterprise-rag-chatbot
pip install -e ".[dev,sync]"
```

### 2. Local Development

```bash
# Start local pgvector database
make dev-db

# Initialize database schema + HNSW indexes
make setup-db

# Ingest sample documents
make ingest ARGS='--source data/sample_docs'

# Test the RAG pipeline interactively
make query
```

### 3. Deploy Infrastructure

```bash
cd terraform/environments/dev
terraform init
terraform apply
```

### 4. Register Teams Bot

Follow the step-by-step guide in [docs/SETUP-AZURE.md](docs/SETUP-AZURE.md) to:
1. Create a Microsoft Entra ID app registration
2. Configure SharePoint API permissions (Sites.Read.All)
3. Register an Azure Bot Service resource
4. Set the messaging endpoint to your API Gateway URL
5. Enable the Teams channel and install the app

### 5. Run Tests

```bash
make test    # pytest with verbose output
make lint    # ruff linter
```

---

## How It Works

### Document Ingestion Pipeline

1. **Sync** — EventBridge triggers a Lambda every 6 hours that authenticates to Microsoft Graph API via MSAL, compares timestamps, and syncs only changed files from SharePoint to S3
2. **Parse** — S3 upload events trigger the ingestion Lambda, which routes files through format-specific parsers (PDF, DOCX, XLSX, PPTX, HTML, CSV, Markdown)
3. **Chunk** — A recursive text splitter breaks documents into token-aware chunks (default 512 tokens, 100 overlap) that respect natural boundaries (paragraphs → sentences → words)
4. **Embed** — Each chunk is embedded via Bedrock Titan Embed Text v2 into a 1024-dimensional vector
5. **Store** — Chunks and embeddings are inserted into Aurora PostgreSQL with a pgvector HNSW index for fast cosine similarity search

### Query Pipeline

1. **Receive** — User sends a question in Microsoft Teams → Azure Bot Service routes to API Gateway → Bot Lambda
2. **Search** — The query is embedded with Titan and searched against pgvector using HNSW cosine similarity (top-k retrieval)
3. **Generate** — Retrieved chunks are passed as context to Claude 3.5 Sonnet via the Bedrock Converse API (temperature 0.0, grounded generation)
4. **Respond** — The answer with source citations is sent back to Teams via Bot Framework API
5. **Log** — Structured JSON logs (query, latency, token counts, sources) are emitted to CloudWatch for observability

---

## Makefile Commands

| Command | Description |
|---|---|
| `make dev-db` | Start local pgvector container (PostgreSQL 16) |
| `make setup-db` | Create pgvector extension, documents table, and HNSW indexes |
| `make ingest ARGS='--source <path>'` | Batch ingest documents from a directory or S3 |
| `make query` | Interactive RAG query REPL for local testing |
| `make test` | Run pytest suite with verbose output |
| `make lint` | Run ruff linter across src, tests, and scripts |
| `make package` | Build Lambda deployment zip packages |
| `make clean` | Remove build artifacts and caches |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Custom pgvector over managed Bedrock KB** | Full control over chunking strategy, token-aware sizing, and future reranking (Phase B) |
| **HNSW index (m=16, ef_construction=200)** | Sub-20ms search at scale with cosine similarity — optimal for RAG workloads |
| **Recursive boundary-respecting chunker** | Preserves semantic coherence by splitting at paragraph → sentence → word boundaries |
| **tiktoken (cl100k_base) for sizing** | Accurate token counting prevents Bedrock context window overflow |
| **Aurora Serverless v2 (0.5–2 ACU)** | Scales to zero in dev, handles production load — cost-effective for variable traffic |
| **Converse API (model-agnostic)** | Swap LLMs (Claude → Nova → Llama) without code changes |
| **Singleton boto3 clients (@lru_cache)** | Reduces Lambda cold start latency by reusing connections across invocations |

---

## Roadmap

| Phase | Focus | Status |
|---|---|---|
| **Phase A — MVP** | End-to-end Teams chatbot with semantic search RAG | ✅ Complete |
| **Phase B — Advanced RAG** | Hybrid search (semantic + keyword), Cohere reranking, eval pipeline (DeepEval/Ragas) | 🔜 Next |
| **Phase C — LangGraph Agent** | Multi-step reasoning, query routing, conversation memory (DynamoDB), tool use | 📋 Planned |

<details>
<summary><b>Phase B Details</b></summary>

- Hybrid search combining semantic embeddings with keyword matching (BM25)
- Cohere reranker via Bedrock for precision improvement
- Automated evaluation pipeline with DeepEval/Ragas measuring retrieval quality, answer faithfulness, and relevance

</details>

<details>
<summary><b>Phase C Details</b></summary>

- LangGraph agent replacing simple retrieve-generate with multi-step reasoning
- Query classification node (simple lookup vs. complex multi-step)
- Conversation memory via DynamoDB for multi-turn context
- Tool nodes: follow-up retrieval, cross-document summarization

</details>

---

## Documentation

- [Azure / Entra ID Setup Guide](docs/SETUP-AZURE.md) — Step-by-step Teams bot + SharePoint registration
- [Presentation Deck](docs/rag-chatbot.md) — Marp slide deck with architecture diagrams and business impact

<!-- ## Demo

> 📸 Screenshots and demo GIF coming soon

-->

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built by [Eric Nguyen](https://github.com/c0debyeric)**

Amazon Bedrock · Microsoft Teams · Terraform · Aurora pgvector

*Fully serverless · Auto-syncing · Source-cited answers*

</div>
