# Intelligent CSV Analytics Assistant using LLM and RAG

An AI-powered web application that lets users analyze CSV datasets through
natural-language queries — no SQL or programming required.

**Team:** B. Aswin, M. Deepak, K. Abishek

## Tech Stack

- **Frontend:** React.js, Axios, Recharts
- **Backend:** Python, FastAPI
- **Data Processing:** Pandas, NumPy
- **LLM:** Anthropic Claude API
- **RAG:** Sentence-Transformers embeddings + ChromaDB vector store

## Project Structure

```
csv-analytics-assistant/
├── backend/
│   ├── main.py            # FastAPI app & routes
│   ├── data_processor.py  # Pandas-based analytics
│   ├── rag_engine.py      # Embeddings + ChromaDB retrieval
│   ├── llm_service.py     # Claude API integration
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.js
    │   ├── api.js
    │   ├── index.js
    │   ├── index.css
    │   └── components/
    │       ├── FileUpload.js
    │       ├── DataTable.js
    │       ├── ChatInterface.js
    │       └── Visualization.js
    ├── public/index.html
    └── package.json
```

## Setup Instructions

### 1. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Add your Anthropic API key
cp .env.example .env
# then edit .env and paste your key

uvicorn main:app --reload
```

The backend will run at `http://localhost:8000`.

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend will run at `http://localhost:3000` and calls the backend
at `http://localhost:8000` by default (configurable via `REACT_APP_API_URL`
in a `.env` file inside `frontend/`).

## How It Works

1. **Upload:** User uploads a CSV file through the React interface.
2. **Processing:** FastAPI backend loads the file into a Pandas DataFrame,
   computes schema info and statistics, and converts rows into text chunks.
3. **Indexing:** Text chunks are embedded using a Sentence-Transformers model
   and stored in a ChromaDB vector collection.
4. **Querying:** When a user asks a question, the backend retrieves the most
   relevant chunks from ChromaDB (RAG) and sends them, along with the dataset
   schema, to Claude (Anthropic API) to generate a contextual answer.
3. **Response:** The answer, along with supporting data/visualizations, is
   displayed back in the React UI.

## API Endpoints

| Method | Endpoint         | Description                              |
|--------|------------------|-------------------------------------------|
| POST   | `/upload`        | Upload CSV, build RAG index               |
| GET    | `/dataset-info`  | Get dataset schema/preview                |
| GET    | `/statistics`    | Get numeric column statistics             |
| GET    | `/summary`       | Get an AI-generated dataset summary       |
| POST   | `/query`         | Ask a natural-language question           |
| POST   | `/filter`        | Filter rows by column/operator/value      |
| POST   | `/aggregate`     | Group-by aggregation on a column          |

## Notes

- This is a single-session demo implementation (one dataset in memory at a
  time). For multi-user production use, add session-keyed state or a
  database-backed store.
- The embedding model (`all-MiniLM-L6-v2`) runs locally/free — no external
  embedding API is required.
