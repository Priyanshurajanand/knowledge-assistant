# 🌟 Enterprise AI Knowledge Assistant

The **Enterprise AI Knowledge Assistant** is a production-grade, secure Retrieval-Augmented Generation (RAG) platform. It allows organizations to upload private documents (PDFs, Word files, and text), securely process and store them, and engage in high-fidelity conversations with citation references, using advanced LLMs like Groq, OpenAI, Gemini, and Claude.

---

## ⚙️ Core Architecture & Retrieval Strategy

The system is designed with a **Hybrid Retrieval Engine** to achieve high accuracy and relevance by combining semantic vectors and lexical text search.

```mermaid
graph TD
    User["User Client (Angular 19)"] <-->|REST APIs / JWT| BE["FastAPI Backend Server"]
    
    subgraph Storage & Retrieval Layer
        BE <-->|PostgreSQL asyncpg| DB[("PostgreSQL Database")]
        BE <-->|Qdrant Client| QDR[("Qdrant Vector DB")]
        BE --->|SentenceTransformers| LocalEmbed["Local Embedding Generator (all-MiniLM-L6-v2)"]
    end
    
    subgraph Multi-LLM Routing
        BE <-->|Groq API| Groq["Groq Llama 3.3"]
        BE <-->|OpenAI API| OpenAI["OpenAI GPT-4o"]
        BE <-->|Gemini API| Gemini["Google Gemini 1.5"]
        BE <-->|Anthropic API| Claude["Claude 3.5 Sonnet"]
    end
    
    DB --- DB_Tables["Users & User Settings<br>Conversations & Messages<br>Documents & Chunk Metadata<br>System Audit Logs"]
```

### 1. Hybrid Search with Reciprocal Rank Fusion (RRF)
To provide the most relevant context to the LLM, the backend queries two separate indexing systems simultaneously:
*   **Semantic Search**: Generates vector representations of user queries locally using the `all-MiniLM-L6-v2` SentenceTransformer model (384 dimensions) or OpenAI's `text-embedding-3-small` model, and queries the **Qdrant Vector Database**.
*   **Keyword Search (FTS)**: Queries the **PostgreSQL** database using a Generalized Inverted Index (**GIN**) on the document chunks text with `to_tsvector('english', text)`.
*   **Rank Fusion**: The results from both searches are combined using **Reciprocal Rank Fusion (RRF)** (with parameters `RRF_K=60` and `TOP_K=5` context chunks), generating a unified, high-relevance rank score before forwarding to the LLM.

### 2. Secure Document Ingestion Pipeline
1.  **Ingestion**: Supports **PDF** (`pypdf`), **Word DOCX** (`python-docx`), and **TXT** files up to 15MB.
2.  **Chunking**: Splitting files into optimal chunks and extracting metadata (e.g. page numbers and file source).
3.  **Indexing**: Embedding generation is triggered, storing high-dimensional vectors in Qdrant and texts/metadata in PostgreSQL.

---

## ✨ Key Features

*   **Multi-LLM Integration**: Supports Groq (default), OpenAI, Anthropic, and Google Gemini.
*   **Automatic Provider Fallback & Migration**: Seamless migration of existing data/preferences from OpenAI to Groq on startup if credentials change.
*   **Citation & Grounding**: AI answers include interactive references indicating the source document, chunk index, and page number.
*   **Admin Panel**: Built-in user administration and security audit logs to track modifications.
*   **Premium Interface**: Dark/light mode theme support, custom SCSS variables, responsive dashboard with animations.

---

## 📂 Project Structure

```
knowledge-assistant/
├── backend/
│   ├── app/
│   │   ├── api/            # API Router and Endpoints (auth, chat, admin, docs)
│   │   ├── core/           # Security configurations, DB engine, Middlewares
│   │   ├── models/         # SQLAlchemy DB models (user, chat, document, audit)
│   │   ├── repositories/   # Data Access Layer (repositories)
│   │   ├── schemas/        # Pydantic schemas (Request/Response validation)
│   │   └── services/       # Core business logic (RAG, embedding, vector, parser)
│   ├── migrations/         # Alembic database migrations
│   ├── storage/            # Local documents temporary file storage
│   ├── create_db.py        # Helper script to create local PostgreSQL database
│   ├── requirements.txt    # Backend Python dependencies
│   └── alembic.ini         # Alembic config
└── frontend/
    ├── src/
    │   ├── app/
    │   │   ├── core/       # Guards, Interceptors, Services
    │   │   ├── features/   # Auth, Dashboard, Admin views
    │   │   └── shared/     # Shared Components, Pipes, UI Modules
    │   └── styles/         # Custom SCSS Variables & Styling
    ├── angular.json        # Angular workspace configuration
    └── package.json        # Frontend scripts and dependencies
```

---

## 🛠️ Prerequisites

Before running the application, make sure you have:
*   [Python 3.10+](https://www.python.org/downloads/)
*   [Node.js 18+](https://nodejs.org/) (with npm)
*   [PostgreSQL 14+](https://www.postgresql.org/download/)
*   [Qdrant Database](https://qdrant.tech/documentation/quick-start/) (Local docker instance or Qdrant Cloud cluster)

---

## 🚀 Getting Started

### 1. Clone the Repository

Clone the project repository to your local machine and navigate into the root directory:

```bash
git clone https://github.com/Priyanshurajanand/knowledge-assistant.git
cd knowledge-assistant
```

### 2. Setup the Backend

To configure and start the backend service:

1.  Navigate to the `backend` directory:
    ```bash
    cd backend
    ```

2.  Create and activate a virtual environment:
    ```bash
    python -m venv virtual-backend
    # On Windows (PowerShell):
    .\virtual-backend\Scripts\Activate.ps1
    # On macOS/Linux:
    source virtual-backend/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Configure the Environment Variables:
    Copy `.env.example` to `.env` and fill in your connection details and API keys:
    ```bash
    copy .env.example .env
    ```

5.  Create the Database:
    Ensure your PostgreSQL server is running, then execute the creation script:
    ```bash
    python create_db.py
    ```

6.  Apply Database Migrations:
    ```bash
    alembic upgrade head
    ```

7.  Start the FastAPI Server:
    ```bash
    uvicorn app.main:app --reload
    ```
    *The API will be available at [http://localhost:8000](http://localhost:8000). You can access the interactive OpenAPI docs at [http://localhost:8000/docs](http://localhost:8000/docs).*

#### 🔑 Seeding / Default Credentials
On the first run, the database is automatically seeded with two test accounts:
*   **Administrator**:
    *   Email: `admin@company.com`
    *   Password: `adminpassword123`
*   **Standard User**:
    *   Email: `user@company.com`
    *   Password: `userpassword123`

---

### 3. Setup the Frontend

To configure and start the Angular frontend:

1.  Open a **new, separate terminal window** (keep the backend server running in the first terminal).
2.  Navigate to the `frontend` directory:
    ```bash
    cd frontend
    ```
3.  Install dependencies:
    ```bash
    npm install
    ```
4.  Start the Angular Development Server:
    ```bash
    npm start
    ```
    *The frontend will run at [http://localhost:4200](http://localhost:4200).*

---

### 💻 Running Backend and Frontend Simultaneously

For normal local development, you must run both the backend (FastAPI) and the frontend (Angular) concurrently:

*   **Terminal 1 (Backend)**: Keep `uvicorn app.main:app --reload` running in the `backend` environment.
*   **Terminal 2 (Frontend)**: Keep `npm start` running in the `frontend` directory.

The Angular frontend is pre-configured to communicate with the FastAPI backend on `http://localhost:8000`. Cross-Origin Resource Sharing (CORS) is enabled on the backend to allow requests from the frontend at `http://localhost:4200`.

---

## 🔒 Configuration (Environment Variables)

Configured variables in the `backend/.env` file:

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Run mode (`development` / `production`) | `development` |
| `CORS_ORIGINS` | Comma-separated list of allowed origins | `http://localhost:4200,http://127.0.0.1:4200,http://localhost` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://postgres:postgres@localhost:5432/knowledge_assistant` |
| `JWT_SECRET` | Secret key for JWT signing | `supersecretkeyreplaceinproduction` |
| `QDRANT_URL` | Qdrant Database endpoint | `http://localhost:6333` |
| `QDRANT_API_KEY` | API Key for Qdrant Cloud (if applicable) | `""` |
| `GROQ_API_KEY` | API Key for Groq Cloud | `""` |
| `OPENAI_API_KEY` | API Key for OpenAI | `""` |
| `GEMINI_API_KEY` | API Key for Google Gemini | `""` |
| `ANTHROPIC_API_KEY` | API Key for Claude | `""` |
| `UPLOAD_DIR` | Path to upload physical files | `storage/documents` |
| `MAX_UPLOAD_SIZE_BYTES`| Maximum allowed document file size | `15728640` (15MB) |


---

