"""
data_processor.py
------------------
Handles all deterministic pandas/numpy based operations on the uploaded
CSV dataset: loading, cleaning, summarization, filtering, and aggregation.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class DataProcessor:
    """Wraps a pandas DataFrame and exposes analytics helper methods."""

    def __init__(self):
        self.df: pd.DataFrame | None = None
        self.filename: str | None = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_csv(self, filepath: str, filename: str) -> Dict[str, Any]:
        """Load a CSV file into a DataFrame and return basic dataset info."""
        self.df = pd.read_csv(filepath)
        self.filename = filename

        # Basic cleaning: strip whitespace from column names
        self.df.columns = [c.strip() for c in self.df.columns]

        return self.get_dataset_info()

    # ------------------------------------------------------------------
    # Dataset info / summary
    # ------------------------------------------------------------------
    def get_dataset_info(self) -> Dict[str, Any]:
        if self.df is None:
            raise ValueError("No dataset loaded.")

        df = self.df
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing = df.isnull().sum().to_dict()

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()

        return {
            "filename": self.filename,
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": df.columns.tolist(),
            "dtypes": dtypes,
            "missing_values": {k: int(v) for k, v in missing.items()},
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "preview": df.head(5).fillna("").to_dict(orient="records"),
        }

    def get_statistical_summary(self) -> Dict[str, Any]:
        """Return describe() stats for numeric columns."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        numeric_df = self.df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return {}
        summary = numeric_df.describe().to_dict()
        # round for readability
        for col, stats in summary.items():
            summary[col] = {k: round(v, 3) if isinstance(v, float) else v for k, v in stats.items()}
        return summary

    # ------------------------------------------------------------------
    # Filtering / aggregation helpers (used by the LLM tool-calling layer)
    # ------------------------------------------------------------------
    def filter_rows(self, column: str, operator: str, value) -> pd.DataFrame:
        """Filter rows based on a simple column/operator/value condition."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found.")

        col = self.df[column]
        ops = {
            "==": lambda c, v: c == v,
            "!=": lambda c, v: c != v,
            ">": lambda c, v: c > v,
            "<": lambda c, v: c < v,
            ">=": lambda c, v: c >= v,
            "<=": lambda c, v: c <= v,
            "contains": lambda c, v: c.astype(str).str.contains(str(v), case=False, na=False),
        }
        if operator not in ops:
            raise ValueError(f"Unsupported operator '{operator}'.")
        return self.df[ops[operator](col, value)]

    def aggregate(self, group_by: str, agg_column: str, agg_func: str) -> pd.DataFrame:
        """Group by a column and aggregate another column."""
        if self.df is None:
            raise ValueError("No dataset loaded.")
        valid_funcs = ["sum", "mean", "count", "min", "max", "median", "std"]
        if agg_func not in valid_funcs:
            raise ValueError(f"Unsupported aggregation function '{agg_func}'.")
        return self.df.groupby(group_by)[agg_column].agg(agg_func).reset_index()

    def get_column_values_sample(self, column: str, n: int = 10):
        if self.df is None or column not in self.df.columns:
            return []
        return self.df[column].dropna().unique()[:n].tolist()

    # ------------------------------------------------------------------
    # Row-level text chunks for RAG embedding
    # ------------------------------------------------------------------
    def rows_to_text_chunks(self, max_rows: int = 2000) -> list[str]:
        """
        Convert dataframe rows into natural-language text chunks so they
        can be embedded and retrieved semantically via the vector store.
        """
        if self.df is None:
            raise ValueError("No dataset loaded.")

        df = self.df.head(max_rows)
        chunks = []
        for idx, row in df.iterrows():
            parts = [f"{col}: {row[col]}" for col in df.columns]
            chunk = f"Row {idx}: " + ", ".join(parts)
            chunks.append(chunk)
        return chunks

    def dataset_schema_text(self) -> str:
        """A textual description of the dataset schema, used as RAG context."""
        info = self.get_dataset_info()
        lines = [
            f"Dataset '{info['filename']}' has {info['rows']} rows and {info['columns']} columns.",
            f"Columns: {', '.join(info['column_names'])}.",
            f"Numeric columns: {', '.join(info['numeric_columns']) or 'none'}.",
            f"Categorical columns: {', '.join(info['categorical_columns']) or 'none'}.",
        ]
        return "\n".join(lines)
