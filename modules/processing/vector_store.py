# modules/processing/vector_store.py
"""
2.3 Vector Store Manager
Gestión de bases de datos vectoriales con múltiples backends
"""

from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from llama_index.core.schema import BaseNode, TextNode
from llama_index.core.vector_stores import (
    VectorStoreQuery,
    VectorStoreQueryResult
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.vector_stores.pinecone import PineconeVectorStore
import logging

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    Gestor unificado de vector stores con múltiples backends
    """
    
    SUPPORTED_BACKENDS = {
        'qdrant': {
            'description': 'Qdrant - Vector DB escalable',
            'local': True,
            'cloud': True,
            'persistent': True
        },
        'chroma': {
            'description': 'ChromaDB - Lightweight y fácil',
            'local': True,
            'cloud': False,
            'persistent': True
        },
        'pinecone': {
            'description': 'Pinecone - Cloud managed',
            'local': False,
            'cloud': True,
            'persistent': True
        },
        'faiss': {
            'description': 'FAISS - Alta velocidad, no persistent',
            'local': True,
            'cloud': False,
            'persistent': False
        }
    }
    
    def __init__(
        self,
        backend: str = 'qdrant',
        collection_name: str = 'rag_documents',
        persist_path: Optional[str] = 'data/vector_stores',
        dimension: int = 1536,
        **backend_kwargs
    ):
        """
        Inicializa el gestor de vector store
        
        Args:
            backend: Tipo de backend
            collection_name: Nombre de la colección
            persist_path: Path de persistencia
            dimension: Dimensiones del vector
            **backend_kwargs: Parámetros específicos del backend
        """
        if backend not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Backend '{backend}' no soportado. "
                f"Use: {list(self.SUPPORTED_BACKENDS.keys())}"
            )
        
        self.backend = backend
        self.collection_name = collection_name
        self.persist_path = Path(persist_path) if persist_path else None
        self.dimension = dimension
        
        # Crear directorio de persistencia
        if self.persist_path:
            self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Inicializar vector store
        self.vector_store = self._initialize_store(**backend_kwargs)
        
        logger.info(
            f"Vector Store Manager inicializado: {backend} "
            f"(collection='{collection_name}', dim={dimension})"
        )
    
    def _initialize_store(self, **kwargs):
        """Inicializa el vector store según backend"""
        
        if self.backend == 'qdrant':
            return self._init_qdrant(**kwargs)
        
        elif self.backend == 'chroma':
            return self._init_chroma(**kwargs)
        
        elif self.backend == 'pinecone':
            return self._init_pinecone(**kwargs)
        
        elif self.backend == 'faiss':
            return self._init_faiss(**kwargs)
        
        else:
            raise ValueError(f"Backend no implementado: {self.backend}")
    
    def _init_qdrant(self, **kwargs):
        """Inicializa Qdrant vector store"""
        try:
            from qdrant_client import QdrantClient
            
            # Modo local o cloud
            if kwargs.get('url'):
                # Modo cloud
                client = QdrantClient(
                    url=kwargs['url'],
                    api_key=kwargs.get('api_key')
                )
            else:
                # Modo local
                client = QdrantClient(
                    path=str(self.persist_path / 'qdrant')
                )
            
            return QdrantVectorStore(
                client=client,
                collection_name=self.collection_name,
                dimension=self.dimension
            )
            
        except ImportError:
            raise ImportError(
                "Qdrant no instalado. Ejecuta: pip install qdrant-client"
            )
    
    def _init_chroma(self, **kwargs):
        """Inicializa ChromaDB vector store"""
        try:
            import chromadb
            
            # Cliente persistente
            client = chromadb.PersistentClient(
                path=str(self.persist_path / 'chroma')
            )
            
            # Obtener o crear colección
            collection = client.get_or_create_collection(
                name=self.collection_name
            )
            
            return ChromaVectorStore(
                chroma_collection=collection
            )
            
        except ImportError:
            raise ImportError(
                "ChromaDB no instalado. Ejecuta: pip install chromadb"
            )
    
    def _init_pinecone(self, **kwargs):
        """Inicializa Pinecone vector store"""
        try:
            from pinecone import Pinecone
            
            api_key = kwargs.get('api_key')
            if not api_key:
                raise ValueError("Pinecone requiere api_key")
            
            pc = Pinecone(api_key=api_key)
            
            # Crear índice si no existe
            index_name = kwargs.get('index_name', self.collection_name)
            
            return PineconeVectorStore(
                pinecone_index=pc.Index(index_name)
            )
            
        except ImportError:
            raise ImportError(
                "Pinecone no instalado. Ejecuta: pip install pinecone-client"
            )
    
    def _init_faiss(self, **kwargs):
        """Inicializa FAISS vector store"""
        try:
            from llama_index.vector_stores.faiss import FaissVectorStore
            import faiss
            
            # Crear índice FAISS
            faiss_index = faiss.IndexFlatL2(self.dimension)
            
            return FaissVectorStore(faiss_index=faiss_index)
            
        except ImportError:
            raise ImportError(
                "FAISS no instalado. Ejecuta: pip install faiss-cpu"
            )
    
    def add_nodes(
        self,
        nodes: List[BaseNode],
        show_progress: bool = True
    ) -> Dict[str, Any]:
        """
        Añade nodos al vector store
        
        Args:
            nodes: Lista de nodos con embeddings
            show_progress: Mostrar progreso
            
        Returns:
            Diccionario con resultados
        """
        if not nodes:
            logger.warning("No hay nodos para añadir")
            return {'added': 0, 'errors': 0}
        
        # Verificar que tengan embeddings
        nodes_without_embeddings = [
            n for n in nodes if not hasattr(n, 'embedding') or n.embedding is None
        ]
        if nodes_without_embeddings:
            logger.warning(
                f"{len(nodes_without_embeddings)} nodos sin embeddings serán omitidos"
            )
            nodes = [n for n in nodes if hasattr(n, 'embedding') and n.embedding]
        
        logger.info(f"Añadiendo {len(nodes)} nodos al vector store")
        
        try:
            self.vector_store.add(nodes)
            
            logger.info(f"Nodos añadidos correctamente: {len(nodes)}")
            
            return {
                'added': len(nodes),
                'errors': 0,
                'collection': self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error añadiendo nodos: {e}")
            return {
                'added': 0,
                'errors': len(nodes),
                'error': str(e)
            }
    
    def query(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> VectorStoreQueryResult:
        """
        Busca en el vector store
        
        Args:
            query_embedding: Vector de embedding de la query
            top_k: Número de resultados
            filters: Filtros de metadata
            
        Returns:
            Resultados de la búsqueda
        """
        logger.info(f"Consultando vector store (top_k={top_k})")
        
        query = VectorStoreQuery(
            query_embedding=query_embedding,
            similarity_top_k=top_k,
            filters=filters
        )
        
        try:
            results = self.vector_store.query(query)
            
            logger.info(f"Query completada: {len(results.nodes)} resultados")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en query: {e}")
            raise
    
    def delete_nodes(
        self,
        node_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Elimina nodos del vector store
        
        Args:
            node_ids: Lista de IDs de nodos
            
        Returns:
            Diccionario con resultados
        """
        if not node_ids:
            return {'deleted': 0}
        
        logger.info(f"Eliminando {len(node_ids)} nodos")
        
        try:
            self.vector_store.delete_nodes(node_ids)
            
            logger.info(f"Nodos eliminados: {len(node_ids)}")
            
            return {'deleted': len(node_ids)}
            
        except Exception as e:
            logger.error(f"Error eliminando nodos: {e}")
            return {'deleted': 0, 'error': str(e)}
    
    def clear_collection(self) -> bool:
        """
        Limpia toda la colección
        
        Returns:
            True si se limpió correctamente
        """
        logger.warning(f"Limpiando colección '{self.collection_name}'")
        
        try:
            self.vector_store.clear()
            logger.info("Colección limpiada")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando colección: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del vector store
        
        Returns:
            Diccionario con estadísticas
        """
        # Nota: No todos los backends soportan estadísticas
        try:
            stats = {
                'backend': self.backend,
                'collection': self.collection_name,
                'dimension': self.dimension,
                'persist_path': str(self.persist_path) if self.persist_path else None
            }
            
            # Intentar obtener conteo (si está disponible)
            # Esto depende del backend específico
            
            return stats
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener estadísticas: {e}")
            return {'backend': self.backend, 'error': str(e)}
    
    def persist(self):
        """Persiste el vector store a disco (si aplica)"""
        if not self.SUPPORTED_BACKENDS[self.backend]['persistent']:
            logger.warning(f"Backend '{self.backend}' no soporta persistencia")
            return
        
        try:
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
                logger.info("Vector store persistido")
            else:
                logger.info("Persistencia automática (no requiere acción)")
                
        except Exception as e:
            logger.error(f"Error persistiendo vector store: {e}")


# Funciones helper
def create_vector_store(
    backend: str = 'qdrant',
    collection_name: str = 'rag_documents',
    dimension: int = 1536,
    **kwargs
) -> VectorStoreManager:
    """
    Factory function para crear vector store
    
    Args:
        backend: Tipo de backend
        collection_name: Nombre de la colección
        dimension: Dimensiones del vector
        **kwargs: Parámetros adicionales
        
    Returns:
        Instancia de VectorStoreManager
    """
    return VectorStoreManager(
        backend=backend,
        collection_name=collection_name,
        dimension=dimension,
        **kwargs
    )


def recommend_backend(
    use_case: str,
    scale: str = 'small'
) -> str:
    """
    Recomienda backend según caso de uso
    
    Args:
        use_case: 'development', 'production', 'cloud', 'local'
        scale: 'small', 'medium', 'large'
        
    Returns:
        Nombre del backend recomendado
    """
    recommendations = {
        ('development', 'small'): 'chroma',
        ('development', 'medium'): 'qdrant',
        ('development', 'large'): 'qdrant',
        ('production', 'small'): 'qdrant',
        ('production', 'medium'): 'qdrant',
        ('production', 'large'): 'pinecone',
        ('cloud', 'any'): 'pinecone',
        ('local', 'any'): 'qdrant'
    }
    
    key = (use_case, scale)
    if key not in recommendations:
        key = (use_case, 'medium')
    
    return recommendations.get(key, 'qdrant')
