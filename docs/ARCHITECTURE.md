# Architecture Decisions

## Overview

This document captures the architectural decisions, trade-offs, and rationale for the Teams SharePoint RAG Chatbot.

---

## ADR-001: Hybrid RAG Architecture (Bedrock KB + LangGraph)

**Decision:** Use Amazon Bedrock Knowledge Bases for document ingestion/retrieval, with LangGraph for orchestration in Phase C.

**Rationale:**
- Bedrock KB has a native SharePoint connector via Microsoft Graph — eliminates custom ETL
- Managed chunking + embedding reduces Week 1–2 effort significantly
- LangGraph layered on top in Phase C adds multi-step reasoning without rewriting ingestion
- Gives portfolio coverage of both managed services AND custom agent architecture

**Trade-offs:**
- Less control over chunking strategy initially (Bedrock KB uses fixed/semantic chunking)
- Aurora pgvector requires VPC setup (subnets, security groups) but keeps costs low (~$50–70/mo)
- Must upgrade to custom retrieval if Bedrock KB hybrid search doesn't meet quality bar

---

## ADR-002: Claude via Bedrock for Generation

**Decision:** Use Anthropic Claude (Sonnet 4) through Amazon Bedrock.

**Rationale:**
- Best-in-class for RAG tasks (instruction following, citation, low hallucination)
- Native Bedrock integration — no external API keys or egress
- Supports Bedrock's RetrieveAndGenerate API directly
- Aligns with existing AWS enterprise footprint

---

## ADR-003: Teams Bot via Azure Bot Service → AWS Backend

**Decision:** Use Azure Bot Service for Teams message routing, with the bot logic hosted on AWS (API Gateway + Lambda).

**Rationale:**
- Azure Bot Service is **required** for Teams integration (Microsoft mandate)
- Bot Service only handles message routing — all logic lives in AWS
- This is a common cross-cloud pattern for enterprises on AWS that use M365

**Flow:**
```
Teams → Azure Bot Service → HTTPS POST → AWS API Gateway → Lambda → Bedrock
```

**Azure resources needed (minimal):**
- Azure Bot registration (free tier)
- Azure AD app registration (for OAuth)
- No Azure compute — everything runs on AWS

---

## ADR-004: No Per-User Permission Filtering (Phase A)

**Decision:** All indexed SharePoint content is available to all bot users.

**Rationale:**
- Dramatically simplifies architecture (no OAuth token passthrough, no Graph API permission checks at query time)
- Acceptable for internal team knowledge bases where content is broadly shared
- Can be added later if scope expands to sensitive content

**Risk:** If SharePoint sites contain restricted docs, those answers will be available to any Teams user who messages the bot. Mitigation: only connect SharePoint sites with broadly-shared content.

---

## ADR-005: Personal Chat First, Channel Bot Later

**Decision:** MVP ships as personal (1:1) chat bot. Channel (@mention) support added in Phase C.

**Rationale:**
- Personal chat is simpler to implement and test
- No threading complexity, no @mention parsing
- Faster to demo to stakeholders
- Channel support is additive (same bot registration, just enable `team` scope)

---

## ADR-006: Aurora PostgreSQL + pgvector as Vector Store

**Decision:** Use Aurora PostgreSQL Serverless v2 with pgvector extension as the vector store for Bedrock KB.

**Alternatives considered:**
- **OpenSearch Serverless (AOSS)** — best hybrid search but minimum $700/mo (2 OCUs), overkill for POC
- **Pinecone** — external dependency, data residency concerns
- **Redis** — limited metadata filtering
- **FAISS (in-memory)** — no persistence, only viable for tiny datasets

**Rationale:**
- Native Bedrock KB integration (RDS storage configuration)
- ~$50–70/mo for dev (Serverless v2 scales to 0.5 ACU) vs $700/mo for AOSS
- Supports pgvector for kNN search + tsvector for keyword search (hybrid)
- Easy upgrade path: swap to OpenSearch Serverless for prod if needed (Terraform config change)
- Aurora Serverless v2 auto-scales — no capacity planning

**Cost note:** db.serverless with 0.5–2.0 ACU range ≈ $50–70/month for dev workloads.

**Upgrade path:** If retrieval quality or scale demands it, switch `storage_configuration` in Terraform from `RDS` to `OPENSEARCH_SERVERLESS` — the KB, data source, and embedding pipeline stay the same.

---

## ADR-007: Terraform for IaC

**Decision:** Terraform with module-per-service pattern.

**Rationale:**
- Matches existing team tooling and workspace conventions (`cis-tool-*` repos)
- HCP Terraform workspace already bootstrapped (see `cis-tool-hcp-bootstrap`)
- Modules can be published to private registry for reuse

---

## Component Details

### SharePoint → Bedrock KB Ingestion

```
SharePoint Site(s)
       │
       │  Microsoft Graph API (app-only auth)
       ▼
┌─────────────────────────────┐
│  Bedrock KB Data Source     │
│  (SharePoint connector)     │
│                             │
│  - Crawl schedule: daily    │
│  - Chunking: semantic       │
│  - Max chunk: 512 tokens    │
│  - Overlap: 20%             │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Embedding Model            │
│  (Titan Embeddings V2)      │
│  1024 dimensions            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  Aurora PostgreSQL          │
│  (pgvector extension)       │
│  - kNN vector search         │
│  - tsvector keyword search   │
│  - Serverless v2 (0.5 ACU)   │
└─────────────────────────────┘
```

### Bot Message Flow (Phase A)

```
1. User sends message in Teams
2. Azure Bot Service routes to messaging endpoint (API Gateway URL)
3. Lambda receives activity JSON
4. Lambda calls Bedrock KB RetrieveAndGenerate API with user query
5. Bedrock retrieves relevant chunks, generates answer with Claude
6. Lambda formats response + source citations
7. Response sent back through Bot Service → Teams
```

### LangGraph Agent Flow (Phase C)

```
1. User sends message
2. Lambda invokes LangGraph graph
3. Router node classifies query:
   ├─ Simple lookup → direct Bedrock KB retrieval
   ├─ Multi-step → decompose into sub-queries
   └─ Clarification needed → ask follow-up question
4. Retriever node(s) fetch relevant chunks
5. Reranker node scores and filters results
6. Generator node produces answer with citations
7. Memory node persists conversation to DynamoDB
8. Response returned to user
```

---

## Security Considerations

| Concern | Mitigation |
|---|---|
| SharePoint API credentials | Stored in AWS Secrets Manager, rotated via Lambda |
| Bot endpoint exposed to internet | API Gateway with request validation + Bot Framework auth token verification |
| Data in transit | TLS everywhere (Teams ↔ Bot Service ↔ API GW ↔ Lambda) |
| Data at rest | Aurora encryption at rest (AWS-managed KMS), S3 SSE |
| Prompt injection | Input sanitization in Lambda, system prompt hardening, output guardrails |
| Overprivileged access | Graph API scoped to `Sites.Read.All` (read-only), no write permissions |

---

## Cost Estimate (Dev Environment)

| Service | Monthly Cost |
|---|---|
| Aurora PostgreSQL Serverless v2 (0.5–2 ACU) | ~$50–70 |
| Bedrock Claude Sonnet (est. 10K queries/mo) | ~$150 |
| Bedrock Titan Embeddings | ~$20 |
| API Gateway + Lambda | ~$5 |
| DynamoDB (on-demand) | ~$5 |
| S3 | ~$1 |
| Azure Bot Service (free tier) | $0 |
| **Total** | **~$250/mo** |

> Note: For production scale, consider upgrading to OpenSearch Serverless (~$700/mo) for better hybrid search performance. The switch is a Terraform config change — no application code changes needed.

---

## Open Questions

- [ ] Which SharePoint site(s) to connect first? (start with one team's docs)
- [ ] Approval for Azure Bot registration in company tenant?
- [ ] Bedrock model access — is Claude already enabled in the account?
- [ ] Network path: does API Gateway need to be private (VPC link) or public is OK?
- [ ] Sync frequency: real-time (webhook) vs. scheduled (daily crawl)?
