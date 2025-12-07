# modules/processing/embeddings.py
"""
2.2 Embedding Generator
Generación de embeddings con múltiples modelos y proveedores
"""

from typing import List, Optional, Dict, Any
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.schema import BaseNode
import logging

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Gestor de generación de embeddings multilingües
    """
    
    SUPPORTED_MODELS = {
        # OpenAI
        'openai-small': {
            'provider': 'openai',
            'model': 'text-embedding-3-small',
            'dimensions': 1536,
            'max_tokens': 8191,
            'multilingual': True
        },
        'openai-large': {
            'provider': 'openai',
            'model': 'text-embedding-3-large',
            'dimensions': 3072,
            'max_tokens': 8191,
            'multilingual': True
        },
        'openai-ada': {
            'provider': 'openai',
            'model': 'text-embedding-ada-002',
            'dimensions': 1536,
            'max_tokens': 8191,
            'multilingual': True
        },
        
        # HuggingFace - BGE (BAAI General Embedding)
        'bge-large': {
            'provider': 'huggingface',
            'model': 'BAAI/bge-large-en-v1.5',
            'dimensions': 1024,
            'max_tokens': 512,
            'multilingual': False
        },
        'bge-small': {
            'provider': 'huggingface',
            'model': 'BAAI/bge-small-en-v1.5',
            'dimensions': 384,
            'max_tokens': 512,
            'multilingual': False
        },
        'bge-m3': {
            'provider': 'huggingface',
            'model': 'BAAI/bge-m3',
            'dimensions': 1024,
            'max_tokens': 8192,
            'multilingual': True  # Multilingüe!
        },
        
        # E5 Models
        'e5-large': {
            'provider': 'huggingface',
            'model': 'intfloat/e5-large-v2',
            'dimensions': 1024,
            'max_tokens': 512,
            'multilingual': False
        },
        'e5-multilingual': {
            'provider': 'huggingface',
            'model': 'intfloat/multilingual-e5-large',
            'dimensions': 1024,
            'max_tokens': 514,
            'multilingual': True
        },
        
        # Sentence Transformers
        'mpnet': {
            'provider': 'huggingface',
            'model': 'sentence-transformers/all-mpnet-base-v2',
            'dimensions': 768,
            'max_tokens': 384,
            'multilingual': False
        },
        'minilm': {
            'provider': 'huggingface',
            'model': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimensions': 384,
            'max_tokens': 256,
            'multilingual': False
        },
        'paraphrase-multilingual': {
            'provider': 'huggingface',
            'model': 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2',
            'dimensions': 768,
            'max_tokens': 128,
            'multilingual': True
        }
    }
    
    def __init__(
        self,
        model_name: str = 'openai-small',
        api_key: Optional[str] = None,
        batch_size: int = 100,
        **kwargs
    ):
        """
        Inicializa el generador de embeddings
        
        Args:
            model_name: Nombre del modelo
            api_key: API key (para OpenAI)
            batch_size: Tamaño de batch para generación
            **kwargs: Parámetros adicionales
        """
        if model_name not in self.SUPPORTED_MODELS:
            raise ValueError(
                f"Modelo '{model_name}' no soportado. "
                f"Use: {list(self.SUPPORTED_MODELS.keys())}"
            )
        
        self.model_name = model_name
        self.model_info = self.SUPPORTED_MODELS[model_name]
        self.batch_size = batch_size
        
        self.embed_model = self._initialize_model(api_key, **kwargs)
        
        logger.info(
            f"Embedding Generator inicializado: {model_name} "
            f"({self.model_info['dimensions']}D, "
            f"multilingual={self.model_info['multilingual']})"
        )
    
    def _initialize_model(self, api_key: Optional[str], **kwargs):
        """Inicializa el modelo de embeddings"""
        
        provider = self.model_info['provider']
        model = self.model_info['model']
        
        if provider == 'openai':
            return OpenAIEmbedding(
                model=model,
                api_key=api_key,
                **kwargs
            )
        
        elif provider == 'huggingface':
            return HuggingFaceEmbedding(
                model_name=model,
                **kwargs
            )
        
        else:
            raise ValueError(f"Provider '{provider}' no soportado")
    
    def generate_embeddings(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Genera embeddings para una lista de textos
        
        Args:
            texts: Lista de textos
            show_progress: Mostrar progreso
            
        Returns:
            Lista de vectores de embeddings
        """
        if not texts:
            logger.warning("No hay textos para generar embeddings")
            return []
        
        logger.info(f"Generando embeddings para {len(texts)} textos")
        
        try:
            # Generar en batches si es necesario
            embeddings = []
            
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                batch_embeddings = self.embed_model.get_text_embedding_batch(batch)
                embeddings.extend(batch_embeddings)
                
                if show_progress:
                    progress = min(i + self.batch_size, len(texts))
                    logger.info(f"Progreso: {progress}/{len(texts)} embeddings generados")
            
            logger.info(f"Embeddings generados: {len(embeddings)} vectores")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generando embeddings: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Genera embedding para una query
        
        Args:
            query: Texto de la query
            
        Returns:
            Vector de embedding
        """
        return self.embed_model.get_query_embedding(query)
    
    def embed_nodes(
        self,
        nodes: List[BaseNode],
        show_progress: bool = True
    ) -> List[BaseNode]:
        """
        Añade embeddings a los nodos
        
        Args:
            nodes: Lista de nodos
            show_progress: Mostrar progreso
            
        Returns:
            Nodos con embeddings
        """
        if not nodes:
            logger.warning("No hay nodos para embeddings")
            return []
        
        logger.info(f"Generando embeddings para {len(nodes)} nodos")
        
        # Extraer textos
        texts = [node.get_content() for node in nodes]
        
        # Generar embeddings
        embeddings = self.generate_embeddings(texts, show_progress)
        
        # Asignar embeddings a nodos
        for node, embedding in zip(nodes, embeddings):
            node.embedding = embedding
            # Añadir metadata del modelo
            node.metadata['embedding_model'] = self.model_name
            node.metadata['embedding_dimensions'] = self.model_info['dimensions']
        
        logger.info(f"Nodos con embeddings: {len(nodes)}")
        
        return nodes
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna información del modelo
        
        Returns:
            Diccionario con información
        """
        return {
            'name': self.model_name,
            **self.model_info,
            'batch_size': self.batch_size
        }
    
    @property
    def dimensions(self) -> int:
        """Retorna dimensiones del embedding"""
        return self.model_info['dimensions']
    
    @property
    def is_multilingual(self) -> bool:
        """Retorna si el modelo es multilingüe"""
        return self.model_info['multilingual']


class HybridEmbeddingGenerator:
    """
    Generador híbrido que combina múltiples modelos
    Útil para búsqueda multilingüe o especializada
    """
    
    def __init__(
        self,
        primary_model: str = 'openai-small',
        secondary_model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Inicializa generador híbrido
        
        Args:
            primary_model: Modelo principal
            secondary_model: Modelo secundario (opcional)
            api_key: API key para OpenAI
        """
        self.primary = EmbeddingGenerator(primary_model, api_key)
        
        self.secondary = None
        if secondary_model:
            self.secondary = EmbeddingGenerator(secondary_model, api_key)
        
        logger.info(
            f"Hybrid Embedding Generator: primary={primary_model}, "
            f"secondary={secondary_model}"
        )
    
    def embed_nodes(
        self,
        nodes: List[BaseNode],
        use_secondary: bool = False
    ) -> List[BaseNode]:
        """
        Genera embeddings con modelo primario o secundario
        
        Args:
            nodes: Lista de nodos
            use_secondary: Usar modelo secundario
            
        Returns:
            Nodos con embeddings
        """
        if use_secondary and self.secondary:
            return self.secondary.embed_nodes(nodes)
        else:
            return self.primary.embed_nodes(nodes)


# Funciones helper
def create_embedding_generator(
    model_name: str = 'openai-small',
    api_key: Optional[str] = None,
    **kwargs
) -> EmbeddingGenerator:
    """
    Factory function para crear generador
    
    Args:
        model_name: Nombre del modelo
        api_key: API key
        **kwargs: Parámetros adicionales
        
    Returns:
        Instancia de EmbeddingGenerator
    """
    return EmbeddingGenerator(
        model_name=model_name,
        api_key=api_key,
        **kwargs
    )


def get_multilingual_models() -> List[str]:
    """
    Retorna lista de modelos multilingües
    
    Returns:
        Lista de nombres de modelos
    """
    return [
        name for name, info in EmbeddingGenerator.SUPPORTED_MODELS.items()
        if info.get('multilingual', False)
    ]


def recommend_model_for_language(language: str) -> str:
    """
    Recomienda modelo según idioma
    
    Args:
        language: Código de idioma (es, ca, en, ...)
        
    Returns:
        Nombre del modelo recomendado
    """
    # Para catalán/español, usar multilingües
    if language in ['ca', 'es', 'pt', 'fr', 'de', 'it']:
        return 'e5-multilingual'  # Gratuito y multilingüe
    
    # Para inglés, modelos específicos más potentes
    elif language == 'en':
        return 'bge-large'
    
    # Default: multilingüe
    else:
        return 'e5-multilingual'
