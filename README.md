# Financial AI Agent

An AI agent for financial report analysis combining a multimodal RAG architecture, hybrid retrieval prioritizing tabular data, and secure visualization generation — designed to minimize the risk of hallucination on numerical data.

---

## About

**Financial AI Agent** lets you upload one or more financial reports (PDF) and query them in natural language: factual questions, comparisons, variation calculations, chart generation — all with systematic source citation and a semantic similarity score for every claim.

The project addresses a concrete problem encountered when analyzing banking reports (tested on Coris Holding annual reports, WAEMU region): critical numerical data is often buried inside tables, which classic semantic search tends to overlook in favor of narrative paragraphs that are semantically close but less precise.

## Features

- **Multimodal extraction** — text (PyMuPDF), structured tables (Docling), image/chart description (Gemini Vision)
- **Hybrid retrieval** — combines general semantic search with a priority search on tables to guarantee critical numerical data is included in context
- **Analytical reasoning** — the agent compares, calculates, and cross-references multiple sources instead of just doing a literal lookup, while explicitly distinguishing extracted data from calculated data
- **Chart generation** — automatic detection of the appropriate visualization type (trend, comparison, ranking, breakdown, gap) and code generation executed in an isolated sandbox
- **Anti-hallucination validation** — numerical values in the generated chart code are checked against the document context before being displayed
- **Audit mode** — every response cites its exact sources (document, page, excerpt) along with a cosine similarity score
- **Multi-document support** — simultaneous analysis and comparison of several reports
- **Conversation history** — persistent chat threads, browsable and resumable
- **Visualization report** — selection and storage of generated charts in a dedicated space

## Architecture
## Architecture

### System overview

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        FE["React + Vite Frontend<br/>(localhost:5173)<br/>Overview · Documents · Analysis · Chat · Reports"]
    end

    subgraph App["Application Layer"]
        API["Flask REST API<br/>(localhost:5000)"]
    end

    subgraph Storage["Storage Layer"]
        PG[("PostgreSQL<br/>Documents, Conversations,<br/>Chat history")]
        CLD[("Cloudinary<br/>PDF file storage")]
        CHR[("ChromaDB<br/>Vector store<br/>(cosine distance)")]
    end

    EMB["Sentence-Transformers<br/>(multilingual embeddings)"]

    FE -->|HTTP / Axios| API
    API --> PG
    API --> CLD
    API --> CHR
    CHR --> EMB

    style Client fill:#EEF2F0,stroke:#16233E
    style App fill:#E4EFE9,stroke:#0E7C5A
    style Storage fill:#F6EFE1,stroke:#9C7A3C
```

### Document processing pipeline (triggered on `/upload/index`)

```mermaid
flowchart LR
    A[PDF uploaded] --> B["PyMuPDF<br/>text extraction<br/>(page by page)"]
    A --> C["Docling<br/>structured table<br/>extraction"]
    A --> D["Gemini Vision<br/>image/chart<br/>description"]

    B --> E["Chunking +<br/>Metadata tagging<br/>(document_id, filename, page, type)"]
    C --> E
    D --> E

    E --> F["Embeddings<br/>(Sentence-Transformers)"]
    F --> G[("ChromaDB")]

    style A fill:#F7F8FA,stroke:#5B6472
    style G fill:#EEF2F0,stroke:#16233E
```

### Question-answering flow (triggered on `/upload/chat`)

```mermaid
flowchart TB
    Q[User question] --> H["Hybrid Retrieval"]

    subgraph H["Hybrid Retrieval"]
        direction LR
        S1["General semantic<br/>search (ChromaDB)"]
        S2["Table-priority<br/>search (ChromaDB)"]
    end

    H --> M["Merge + Dedupe +<br/>Rank by similarity"]
    M --> CTX["Context construction<br/>(with sources: doc, page, type)"]
    CTX --> LLM["Gemini<br/>(financial analyst prompt)<br/>→ analysis, calculations, comparisons"]
    LLM --> OUT["Answer + Sources +<br/>Similarity scores"]
    OUT --> DB[("Saved to PostgreSQL")]

    style H fill:#EEF2F0,stroke:#16233E
    style LLM fill:#E4EFE9,stroke:#0E7C5A
```

### Chart generation flow (triggered on `/upload/chart`)

```mermaid
flowchart TB
    Q[User question] --> I["Intent classification<br/>(trend / comparison / ranking /<br/>breakdown / gap / single value)"]
    I --> G["Gemini generates<br/>Matplotlib code"]
    G --> V{"Numerical validation<br/>(code values vs.<br/>document context)"}
    V -->|fails| R["Retry with<br/>correction prompt"]
    R --> G
    V -->|passes| E["E2B sandbox execution<br/>(isolated from main server)"]
    E --> C["chart.png retrieved"]
    C --> S["Served via<br/>/upload/chart-image"]

    style V fill:#F6EFE1,stroke:#9C7A3C
    style E fill:#FBE9E5,stroke:#B3261E
    style S fill:#E4EFE9,stroke:#0E7C5A
```
**Indexing pipeline**: Upload → Cloudinary → extraction (text/tables/images) → chunking → embeddings → ChromaDB

**Question pipeline**: Question → hybrid retrieval (semantic + table priority) → context construction → Gemini → answer + sources

**Chart pipeline**: Question → type detection → code generation (Gemini) → numerical validation → isolated execution (E2B) → image

## Tech stack

| Domain | Technologies |
|---|---|
| Backend | Python, Flask, SQLAlchemy |
| Frontend | React, Vite, Axios, React Markdown, Lucide Icons |
| Relational database | PostgreSQL |
| Vector database | ChromaDB (cosine distance) |
| File storage | Cloudinary |
| Generative AI | Google Gemini API |
| Embeddings | Sentence-Transformers (`paraphrase-multilingual-MiniLM-L12-v2`) |
| Document extraction | PyMuPDF, Docling |
| Code execution | E2B (isolated sandbox) |
| Visualization | Matplotlib |

## Installation

### Prerequisites

- Python 3.12+
- Node.js + npm
- PostgreSQL
- API accounts: [Google AI Studio](https://aistudio.google.com) (Gemini), [E2B](https://e2b.dev), [Cloudinary](https://cloudinary.com)

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file inside `backend/`:

```env
GEMINI_API_KEY=your_key
E2B_API_KEY=your_key
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_key
CLOUDINARY_API_SECRET=your_secret
DATABASE_URL=postgresql://postgres:password@localhost:5432/financial_ai_agent
```

Create the PostgreSQL database (via pgAdmin or psql):

```sql
CREATE DATABASE financial_ai_agent;
```

Enable PDF storage on Cloudinary: in the Cloudinary dashboard → Settings → Security → enable "Allow delivery of PDF and ZIP files".

Start the server:

```bash
python app.py
```

The backend runs on `http://localhost:5000`. PostgreSQL tables are created automatically on first run.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on `http://localhost:5173`.

