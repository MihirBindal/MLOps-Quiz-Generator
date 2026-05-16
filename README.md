# 🧠 AI Quiz Master: MLOps-Powered Quiz Generation Platform

AI Quiz Master is an end-to-end, microservices-based platform that automates the creation of high-quality technical quizzes from documents (PDF, DOCX, PPTX). Built with **MLOps** best practices, it features a robust RAG (Retrieval-Augmented Generation) pipeline, secure secret management, and centralized observability.

## 🚀 Project Overview

The platform allows users to upload technical documentation, which is then vectorized and stored in a knowledge base. Users can generate targeted or global quizzes, which are synthesized by the **Google Gemini 1.5 Flash** model using context-aware prompts.

### Key Features
- **RAG Pipeline:** Uses LangChain and Qdrant for precise context retrieval.
- **Microservices Architecture:** Independently scalable Frontend, Ingest, and Generate services.
- **Zero-Trust Security:** Secure API key management via HashiCorp Vault sidecar injection.
- **Elastic Scaling:** Automated horizontal scaling using Kubernetes HPA.
- **Observability:** Centralized logging and analytics via the ELK Stack (Elasticsearch, Logstash, Kibana).

---

## 🏗️ Architecture

The system is composed of three primary microservices:
1.  **Frontend (Streamlit):** The interactive UI for document uploads and quiz taking.
2.  **Ingest API (FastAPI):** Handles document parsing, chunking, and vector embedding storage.
3.  **Generate API (FastAPI):** Orchestrates the AI generation logic and prompt engineering.

---

## 📂 Project Structure

```bash
.
├── frontend/                # Streamlit UI Microservice
│   ├── app.py               # Main UI logic and session state management
│   ├── Dockerfile           # Single-stage Docker build
│   └── Jenkinsfile          # CI/CD pipeline for the frontend
├── generate/                # AI Orchestration Microservice
│   ├── main.py              # FastAPI app and RAG logic
│   ├── prompt_template.py   # 3-tier AI instruction hierarchy
│   ├── jsonclass.py         # Pydantic models for structured AI output
│   ├── Dockerfile           # Multi-stage build with build-gate tests
│   └── Jenkinsfile          # CI/CD pipeline with automated testing
├── ingest/                  # Data Ingestion Microservice
│   ├── main.py              # Document processing and vectorization logic
│   ├── parsers/             # Specialized parsers for PDF, DOCX, PPTX
│   ├── Dockerfile           # Multi-stage build with system dependencies
│   └── Jenkinsfile          # CI/CD pipeline for data ingestion
├── devops/                  # Infrastructure as Code (IaC)
│   ├── ansible/             # Ansible playbooks and roles for deployment
│   ├── apis.yaml            # K8s manifests for Backend services
│   ├── frontend.yaml        # K8s manifests for the UI
│   ├── hpa.yaml             # Horizontal Pod Autoscaler configuration
│   ├── qdrant.yaml          # Vector Database orchestration
│   └── elk-stack/           # K8s manifests for ELK (Elasticsearch, Logstash, Kibana)
├── tests/                   # Automated Testing Suite
│   ├── test_generate.py     # Unit tests for AI service (FastAPI TestClient)
│   └── test_ingest.py       # Unit tests for Ingest service
└── docker-compose.yaml      # Local orchestration for development
```

---

## 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **AI & ML** | LangChain, Google Gemini 1.5 Flash, HuggingFace (MiniLM-L6-v2) |
| **Backend** | Python, FastAPI, Uvicorn, Pydantic |
| **Frontend** | Streamlit |
| **Database** | Qdrant (Vector DB) |
| **DevOps** | Docker, Kubernetes (Minikube), Jenkins, Ansible |
| **Security** | HashiCorp Vault (Sidecar Injection), Ansible Vault |
| **Observability** | ELK Stack (Elasticsearch, Logstash, Kibana), Filebeat |

---

## ⚙️ Setup & Deployment

### Local Development (Docker Compose)
To run the entire stack locally:
```bash
docker-compose up --build
```

### Production Deployment (Kubernetes)
The deployment is automated via Jenkins. The pipeline follows these steps:
1.  **Test Gate:** Runs `pytest` inside a Docker builder container.
2.  **Build & Push:** Builds a lightweight production image and pushes to Docker Hub.
3.  **Ansible Deploy:** Executes playbooks to apply K8s manifests and perform a rolling update.

---

## 👥 Authors
- **Asutosh Panda** (MT2025025) - AI Pipeline, Frontend, & Security.
- **Mihir Bindal** (MT2025072) - Ingestion Pipeline, Infrastructure, & Monitoring.
