import os
from openai import OpenAI

from app.rag.embeddings import create_embedding
from app.rag.vector_store import search_chunks


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


# Qdrant se aaye relevant code chunks ko ek single text/context mein combine karna
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

    return "\n\n---\n\n".join(context_parts)


# Gives the response in non-streaming manner
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
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
 
        messages=[
            {
                "role": "system",
                "content": (
                    "You are CodeLens, a codebase intelligence assistant.\n\n"
                    "Answer only using the provided repository context. \n\n"
                    "If the context does not contain enough information to answer the question, say that clearly instead of guessing.\n\n"
                    "When possible, mention the relevant file paths and line ranges."
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

    # 5. Return answer + sources
    sources = []

    for result in results:
        sources.append({
            "file_path": result.payload["file_path"],
            "start_line": result.payload["start_line"],
            "end_line": result.payload["end_line"],
            "score": result.score,
        })

    return {
        "answer": response.choices[0].message.content,
        "sources": sources,
    }


# Gives the response in streaming manner
def stream_repository_answer(question: str, repository_id: int):
    
    # 1. QUESTION → EMBEDDING
    query_embedding = create_embedding(question)

    # 2. QDRANT SEARCH
    results = search_chunks(
        query_embedding=query_embedding,
        repository_id=repository_id,
        limit=5,
    )

    # 3. NO RESULTS
    if not results:
        yield {
            "type": "error",
            "message": "I could not find relevant code in this repository.",
        }

        return

    # 4. BUILD CONTEXT
    context = build_context(results)

    # 5. OPENAI STREAM
    stream = client.chat.completions.create(
        model="openai/gpt-oss-20b:free",
        stream=True,
        messages=[
            { 
                "role": "system",
                "content": (
                    "You are CodeLens, a codebase intelligence assistant.\n\n"
                    "Answer only using the provided repository context. \n\n"
                    "If the context does not contain enough information to answer the question, say that clearly instead of guessing.\n\n"
                    "When possible, mention the relevant file paths and line ranges."
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

    # 6. STREAM TEXT
    # OpenRouter Chat Completions streamed text is inside: chunk.choices[0].delta.content
    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        if delta.content:
            yield {
                "type": "text",
                "text": delta.content,
            }

    # 7. SEND SOURCES AT END
    sources = []
    for result in results:
        payload = result.payload
        sources.append({
            "file_path": payload["file_path"],
            "start_line": payload["start_line"],
            "end_line":payload["end_line"],
            "score":result.score,
        })


    yield {
        "type": "sources",
        "sources": sources,
    }


    