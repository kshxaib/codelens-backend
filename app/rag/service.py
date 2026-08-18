from openai import OpenAI

from app.rag.embeddings import create_embedding
from app.rag.vector_store import search_chunks


client = OpenAI()


def build_context(results):
    context_parts = []

    for result in results:
        payload = result.payload
        context_parts.append(
            f"""
                File: {payload["file_path"]}
                Lines: {payload["start_line"]}-{payload["end_line"]}

                {payload["content"]}
            """
        )

    return "\n\n---\n\n".join(
        context_parts
    )


def ask_repository( question: str, repository_id: int):
    # 1. Question → embedding
    query_embedding = create_embedding(question)

    # 2. Search relevant code
    results = search_chunks(
        query_embedding=query_embedding,
        repository_id=repository_id,
        limit=5,
    )


    if not results:
        return {
            "answer": "I could not find relevant code in this repository.",
            "sources": [],
        }


    # 3. Build context
    context = build_context(results)


    # 4. Ask OpenAI
    response = client.responses.create(
        model="gpt-4o",

        input=[
            {
                "role": "system",
                "content": (
                    "You are CodeLens, a codebase "
                    "intelligence assistant. "
                    "Answer only using the provided "
                    "repository context. "
                    "If the context does not contain "
                    "the answer, say so. "
                    "Mention relevant file paths and "
                    "line ranges when possible."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Repository context:\n\n"
                    f"{context}\n\n"
                    f"Question:\n{question}"
                ),
            },
        ],
    )


    # ========================================================
    # 5. Return answer + sources
    # ========================================================

    return {
        "answer": response.output_text,

        "sources": [
            {
                "file_path":
                    result.payload["file_path"],

                "start_line":
                    result.payload["start_line"],

                "end_line":
                    result.payload["end_line"],

                "score":
                    result.score,
            }
            for result in results
        ],
    }