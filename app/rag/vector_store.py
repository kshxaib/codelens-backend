import os
from qdrant_client import QdrantClient, models


# QDRANT CLIENT
client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))


COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "codelens_code")


# CREATE COLLECTION
def create_collection():
    collections = client.get_collections()

    exists = False

    for collection in collections.collections:
        if collection.name == COLLECTION_NAME:
            exists = True
            break

    if not exists:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE,
        ),
    )


# Store chunks into vectorDB with metadata and vector embedding
def store_chunks(chunks):
    points = []

    for chunk in chunks:
        # Append chunks to the points list
        points.append(
            models.PointStruct(
                id=chunk["id"],
                vector=chunk["embedding"],
                payload={
                    "repository_id": chunk["repository_id"],
                    "file_id": chunk["file_id"],
                    "file_path": chunk["file_path"],
                    "language": chunk["language"],
                    "start_line": chunk["start_line"],
                    "end_line": chunk["end_line"],
                    "content": chunk["content"],
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )



def search_chunks(query_embedding, repository_id: int, limit: int = 5):
    results = client.query_points(
        collection_name=COLLECTION_NAME,

        # Question ka embedding
        query=query_embedding,

        # Sirf selected repository ke chunks search karo
        query_filter=models.Filter(
            must=[
                models.FieldCondition(key="repository_id",
                    match=models.MatchValue(
                        value=repository_id
                    ),
                )
            ]
        ),

        # Top 5 results
        limit=limit,

        # Metadata + content return karo
        with_payload=True,
    )

    return results.points