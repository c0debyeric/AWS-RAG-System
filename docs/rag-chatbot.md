---
marp: true
theme: default
paginate: true
size: 16:9
header: ''
footer: ''
style: |
  /* ── Base ── */
  section {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 26px;
    padding: 40px 50px;
    background: linear-gradient(170deg, #0a0a1a 0%, #0f1029 60%, #12082a 100%);
    color: #e2e8f0;
    line-height: 1.4;
  }
  /* subtle corner glow on every content slide */
  section::before {
    content: '';
    position: absolute;
    top: -120px; right: -120px;
    width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
  }

  /* ── Lead (title / closing) ── */
  section.lead {
    background: linear-gradient(135deg, #06061a 0%, #0c1445 35%, #1e1060 65%, #2a0e5e 100%);
    color: #FFFFFF;
    text-align: center;
    justify-content: center;
  }
  section.lead::before {
    top: 50%; left: 50%; transform: translate(-50%, -50%);
    width: 700px; height: 700px;
    background: radial-gradient(circle, rgba(99,102,241,0.15) 0%, rgba(168,85,247,0.08) 40%, transparent 70%);
  }
  section.lead h1 { color: #FFFFFF; font-size: 2.0em; border: none; text-shadow: 0 0 40px rgba(99,102,241,0.4); }
  section.lead h2 { color: #a5b4fc; font-weight: 300; letter-spacing: 0.02em; }
  section.lead p   { color: #94a3b8; }

  /* ── Accent (highlight) ── */
  section.accent {
    background: linear-gradient(135deg, #0c1445 0%, #1e1060 40%, #2a0e5e 100%);
    color: #FFFFFF;
  }
  section.accent::before {
    top: -80px; right: -80px;
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(168,85,247,0.15) 0%, transparent 70%);
  }
  section.accent h1, section.accent h2 { color: #FFFFFF; border-color: rgba(165,180,252,0.3); }
  section.accent h3 { color: #c4b5fd; }
  section.accent p, section.accent li { color: #cbd5e1; }

  /* ── Dense slides ── */
  section.dense { font-size: 22px; }
  section.dense h1 { font-size: 1.5em; }
  section.dense h3 { font-size: 1.05em; margin-top: 0.2em; margin-bottom: 0.2em; }

  /* ── Headings ── */
  h1 {
    color: #c4b5fd;
    border-bottom: 2px solid transparent;
    border-image: linear-gradient(90deg, #6366f1, #a855f7, transparent) 1;
    padding-bottom: 6px; font-size: 1.35em; margin-bottom: 0.3em;
  }
  h2 { color: #a5b4fc; font-size: 1.15em; }
  h3 { color: #94a3b8; font-size: 1.0em; margin-top: 0.2em; margin-bottom: 0.2em; }

  /* ── Tables ── */
  table { font-size: 0.82em; width: 100%; border-collapse: collapse; border: none !important; }
  th { background: rgba(99,102,241,0.15) !important; color: #c4b5fd !important; border: none !important; border-bottom: 2px solid rgba(99,102,241,0.4) !important; }
  td { border: none !important; border-bottom: 1px solid rgba(99,102,241,0.1) !important; color: #cbd5e1 !important; background: transparent !important; }
  td, th { padding: 5px 10px; }
  tr:nth-child(even) td { background-color: rgba(99,102,241,0.05) !important; }
  tr { background: transparent !important; }

  /* ── Code ── */
  code { background-color: rgba(99,102,241,0.1); color: #93c5fd; font-size: 0.85em; border: 1px solid rgba(99,102,241,0.2); border-radius: 4px; }
  pre { margin: 0.4em 0; line-height: 1.2; background: linear-gradient(135deg, #0c0c20, #0f1029) !important; border: 1px solid rgba(99,102,241,0.2); border-radius: 8px; }
  pre code { border: none; color: #a5b4fc; background: transparent; }

  /* ── Misc ── */
  strong { color: #c4b5fd; }
  blockquote {
    border-left: 3px solid #6366f1;
    background: linear-gradient(135deg, rgba(99,102,241,0.08), rgba(168,85,247,0.05));
    padding: 0.4em 0.8em;
    margin: 0.4em 0;
    color: #cbd5e1;
    font-style: normal;
    font-size: 0.92em;
    border-radius: 0 6px 6px 0;
  }
  ul, ol { margin: 0.3em 0; }
  li { margin: 0.15em 0; }
  li::marker { color: #6366f1; }
  img[alt~="center"] { display: block; margin: 0 auto; }

  /* ── Pagination ── */
  section::after { color: #475569; font-size: 0.7em; }

  /* ── Two-column grid ── */
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; }
---

<!-- _class: lead -->
<!-- _paginate: skip -->

# SharePoint RAG Chatbot

## AI-Powered Knowledge Assistant for Microsoft Teams

<br>

**Eric Nguyen**
May 2026

---

<!-- _class: dense -->

# The Problem

### Finding information across SharePoint is painful

<div class="columns">
<div>

**What employees experience today:**

- 📂 Documents scattered across multiple SharePoint sites
- 🔍 Native search returns too many irrelevant results
- ⏳ Hours wasted hunting for the right document
- 🔁 Repeat questions to SMEs who already documented answers

</div>
<div>

**The cost of the status quo:**

> *"I know we documented this somewhere, but I can't find it."*

- Employees default to Teams messages instead of self-service
- SMEs become bottlenecks answering the same questions
- Onboarding takes longer than it should
- Decision-making delayed by slow information retrieval

</div>
</div>

---

# The Solution

### An AI chatbot that reads your team documentation — so your engineers don't have to hunt for it

<div class="columns">
<div>

**What we built:**

A **Retrieval-Augmented Generation (RAG)** chatbot that:

1. **Indexes** internal documentation from multiple sources
2. **Understands** natural language questions
3. **Retrieves** the most relevant document sections
4. **Generates** accurate, cited answers
5. **Lives in Teams** — no new tools to learn

</div>
<div>

**How it feels to use:**

> **User:** *"How do I spin up an EC2 instance using Terraform in HCP?"*
>
> **Bot:** *"Use the non-prod HCP Terraform workspace for your service. Open a PR with the EC2 module variables (instance type, subnet, SG, tags), run plan in HCP, then apply after approval. Do not launch from the AWS Console unless break-glass is approved."*
>
> **Sources:** aws-account-onboarding.md, deployment-checklist.md

</div>
</div>

---

<!-- _class: accent -->
<!-- _paginate: skip -->

# Key Capabilities

<div class="columns">
<div>

### 🤖 Intelligent Answers
Claude generates responses grounded in indexed team documentation

### 🔄 Auto-Syncing
Documentation can be ingested from SharePoint, README files, and operational docs

### 📎 Source Citations
Every answer links back to the original source document

</div>
<div>

### 💬 Teams Native
Chat bot directly inside Microsoft Teams — DM or channel

### 🔒 Fully Managed Infra
Serverless API + Lambda with Aurora pgvector as the vector store

### 🏗️ Infrastructure as Code
Terraform-first workflow (HCP Terraform standard process)

</div>
</div>

---

# Architecture Overview

<style scoped>
pre { font-size: 0.68em; line-height: 1.15; }
pre code { color: #a5b4fc; }
h1 { margin-bottom: 0.2em; }
</style>

```
  ┌──────────────┐                         ┌───────────────────┐
  │  MS Teams    │── Bot Framework ─────▶ │ Azure Bot Service │
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
                │ Claude + Titan   │      │ + pgvector           │  │ Structured Logs│
                └──────────────────┘      └──────────────────────┘  └────────────────┘

  ┌──────────────┐   MS Graph API   ┌──────────────────────┐     ┌──────────────┐
  │ SharePoint   │ ───────────────▶ │ SharePoint Sync      │ ──▶ │ S3 Documents │
  │ + Team Docs  │                  │ Lambda (EventBridge) │     └──────┬───────┘
  └──────────────┘                  └──────────────────────┘            │
                                                                          ▼
                                                        ┌───────────────────────────────┐
                                                        │ Additional project sources:    │
                                                        │ - README / markdown files      │
                                                        │ - runbooks / playbooks         │
                                                        │ Ingestion/bootstrap path:      │
                                                        │ - Custom ingest_handler Lambda │
                                                        │ - One-time pgvector setup Lambda│
                                                        └──────────────┬────────────────┘
                                                                       ▼
                                                            ┌──────────────────────┐
                                                            │ Aurora pgvector      │
                                                            │ documents + vectors  │
                                                            └──────────────────────┘
```

---

# How It Works — Data Ingestion

<style scoped>
pre { font-size: 0.65em; line-height: 1.15; }
pre code { color: #a5b4fc; }
ol { font-size: 0.88em; }
h3 { margin-bottom: 0.1em; }
</style>

### Documentation Sources → S3 → Vector Store

```
  ┌──────────────┐   MS Graph API   ┌──────────────────────┐     ┌──────────┐
  │ SharePoint   │ ───────────────▶ │ SharePoint Sync      │ ──▶ │   S3     │
  │ team sites   │                  │ Lambda (scheduled)   │     │ Bucket   │
  └──────────────┘                  └──────────────────────┘     └────┬─────┘
                                                                         │
  ┌──────────────┐   local/repo docs                                     │
  │ README files │ ──────────────────────────────────────────────────────▶│
  │ runbooks     │                                                       │
  └──────────────┘                                                       │
                    ┌────────────────────────────────────────────────────┼────────────────────────────────────┐
                    ▼                                                    ▼                                    ▼
      ┌─────────────────────────────┐                    ┌─────────────────────────────┐       ┌──────────────────┐
      │ One-time setup Lambda       │                    │ ingest_handler Lambda        │       │ Aurora PostgreSQL │
      │ (schema bootstrap only)     │                    │ (parse/chunk/embed on S3)   │       │ + pgvector        │
      └─────────────────────────────┘                    └─────────────────────────────┘       └──────────────────┘
```

1. **EventBridge** triggers SharePoint sync every 6 hours for cloud-hosted docs
2. **Additional sources** such as README files and runbooks can also be ingested
3. Ingestion path uses either **Bedrock KB ingestion job** or **custom ingest_handler**
4. Final indexed chunks/vectors are stored in **Aurora PostgreSQL + pgvector**

---

# How It Works — Query Flow

<style scoped>
pre { font-size: 0.68em; line-height: 1.15; }
pre code { color: #a5b4fc; }
h3 { margin-bottom: 0.1em; }
</style>

### User asks a question → Bot returns a cited answer

```
   User Question                     "How do I provision EC2 with Terraform in HCP?"
        │
        ▼
   ┌──────────────────────┐
   │ Bot Lambda (app.py)  │  ──▶  Parse message + run RAG pipeline
   └───────────┬──────────┘
     │
     ▼
   ┌──────────────────────┐
   │ vector_search()      │  ──▶  embed_query() via Titan + pgvector top-k
   └───────────┬──────────┘
     │
     ▼
   ┌──────────────────────┐
   │ generate_answer()    │  ──▶  Claude answer using retrieved chunks only
   └───────────┬──────────┘
     │
     ▼
   ┌──────────────────────┐
   │ log_query()          │  ──▶  Structured CloudWatch log (latency, sources)
   └───────────┬──────────┘
     │
     ▼
   ┌──────────────────────┐
   │ Response             │  ──▶  Answer + source citations back to Teams
   └──────────────────────┘
```

---

<!-- _class: dense -->

# Technology Stack

<div class="columns">
<div>

### AWS Services

| Service | Role |
|---|---|
| **Bedrock Runtime (Claude)** | Answer generation constrained by retrieved context |
| **Bedrock Runtime (Titan Embed v2)** | Query/chunk embeddings (1024-dim) |
| **Bedrock Knowledge Base** | S3 ingestion path provisioned in Terraform modules |
| **Aurora PostgreSQL** | pgvector — vector store |
| **API Gateway** | HTTPS endpoint for bot webhook |
| **Lambda** | Bot handler + SharePoint sync + optional ingest handler |
| **S3** | Document storage (encrypted) |
| **EventBridge** | Scheduled SharePoint sync trigger |
| **CloudWatch** | Logging & monitoring |
| **Secrets Manager** | SharePoint credentials |

</div>
<div>

### Microsoft / Azure

| Service | Role |
|---|---|
| **Azure Bot Service** | Teams message routing |
| **MS Graph API** | SharePoint document access |
| **Microsoft Teams** | End-user interface |

### Infrastructure

| Tool | Role |
|---|---|
| **Terraform** | Infrastructure as Code |
| **Python 3.11** | Bot + sync Lambda runtime |

</div>
</div>

---

# Security & Compliance

<style scoped>
li { font-size: 0.9em; }
blockquote { font-size: 0.82em; margin-top: 0.6em; border-color: #6366f1; background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(168,85,247,0.06)); }
</style>

<div class="columns">
<div>

### Data Protection

- ✅ **S3 encryption** — KMS server-side encryption
- ✅ **Aurora encryption** — Encrypted at rest
- ✅ **VPC isolation** — Aurora runs in private subnets
- ✅ **No public access** — S3 bucket fully locked down
- ✅ **Secrets Manager** — No credentials in code

</div>
<div>

### Access & Network

- ✅ **IAM least privilege** — Scoped Lambda and Bedrock roles
- ✅ **API Gateway** — HTTPS only, no direct invoke

</div>
</div>

> **Note:** Access controls are enforced through IAM + network controls; workflow actions requiring firewall/TGW updates are routed through ServiceNow approvals.

---

# Supported Document Types

Current ingestion pipeline supports a wide range of documentation sources:

<div class="columns">
<div>

### Documents
- 📄 PDF
- 📝 Word (.doc, .docx)
- 📊 Excel (.xls, .xlsx)
- 📑 PowerPoint (.ppt, .pptx)

### Web Content
- 🌐 HTML / HTM
- 📋 Markdown (.md)

</div>
<div>

### Data Files
- 📊 CSV
- 🔧 JSON
- 📐 XML

### Plain Text
- 📝 TXT

> The sync pipeline automatically filters for supported types and skips unsupported files.

</div>
</div>

---

# Infrastructure as Code

<style scoped>
pre { font-size: 0.78em; line-height: 1.2; }
pre code { color: #93c5fd; }
table { font-size: 0.8em; }
</style>

### Modular Terraform — clean, repeatable, environment-aware

```
terraform/
├── environments/
│   ├── dev/            ← Lower capacity, skip_final_snapshot
│   └── prod/           ← HA, deletion protection, backups
└── modules/
    ├── bedrock-kb/       ← Knowledge Base + Aurora pgvector + S3
    ├── bot-service/      ← API Gateway + Lambda + Bot wiring
    └── sharepoint-sync/  ← Sync Lambda + EventBridge schedule
```

| Decision | Rationale |
|---|---|
| Terraform module structure | Clear ownership across bedrock-kb, bot-service, sharepoint-sync |
| Team standard workflow | HCP Terraform for plan/apply and approval gates |
| State in current repo | S3 backend + lockfile configured in dev environment |
| EC2 provisioning policy | Provision via Terraform workflows, not ad-hoc console changes |

---

# Team-Relevant Example Questions

<style scoped>
li { font-size: 0.9em; }
blockquote { font-size: 0.86em; }
</style>

- **Terraform / HCP**: "How do I spin up an EC2 instance using HCP Terraform?"
- **Security**: "Which instance profiles are required for this EC2 role while maintaining least privilege?"
- **Networking**: "I need a Fortigate firewall rule update in the non-prod TGW account. What ServiceNow request type should I submit?"
- **Operations**: "How does our SSM automation handle patching and domain join?"

> These are the types of questions this assistant is optimized to answer using citations from SharePoint, README files, runbooks, and other internal documentation.

---

<!-- _class: accent -->
<!-- _paginate: skip -->

# Impact & Results

<div class="columns">
<div>

### Before

- Employees spend **15–30 min** searching for answers
- SMEs interrupted **multiple times daily** with repeat questions
- New hires take weeks to find key documentation

</div>
<div>

### After

- Answers in **< 10 seconds** with source citations
- Self-service reduces SME interruptions
- Onboarding accelerated — instant access to institutional knowledge
- **24/7 availability** — the bot never goes on PTO

</div>
</div>

---

# Roadmap — What's Next

| Phase | Focus | Status |
|---|---|---|
| **Phase A — MVP** | End-to-end Teams chatbot with basic RAG | ✅ Complete |
| **Phase B — Advanced RAG** | Hybrid search, reranking, eval pipeline | 🔜 Next |
| **Phase C — LangGraph Agent** | Multi-step reasoning, query routing, memory | 📋 Planned |

<div class="columns">
<div>

### Phase B Highlights
- **Hybrid search** — semantic + keyword for better recall
- **Reranking** — Cohere reranker for precision
- **Eval pipeline** — automated quality metrics

</div>
<div>

### Phase C Highlights
- **Query classification** — route simple vs. complex questions
- **Conversation memory** — multi-turn context and follow-up handling
- **Tool use** — follow-up searches, cross-doc summaries

</div>
</div>

---

<!-- _class: lead -->
<!-- _paginate: skip -->

# Thank You

### Questions?

<br>

**Eric Nguyen**

<br>

*Built with Amazon Bedrock · Microsoft Teams · Terraform*
*Fully serverless · Auto-syncing · Source-cited answers*
