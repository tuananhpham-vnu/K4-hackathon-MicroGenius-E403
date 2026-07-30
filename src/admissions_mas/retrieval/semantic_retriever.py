"""Sentence-Transformer embeddings and Weaviate Cloud vector adapter."""

from __future__ import annotations

import os
import uuid
from typing import Any

from ..domain.models import Evidence
from ..infrastructure.text import stable_id


class SemanticRetriever:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "bkai-foundation-models/vietnamese-bi-encoder")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")
        self.collection_name = os.getenv("WEAVIATE_COLLECTION", "AdmissionsEvidence")
        self._model = None
        self._client = None

    @property
    def configured(self) -> bool:
        return bool(self.weaviate_url and self.weaviate_api_key)

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _connect(self):
        if self._client is not None:
            return self._client
        import weaviate
        from weaviate.auth import Auth
        self._client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.weaviate_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
        )
        return self._client

    def _collection(self):
        from weaviate.classes.config import Configure, DataType, Property
        client = self._connect()
        if not client.collections.exists(self.collection_name):
            return client.collections.create(
                name=self.collection_name,
                vector_config=Configure.Vectors.self_provided(),
                properties=[
                    Property(name="source_id", data_type=DataType.TEXT),
                    Property(name="locator", data_type=DataType.TEXT),
                    Property(name="text", data_type=DataType.TEXT),
                ],
            )
        return client.collections.use(self.collection_name)

    def index(self, documents: list[dict[str, str]]) -> int:
        if not self.configured:
            return 0
        collection = self._collection()
        model = self._load_model()
        texts = [document["text"] for document in documents]
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        with collection.batch.fixed_size(batch_size=64) as batch:
            for document, vector in zip(documents, vectors):
                object_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document['source_id']}:{document['locator']}"))
                batch.add_object(properties=document, vector=vector.tolist(), uuid=object_id)
        return len(documents)

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if not self.configured:
            return []
        collection = self._collection()
        model = self._load_model()
        vector = model.encode(query, normalize_embeddings=True).tolist()
        from weaviate.classes.query import MetadataQuery
        response = collection.query.near_vector(near_vector=vector, limit=limit, return_metadata=MetadataQuery(distance=True))
        results: list[Evidence] = []
        for index, item in enumerate(response.objects, 1):
            properties: dict[str, Any] = item.properties
            distance = float(getattr(item.metadata, "distance", 1.0) or 1.0)
            relevance = max(0.0, min(1.0, 1.0 - distance))
            source_id = str(properties["source_id"])
            source = self.knowledge_base.sources.get(source_id)
            if not source:
                continue
            results.append(Evidence(
                evidence_id=f"vec_{index:03d}_{stable_id('ev', source_id + str(properties['locator']))[-8:]}",
                source_id=source_id, quote=str(properties["text"]), locator=str(properties["locator"]),
                relevance_score=round(relevance, 3), source_trust_score=source.trust_score,
                query=query, retrieval_method=f"weaviate:{self.model_name}",
                source_check_passed=source.authority in {"approved_local", "approved_external"} and source.trust_score >= 0.7,
            ))
        return results
