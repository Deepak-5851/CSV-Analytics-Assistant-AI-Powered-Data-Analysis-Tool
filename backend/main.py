"""
main.py
-------
FastAPI application entry point for the Intelligent CSV Analytics Assistant.

Endpoints:
  POST /upload          -> upload a CSV file, build RAG index, return dataset info
  GET  /dataset-info    -> get info about the currently loaded dataset
  GET  /statistics      -> get statistical summary of numeric columns
  POST /query           -> ask a natural-language question about the dataset
  POST /filter          -> filter rows by a simple condition
  POST /aggregate       -> group-by aggregation
  GET  /summary         -> LLM-generated dataset summary
"""

import os
import shutil
import uuid
import re

from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_processor import DataProcessor
from rag_engine import RAGEngine
from llm_service import LLMService


load_dotenv()

app = FastAPI(
    title="Intelligent CSV Analytics Assistant",
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Upload directory
# ---------------------------------------------------------

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ---------------------------------------------------------
# Application state
# ---------------------------------------------------------

processor = DataProcessor()
rag_engine = RAGEngine()
llm_service = LLMService()


# ---------------------------------------------------------
# Request models
# ---------------------------------------------------------

class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class FilterRequest(BaseModel):
    column: str
    operator: str
    value: str


class AggregateRequest(BaseModel):
    group_by: str
    agg_column: str
    agg_func: str


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize text so that:
    Bank Balance
    bank_balance
    BANK-BALANCE

    are treated similarly.
    """
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def find_column_from_question(question: str):
    """
    Find a dataset column mentioned in the user's question.
    """

    if processor.df is None:
        return None

    question_normalized = normalize_text(question)

    # First: check whether the complete normalized column name
    # appears in the question.
    for column in processor.df.columns:
        column_normalized = normalize_text(column)

        if column_normalized and column_normalized in question_normalized:
            return column

    # Second: match individual words from the column name.
    question_words = set(
        re.findall(r"[a-zA-Z0-9]+", question.lower())
    )

    best_column = None
    best_score = 0

    for column in processor.df.columns:

        column_words = set(
            re.findall(r"[a-zA-Z0-9]+", str(column).lower())
        )

        if not column_words:
            continue

        score = len(question_words.intersection(column_words))

        if score > best_score:
            best_score = score
            best_column = column

    return best_column if best_score > 0 else None


def detect_aggregation(question: str):
    """
    Detect whether the user is asking for a mathematical
    aggregation over a column.
    """

    q = question.lower()

    if any(word in q for word in [
        "average",
        "avg",
        "mean"
    ]):
        return "mean"

    if any(word in q for word in [
        "sum",
        "total"
    ]):
        return "sum"

    if any(word in q for word in [
        "maximum",
        "max",
        "highest",
        "largest"
    ]):
        return "max"

    if any(word in q for word in [
        "minimum",
        "min",
        "lowest",
        "smallest"
    ]):
        return "min"

    if "median" in q:
        return "median"

    if any(word in q for word in [
        "count",
        "number of",
        "how many"
    ]):
        return "count"

    return None


def calculate_direct_answer(question: str):
    """
    Calculate numeric aggregation directly from the COMPLETE
    dataset instead of using only RAG-retrieved rows.

    Returns None when the question is not a simple aggregation.
    """

    if processor.df is None:
        return None

    agg_func = detect_aggregation(question)

    if agg_func is None:
        return None

    column = find_column_from_question(question)

    if column is None:
        return None

    df = processor.df

    # Count does not require a numeric column.
    if agg_func == "count":
        result = df[column].count()

        return (
            f"The number of non-empty values in "
            f"'{column}' is {result:,}."
        )

    # Convert the selected column to numeric.
    numeric_values = (
        df[column]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.strip()
    )

    numeric_values = __import__("pandas").to_numeric(
        numeric_values,
        errors="coerce"
    ).dropna()

    if numeric_values.empty:
        return None

    if agg_func == "mean":
        result = numeric_values.mean()
        return f"The average {column} is {result:,.2f}."

    if agg_func == "sum":
        result = numeric_values.sum()
        return f"The total {column} is {result:,.2f}."

    if agg_func == "max":
        result = numeric_values.max()
        return f"The maximum {column} is {result:,.2f}."

    if agg_func == "min":
        result = numeric_values.min()
        return f"The minimum {column} is {result:,.2f}."

    if agg_func == "median":
        result = numeric_values.median()
        return f"The median {column} is {result:,.2f}."

    return None


# ---------------------------------------------------------
# Root
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Intelligent CSV Analytics Assistant API is running."
    }


# ---------------------------------------------------------
# Upload CSV
# ---------------------------------------------------------

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    session_id = uuid.uuid4().hex[:8]

    filepath = os.path.join(
        UPLOAD_DIR,
        f"{session_id}_{file.filename}"
    )

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        info = processor.load_csv(
            filepath,
            file.filename
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to parse CSV: {e}"
        )

    # Build RAG index
    chunks = processor.rows_to_text_chunks()

    rag_engine.build_index(
        chunks,
        session_id=session_id
    )

    return {
        "status": "success",
        "session_id": session_id,
        "dataset_info": info
    }


# ---------------------------------------------------------
# Dataset info
# ---------------------------------------------------------

@app.get("/dataset-info")
def dataset_info():

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    return processor.get_dataset_info()


# ---------------------------------------------------------
# Statistics
# ---------------------------------------------------------

@app.get("/statistics")
def statistics():

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    return processor.get_statistical_summary()


# ---------------------------------------------------------
# Dataset summary
# ---------------------------------------------------------

@app.get("/summary")
def summary():

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    schema_text = processor.dataset_schema_text()

    stats = processor.get_statistical_summary()

    stats_text = str(stats)

    result = llm_service.summarize_dataset(
        schema_text,
        stats_text
    )

    return {
        "summary": result
    }


# ---------------------------------------------------------
# Query
# ---------------------------------------------------------

@app.post("/query")
def query(request: QueryRequest):

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    # -----------------------------------------------------
    # STEP 1:
    # Try direct Pandas calculation first.
    #
    # Example:
    # "What is the average bank balance?"
    #
    # This uses ALL rows in the CSV.
    # -----------------------------------------------------

    direct_answer = calculate_direct_answer(
        request.question
    )

    if direct_answer is not None:

        return {
            "question": request.question,
            "answer": direct_answer,
            "retrieved_context": [],
            "calculation": "Calculated directly from the complete dataset."
        }

    # -----------------------------------------------------
    # STEP 2:
    # For normal questions use RAG + Ollama.
    # -----------------------------------------------------

    schema_text = processor.dataset_schema_text()

    stats = processor.get_statistical_summary()

    stats_text = str(stats)

    retrieved_chunks = rag_engine.retrieve(
        request.question,
        top_k=request.top_k
    )

    answer = llm_service.answer_query(
        question=request.question,
        schema_text=schema_text,
        retrieved_chunks=retrieved_chunks,
        stats_context=stats_text,
    )

    return {
        "question": request.question,
        "answer": answer,
        "retrieved_context": retrieved_chunks,
    }


# ---------------------------------------------------------
# Filter
# ---------------------------------------------------------

@app.post("/filter")
def filter_rows(request: FilterRequest):

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    try:

        value = request.value

        try:
            value = (
                float(value)
                if "." in value
                else int(value)
            )

        except ValueError:
            pass

        result_df = processor.filter_rows(
            request.column,
            request.operator,
            value
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "row_count": len(result_df),
        "rows": result_df.head(100)
        .fillna("")
        .to_dict(orient="records")
    }


# ---------------------------------------------------------
# Aggregate
# ---------------------------------------------------------

@app.post("/aggregate")
def aggregate(request: AggregateRequest):

    if processor.df is None:
        raise HTTPException(
            status_code=404,
            detail="No dataset uploaded yet."
        )

    try:

        result_df = processor.aggregate(
            request.group_by,
            request.agg_column,
            request.agg_func
        )

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "rows": result_df
        .fillna("")
        .to_dict(orient="records")
    }


# ---------------------------------------------------------
# Run directly
# ---------------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )