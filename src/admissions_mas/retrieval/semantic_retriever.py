"""Sentence-Transformer embeddings and Weaviate hybrid-search adapter."""

from __future__ import annotations

import os
import uuid
from typing import Any

from ..domain.models import Evidence, Source
from ..infrastructure.text import stable_id


class SemanticRetriever:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.model_name = os.getenv("EMBEDDING_MODEL_NAME", "bkai-foundation-models/vietnamese-bi-encoder")
        self.weaviate_url = os.getenv("WEAVIATE_URL", "")
        self.weaviate_api_key = os.getenv("WEAVIATE_API_KEY", "")
        self.collection_name = os.getenv("WEAVIATE_COLLECTION", "AdmissionsEvidence")
        self.hybrid_alpha = float(os.getenv("WEAVIATE_HYBRID_ALPHA", "0.5"))
        self._model = None
        self._client = None

    @property
    def configured(self) -> bool:
        placeholders = ("your-", "example", "changeme")
        values = (self.weaviate_url.strip().lower(), self.weaviate_api_key.strip().lower())
        return all(values) and not any(marker in value for value in values for marker in placeholders)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def _connect(self):
        if self._client is not None:
            return self._client
        import weaviate
        from weaviate.classes.init import Auth
        self._client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.weaviate_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
        )
        return self._client

    def _collection(self):
        from weaviate.classes.config import Configure, DataType, Property
        client = self._connect()
        if client.collections.exists(self.collection_name):
            return client.collections.use(self.collection_name)
        properties = [
            Property(name="source_id", data_type=DataType.TEXT),
            Property(name="source_title", data_type=DataType.TEXT),
            Property(name="source_uri", data_type=DataType.TEXT),
            Property(name="source_type", data_type=DataType.TEXT),
            Property(name="authority", data_type=DataType.TEXT),
            Property(name="trust_score", data_type=DataType.NUMBER),
            Property(name="locator", data_type=DataType.TEXT),
            Property(name="text", data_type=DataType.TEXT),
        ]
        try:
            return client.collections.create(
                name=self.collection_name,
                vectorizer_config=Configure.Vectorizer.none(),
                properties=properties,
            )
        except TypeError:
            return client.collections.create(
                name=self.collection_name,
                vector_config=Configure.Vectors.self_provided(),
                properties=properties,
            )

    def _properties_for_upload(self, document: dict[str, str]) -> dict[str, Any]:
        source = self.knowledge_base.sources[document["source_id"]]
        return {
            "source_id": source.source_id,
            "source_title": source.title,
            "source_uri": source.uri,
            "source_type": source.source_type,
            "authority": source.authority,
            "trust_score": source.trust_score,
            "locator": document["locator"],
            "text": document["text"],
        }

    def index(self, documents: list[dict[str, str]]) -> int:
        """Embed and upsert regex chunks into Weaviate."""
        if not self.configured or not documents:
            return 0
        collection = self._collection()
        model = self._load_model()
        texts = [document["text"] for document in documents]
        vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        with collection.batch.fixed_size(batch_size=64) as batch:
            for document, vector in zip(documents, vectors):
                object_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document['source_id']}:{document['locator']}"))
                batch.add_object(
                    properties=self._properties_for_upload(document),
                    vector=vector.tolist(),
                    uuid=object_id,
                )
        return len(documents)

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
        """Run Weaviate hybrid search: BM25 query + supplied embedding vector."""
        if not self.configured:
            return []
        collection = self._collection()
        vector = self._load_model().encode(query, normalize_embeddings=True).tolist()
        from weaviate.classes.query import MetadataQuery
        response = collection.query.hybrid(
            query=query,
            vector=vector,
            alpha=self.hybrid_alpha,
            limit=limit,
            return_metadata=MetadataQuery(score=True, explain_score=True),
        )
        results: list[Evidence] = []
        for index, item in enumerate(response.objects, 1):
            properties: dict[str, Any] = item.properties
            source = self._source_from_properties(properties)
            relevance = self._relevance(item)
            locator = str(properties.get("locator") or "chunk")
            results.append(Evidence(
                evidence_id=f"hyb_{index:03d}_{stable_id('ev', source.source_id + locator)[-8:]}",
                source_id=source.source_id,
                quote=str(properties.get("text") or ""),
                locator=locator,
                relevance_score=relevance,
                source_trust_score=source.trust_score,
                query=query,
                retrieval_method=f"weaviate_hybrid:{self.model_name}:alpha={self.hybrid_alpha}",
                source_check_passed=source.authority in {"approved_local", "approved_external"} and source.trust_score >= 0.7,
                source_title=source.title,
                source_uri=source.uri,
            ))
        return results

    def _source_from_properties(self, properties: dict[str, Any]) -> Source:
        source_id = str(properties.get("source_id") or stable_id("src", str(properties.get("source_uri") or "")))
        source = self.knowledge_base.sources.get(source_id)
        if source:
            return source
        source = Source(
            source_id=source_id,
            title=str(properties.get("source_title") or source_id),
            uri=str(properties.get("source_uri") or ""),
            source_type=str(properties.get("source_type") or "weaviate_document"),
            trust_score=float(properties.get("trust_score") or 0.7),
            authority=str(properties.get("authority") or "approved_local"),
        )
        self.knowledge_base.sources[source_id] = source
        return source

    @staticmethod
    def _relevance(item) -> float:
        metadata = getattr(item, "metadata", None)
        raw_score = getattr(metadata, "score", None)
        try:
            if raw_score is not None:
                return round(max(0.0, min(1.0, float(raw_score))), 3)
        except (TypeError, ValueError):
            pass
        return 0.5
