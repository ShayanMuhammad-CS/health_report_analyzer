# DOCUS AI

DOCUS AI is a clinical-grade AI assistant for blood report analysis. It reads a blood report PDF, runs a comprehensive analysis using multiple large language models, and provides context-aware follow-up chat powered by retrieval-augmented generation. The system is designed to be accurate, clinically structured, and easy to use for patients and health-conscious individuals who want to understand their lab results without needing to book a doctor appointment for basic interpretation.

---

## What It Does

The application accepts a blood report in PDF format or lets the user test with a sample report. It extracts all text from the report using pdfplumber, sends it to a multi-model AI pipeline that selects the best available language model through an automated fallback chain, and returns a structured medical analysis covering all major biomarkers.

Once the report is analyzed, the user can engage in a full follow-up conversation with the AI. Every follow-up question is answered using RAG, meaning the AI retrieves the most relevant passages from the original report before generating a response. This prevents hallucination and keeps every answer grounded in the actual document.

The system maintains daily analysis limits, session history, and user accounts through Supabase. Users can create multiple sessions, switch between them, and all chat history is persisted so nothing is lost between visits.

---

## System Architecture

The backend is divided into four main layers.

The agent layer contains the AnalysisAgent, ChatAgent, and ModelManager. The AnalysisAgent handles rate limiting, in-context learning from previous analyses, and delegates to the ModelManager which tries Groq models in a priority order. The ChatAgent manages vector store creation and retrieval for RAG-powered chat.

The service layer provides a clean interface between the UI and the agents through AIService, which the UI never bypasses. This layer also manages caching of vector stores per session to avoid re-embedding on every message.

The auth layer uses Supabase for user authentication, session management, and persistent storage of chat sessions and messages. It includes a transparent fallback for Supabase rate limit errors during development.

The component layer is a set of independent Streamlit components for the sidebar, header, analysis form, auth pages, and footer. Each component is isolated and reusable.

---

## Technology Stack

The application is built on Streamlit for the UI, Supabase for user authentication and the database, and the Groq API for language model inference. Embeddings are generated using sentence-transformers with the all-MiniLM-L6-v2 model and indexed with FAISS for similarity search. PDF extraction runs on pdfplumber. The LangChain ecosystem is used for the RAG pipeline including text splitting, vector stores, and retrieval chains.

---

## Project Structure

```
hia/
  src/
    agents/          Model orchestration, rate limiting, RAG chat
    auth/            Supabase auth and session management
    components/      Streamlit UI components
    config/          App-wide constants and prompts
    services/        AIService facade
    utils/           Validators, PDF extraction utilities
    main.py          App entry point and routing
  .streamlit/
    config.toml      Theme and UI configuration
    secrets.toml     API keys (not committed to version control)
  requirements.txt
```

---

## Getting Started

Clone the repository and install dependencies.

```
pip install -r requirements.txt
```

Create a `.streamlit/secrets.toml` file inside the `hia` directory with the following keys.

```toml
GROQ_API_KEY = "your_groq_api_key"
SUPABASE_URL = "your_supabase_project_url"
SUPABASE_KEY = "your_supabase_anon_key"
```

Run the application from the `hia` directory.

```
python -m streamlit run src/main.py
```

---

## Database Setup

The application expects three tables in Supabase. A `users` table with columns `id`, `email`, `name`, and `created_at`. A `chat_sessions` table with `id`, `user_id`, `title`, `report_text`, `analysis_result`, and `created_at`. A `chat_messages` table with `id`, `session_id`, `role`, `content`, and `created_at`. Row-level security should be configured so that users can only access their own data.

---

## Configuration

The daily analysis limit, session timeout, and upload constraints can be adjusted in `src/config/app_config.py`. Model fallback priority and prompts are defined in `src/config/prompts.py` and `src/agents/model_manager.py`.

---

## Deployment

The application is deployable on Streamlit Community Cloud. Set all secrets from `secrets.toml` in the Streamlit Cloud secrets manager. The entry point is `src/main.py` and the repository root is the `hia` directory.

---

## Notes

The `secrets.toml` file is excluded from version control via `.gitignore` and must never be committed. The sentence transformer model is downloaded at startup and may take a moment on the first run. The Groq client initializes lazily through a cached Streamlit resource to avoid reloading the model on every page interaction.
