# modules/processing/__init__.py
"""
Módulo 2: Document Processing & Indexing
Procesamiento avanzado y almacenamiento vectorial
"""

from .chunking import (
    ChunkingStrategy,
    AdaptiveChunker,
    create_chunker,
    optimal_chunk_size_for_model
)

from .embeddings import (
    EmbeddingGenerator,
    HybridEmbeddingGenerator,
    create_embedding_generator,
    get_multilingual_models,
    recommend_model_for_language
)

from .vector_store import (
    VectorStoreManager,
    create_vector_store,
    recommend_backend
)

from .index_builder import (
    IndexBuilder,
    create_index_builder,
    build_complete_pipeline
)

from .metadata_index import (
    MetadataIndex,
    create_metadata_index,
    hybrid_search
)

__all__ = [
    # Chunking
    'ChunkingStrategy',
    'AdaptiveChunker',
    'create_chunker',
    'optimal_chunk_size_for_model',
    
    # Embeddings
    'EmbeddingGenerator',
    'HybridEmbeddingGenerator',
    'create_embedding_generator',
    'get_multilingual_models',
    'recommend_model_for_language',
    
    # Vector Store
    'VectorStoreManager',
    'create_vector_store',
    'recommend_backend',
    
    # Index Builder
    'IndexBuilder',
    'create_index_builder',
    'build_complete_pipeline',
    
    # Metadata Index
    'MetadataIndex',
    'create_metadata_index',
    'hybrid_search'
]

__version__ = '2.0.0'
