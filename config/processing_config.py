# config/processing_config.py
"""
Configuración para el Módulo 2: Document Processing & Indexing
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from pathlib import Path


class ProcessingConfig(BaseSettings):
    """
    Configuración del procesamiento y indexing
    """
    
    # =================================================================
    # CHUNKING
    # =================================================================
    CHUNKING_STRATEGY: str = "sentence"  # sentence, semantic, sentence_window, fixed_size, recursive
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    
    # Semantic chunking
    SEMANTIC_BUFFER_SIZE: int = 1
    SEMANTIC_THRESHOLD: int = 95
    
    # Sentence window
    SENTENCE_WINDOW_SIZE: int = 3
    
    # =================================================================
    # EMBEDDINGS
    # =================================================================
    # Modelo: openai-small, openai-large, bge-large, bge-m3, e5-multilingual, etc.
    # EMBEDDING_MODEL: str = "openai-small"
    # EMBEDDING_BATCH_SIZE: int = 100
    # EMBEDDING_DIMENSIONS: int = 1536  # Se ajusta automáticamente según modelo
    
    # OpenAI
    # OPENAI_API_KEY: Optional[str] = None
    
    # HuggingFace (para modelos locales)
    HF_TOKEN: Optional[str] = None
    HF_CACHE_DIR: str = "models/embeddings"
    
    # =================================================================
    # VECTOR STORE
    # =================================================================
    VECTOR_STORE_BACKEND: str = "qdrant"  # qdrant, chroma, pinecone, faiss
    VECTOR_STORE_PATH: str = "data/vector_stores"
    COLLECTION_NAME: str = "rag_documents"
    
    # Qdrant
    QDRANT_URL: Optional[str] = None  # None = local, o URL cloud
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    
    # Pinecone
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_ENVIRONMENT: Optional[str] = None
    PINECONE_INDEX_NAME: Optional[str] = None
    
    # =================================================================
    # INDEX BUILDER
    # =================================================================
    INDEX_PERSIST_DIR: str = "data/indexes"
    INDEX_NAME: str = "main_index"
    
    # Retrieval
    SIMILARITY_TOP_K: int = 10
    RETRIEVAL_MODE: str = "default"  # default, mmr, diversity
    
    # =================================================================
    # METADATA INDEX
    # =================================================================
    METADATA_INDEX_PATH: str = "data/indexes/metadata"
    METADATA_FIELDS_TO_INDEX: str = "filename,file_type,department,category,language"
    
    # =================================================================
    # HYBRID SEARCH
    # =================================================================
    ENABLE_HYBRID_SEARCH: bool = True
    HYBRID_ALPHA: float = 0.5  # 0 = full keyword, 1 = full semantic
    
    # =================================================================
    # PERFORMANCE
    # =================================================================
    MAX_WORKERS_EMBEDDING: int = 4
    BATCH_SIZE_INDEXING: int = 100
    ENABLE_ASYNC_INDEXING: bool = False
    
    # =================================================================
    # QUALITY CONTROL
    # =================================================================
    MIN_CHUNK_LENGTH: int = 50
    MAX_CHUNK_LENGTH: int = 2000
    VALIDATE_EMBEDDINGS: bool = True
    
    # =================================================================
    # LOGGING
    # =================================================================
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/processing.log"
    
    # =================================================================
    # ENTORNO
    # =================================================================
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PROCESSING_",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Propiedades computadas
    @property
    def METADATA_FIELDS_LIST(self) -> List[str]:
        """Parsea METADATA_FIELDS_TO_INDEX a lista"""
        return [field.strip() for field in self.METADATA_FIELDS_TO_INDEX.split(",")]
    
    def get_vector_store_config(self) -> dict:
        """Obtiene configuración del vector store"""
        if self.VECTOR_STORE_BACKEND == "qdrant":
            config = {
                'backend': 'qdrant',
                'collection_name': self.COLLECTION_NAME,
                'persist_path': self.VECTOR_STORE_PATH,
                'dimension': self.EMBEDDING_DIMENSIONS
            }
            
            if self.QDRANT_URL:
                config['url'] = self.QDRANT_URL
                config['api_key'] = self.QDRANT_API_KEY
            
            return config
        
        elif self.VECTOR_STORE_BACKEND == "chroma":
            return {
                'backend': 'chroma',
                'collection_name': self.COLLECTION_NAME,
                'persist_path': self.VECTOR_STORE_PATH,
                'dimension': self.EMBEDDING_DIMENSIONS
            }
        
        elif self.VECTOR_STORE_BACKEND == "pinecone":
            return {
                'backend': 'pinecone',
                'api_key': self.PINECONE_API_KEY,
                'index_name': self.PINECONE_INDEX_NAME or self.COLLECTION_NAME,
                'dimension': self.EMBEDDING_DIMENSIONS
            }
        
        else:
            return {
                'backend': self.VECTOR_STORE_BACKEND,
                'dimension': self.EMBEDDING_DIMENSIONS
            }
    
    def get_embedding_config(self) -> dict:
        """Obtiene configuración de embeddings"""
        config = {
            'model_name': self.EMBEDDING_MODEL,
            'batch_size': self.EMBEDDING_BATCH_SIZE
        }
        
        if 'openai' in self.EMBEDDING_MODEL:
            config['api_key'] = self.OPENAI_API_KEY
        
        return config
    
    def get_chunking_config(self) -> dict:
        """Obtiene configuración de chunking"""
        return {
            'strategy': self.CHUNKING_STRATEGY,
            'chunk_size': self.CHUNK_SIZE,
            'chunk_overlap': self.CHUNK_OVERLAP,
            'buffer_size': self.SEMANTIC_BUFFER_SIZE,
            'threshold': self.SEMANTIC_THRESHOLD,
            'window_size': self.SENTENCE_WINDOW_SIZE
        }


# Instancia global
config = ProcessingConfig()


# Funciones helper
def setup_directories():
    """Crea los directorios necesarios"""
    directories = [
        config.VECTOR_STORE_PATH,
        config.INDEX_PERSIST_DIR,
        config.METADATA_INDEX_PATH,
        config.HF_CACHE_DIR,
        Path(config.LOG_FILE).parent
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directorios del Módulo 2 creados")


# Configuraciones por entorno
class DevelopmentConfig(ProcessingConfig):
    """Configuración desarrollo"""
    LOG_LEVEL: str = "DEBUG"
    DEBUG: bool = True
    EMBEDDING_BATCH_SIZE: int = 50
    CHUNK_SIZE: int = 256
    SIMILARITY_TOP_K: int = 5


class ProductionConfig(ProcessingConfig):
    """Configuración producción"""
    LOG_LEVEL: str = "WARNING"
    DEBUG: bool = False
    EMBEDDING_BATCH_SIZE: int = 200
    MAX_WORKERS_EMBEDDING: int = 8
    ENABLE_ASYNC_INDEXING: bool = True
    VALIDATE_EMBEDDINGS: bool = True


class TestingConfig(ProcessingConfig):
    """Configuración testing"""
    LOG_LEVEL: str = "DEBUG"
    CHUNK_SIZE: int = 128
    EMBEDDING_BATCH_SIZE: int = 10
    SIMILARITY_TOP_K: int = 3
    VECTOR_STORE_PATH: str = "tests/fixtures/vector_stores"
    INDEX_PERSIST_DIR: str = "tests/fixtures/indexes"


def get_config(environment: str = "development") -> ProcessingConfig:
    """
    Obtiene configuración según entorno
    
    Args:
        environment: 'development', 'testing', 'production'
        
    Returns:
        Configuración
    """
    configs = {
        'development': DevelopmentConfig(),
        'testing': TestingConfig(),
        'production': ProductionConfig()
    }
    
    return configs.get(environment.lower(), ProcessingConfig())


def validate_config():
    """Valida la configuración"""
    errors = []
    
    # Validar chunking
    if config.CHUNK_SIZE < 50:
        errors.append("CHUNK_SIZE debe ser >= 50")
    
    if config.CHUNK_OVERLAP >= config.CHUNK_SIZE:
        errors.append("CHUNK_OVERLAP debe ser < CHUNK_SIZE")
    
    # Validar embeddings
    if 'openai' in config.EMBEDDING_MODEL and not config.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY requerida para modelos OpenAI")
    
    if config.VECTOR_STORE_BACKEND == 'pinecone' and not config.PINECONE_API_KEY:
        errors.append("PINECONE_API_KEY requerida para Pinecone")
    
    # Validar similarity
    if config.SIMILARITY_TOP_K < 1:
        errors.append("SIMILARITY_TOP_K debe ser >= 1")
    
    if errors:
        raise ValueError(f"Errores de configuración:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Validar al cargar
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  ADVERTENCIA: {e}")
