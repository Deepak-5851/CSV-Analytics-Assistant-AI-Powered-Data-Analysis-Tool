"""
llm_service.py
---------------
Uses a local Ollama model instead of the Anthropic Claude API.
"""

import ollama


MODEL_NAME = "llama3.2:3b"


SYSTEM_PROMPT = """You are a concise CSV data analytics assistant.

Answer the user's question directly and briefly.

Rules:
- Give the answer first.
- For simple calculations, provide only the final result and a very short explanation.
- Do not list all retrieved rows unless specifically asked.
- Do not show unnecessary calculation steps.
- Keep answers to 1-3 sentences whenever possible.
- Use exact numbers from the provided data.
- Never guess or fabricate information.
"""


class LLMService:

    def __init__(self):
        self.model = MODEL_NAME

    def answer_query(
        self,
        question: str,
        schema_text: str,
        retrieved_chunks: list[str],
        stats_context: str = "",
    ) -> str:

        context_block = "\n".join(
            f"- {c}" for c in retrieved_chunks
        ) or "No directly matching rows found."

        user_message = f"""Dataset schema:
{schema_text}

Retrieved relevant rows (via RAG):
{context_block}

{f"Precomputed statistics:\n{stats_context}\n" if stats_context else ""}

User question:
{question}

Answer the user's question using only the information provided above.
"""

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            options={
                "temperature": 0.2,
                "num_predict": 150,
            },
        )

        return response["message"]["content"].strip()

    def summarize_dataset(
        self,
        schema_text: str,
        stats_context: str,
    ) -> str:

        user_message = f"""Dataset schema:
{schema_text}

Statistical summary:
{stats_context}

Write a concise, human-readable summary in 3-5 sentences describing
what this dataset contains and any notable patterns visible in the statistics.
"""

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            options={
                "temperature": 0.2,
                "num_predict": 150,
            },
        )

        return response["message"]["content"].strip()