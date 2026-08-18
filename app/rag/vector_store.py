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