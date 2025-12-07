# modules/processing/index_builder.py
"""
2.4 Index Builder
Construcción y actualización de índices vectoriales
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from llama_index.core import (
    VectorStoreIndex,
    StorageContext,
    load_index_from_storage,
    Document
)
from llama_index.core.schema import BaseNode
from llama_index.core.embeddings import BaseEmbedding
import json
import logging

logger = logging.getLogger(__name__)


class IndexBuilder:
    """
    Constructor y gestor de índices vectoriales
    """
    
    def __init__(
        self,
        vector_store_manager,
        embed_model: BaseEmbedding,
        persist_dir: str = 'data/indexes',
        index_name: str = 'main_index'
    ):
        """
        Inicializa el constructor de índices
        
        Args:
            vector_store_manager: Gestor del vector store
            embed_model: Modelo de embeddings
            persist_dir: Directorio de persistencia
            index_name: Nombre del índice
        """
        self.vector_store_manager = vector_store_manager
        self.embed_model = embed_model
        self.persist_dir = Path(persist_dir)
        self.index_name = index_name
        
        # Crear directorio
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Índice principal
        self.index: Optional[VectorStoreIndex] = None
        
        # Metadata del índice
        self.index_metadata = self._load_metadata()
        
        logger.info(f"Index Builder inicializado: {index_name}")
    
    def build_index(
        self,
        nodes: List[BaseNode],
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        Construye un índice desde nodos
        
        Args:
            nodes: Lista de nodos con embeddings
            show_progress: Mostrar progreso
            
        Returns:
            Índice vectorial
        """
        if not nodes:
            raise ValueError("No hay nodos para construir el índice")
        
        logger.info(f"Construyendo índice con {len(nodes)} nodos")
        
        try:
            # Crear storage context con el vector store
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store_manager.vector_store
            )
            
            # Construir índice
            self.index = VectorStoreIndex(
                nodes=nodes,
                storage_context=storage_context,
                embed_model=self.embed_model,
                show_progress=show_progress
            )
            
            # Actualizar metadata
            self._update_metadata({
                'total_nodes': len(nodes),
                'created_at': datetime.now().isoformat(),
                'embedding_model': getattr(self.embed_model, 'model_name', 'unknown'),
                'vector_store': self.vector_store_manager.backend
            })
            
            logger.info("Índice construido correctamente")
            
            return self.index
            
        except Exception as e:
            logger.error(f"Error construyendo índice: {e}")
            raise
    
    def build_from_documents(
        self,
        documents: List[Document],
        chunker,
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        Construye índice desde documentos (incluye chunking y embedding)
        
        Args:
            documents: Lista de documentos
            chunker: Estrategia de chunking
            show_progress: Mostrar progreso
            
        Returns:
            Índice vectorial
        """
        logger.info(f"Construyendo índice desde {len(documents)} documentos")
        
        # 1. Chunking
        logger.info("Paso 1/3: Chunking...")
        nodes = chunker.chunk_documents(documents, show_progress)
        
        # 2. Embeddings (si no los tienen)
        logger.info("Paso 2/3: Generando embeddings...")
        nodes_without_embeddings = [
            n for n in nodes 
            if not hasattr(n, 'embedding') or n.embedding is None
        ]
        
        if nodes_without_embeddings:
            logger.info(f"Generando embeddings para {len(nodes_without_embeddings)} nodos")
            # Aquí se asume que el embed_model es un EmbeddingGenerator
            from .embeddings import EmbeddingGenerator
            if isinstance(self.embed_model, EmbeddingGenerator):
                nodes = self.embed_model.embed_nodes(nodes, show_progress)
        
        # 3. Construcción del índice
        logger.info("Paso 3/3: Construyendo índice...")
        return self.build_index(nodes, show_progress)
    
    def load_index(self) -> Optional[VectorStoreIndex]:
        """
        Carga un índice existente desde disco
        
        Returns:
            Índice cargado o None
        """
        try:
            logger.info(f"Cargando índice desde {self.persist_dir}")
            
            # Crear storage context
            storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store_manager.vector_store,
                persist_dir=str(self.persist_dir)
            )
            
            # Cargar índice
            self.index = load_index_from_storage(
                storage_context=storage_context,
                embed_model=self.embed_model
            )
            
            logger.info("Índice cargado correctamente")
            
            return self.index
            
        except Exception as e:
            logger.warning(f"No se pudo cargar índice: {e}")
            return None
    
    def update_index(
        self,
        new_nodes: List[BaseNode],
        delete_old: bool = False
    ) -> Dict[str, Any]:
        """
        Actualiza el índice con nuevos nodos
        
        Args:
            new_nodes: Nuevos nodos a añadir
            delete_old: Eliminar nodos antiguos antes
            
        Returns:
            Diccionario con resultados
        """
        if not self.index:
            logger.warning("No hay índice cargado, construyendo uno nuevo")
            self.build_index(new_nodes)
            return {'action': 'created', 'nodes': len(new_nodes)}
        
        logger.info(f"Actualizando índice con {len(new_nodes)} nodos")
        
        try:
            if delete_old:
                logger.info("Eliminando nodos antiguos")
                # Aquí se implementaría la lógica de eliminación
                pass
            
            # Insertar nuevos nodos
            self.index.insert_nodes(new_nodes)
            
            # Actualizar metadata
            current_total = self.index_metadata.get('total_nodes', 0)
            self._update_metadata({
                'total_nodes': current_total + len(new_nodes),
                'last_updated': datetime.now().isoformat()
            })
            
            logger.info("Índice actualizado correctamente")
            
            return {
                'action': 'updated',
                'nodes_added': len(new_nodes),
                'total_nodes': current_total + len(new_nodes)
            }
            
        except Exception as e:
            logger.error(f"Error actualizando índice: {e}")
            return {'action': 'error', 'error': str(e)}
    
    def persist(self):
        """Persiste el índice a disco"""
        if not self.index:
            logger.warning("No hay índice para persistir")
            return
        
        try:
            logger.info(f"Persistiendo índice en {self.persist_dir}")
            
            self.index.storage_context.persist(persist_dir=str(self.persist_dir))
            
            # Guardar metadata
            self._save_metadata()
            
            logger.info("Índice persistido correctamente")
            
        except Exception as e:
            logger.error(f"Error persistiendo índice: {e}")
            raise
    
    def rebuild_index(
        self,
        nodes: List[BaseNode],
        show_progress: bool = True
    ) -> VectorStoreIndex:
        """
        Reconstruye completamente el índice
        
        Args:
            nodes: Nuevos nodos
            show_progress: Mostrar progreso
            
        Returns:
            Nuevo índice
        """
        logger.warning("Reconstruyendo índice completamente")
        
        # Limpiar vector store
        self.vector_store_manager.clear_collection()
        
        # Construir nuevo índice
        return self.build_index(nodes, show_progress)
    
    def get_query_engine(self, **kwargs):
        """
        Obtiene query engine del índice
        
        Args:
            **kwargs: Parámetros para el query engine
            
        Returns:
            Query engine
        """
        if not self.index:
            raise ValueError("No hay índice construido. Llama a build_index() primero")
        
        return self.index.as_query_engine(**kwargs)
    
    def get_retriever(self, **kwargs):
        """
        Obtiene retriever del índice
        
        Args:
            **kwargs: Parámetros para el retriever
            
        Returns:
            Retriever
        """
        if not self.index:
            raise ValueError("No hay índice construido. Llama a build_index() primero")
        
        return self.index.as_retriever(**kwargs)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Carga metadata del índice"""
        metadata_file = self.persist_dir / f"{self.index_name}_metadata.json"
        
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        return {
            'index_name': self.index_name,
            'version': '1.0',
            'created_at': None,
            'last_updated': None,
            'total_nodes': 0
        }
    
    def _save_metadata(self):
        """Guarda metadata del índice"""
        metadata_file = self.persist_dir / f"{self.index_name}_metadata.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(self.index_metadata, f, indent=2)
    
    def _update_metadata(self, updates: Dict[str, Any]):
        """Actualiza metadata"""
        self.index_metadata.update(updates)
        self._save_metadata()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            **self.index_metadata,
            'vector_store': self.vector_store_manager.backend,
            'embedding_model': getattr(self.embed_model, 'model_name', 'unknown'),
            'persist_dir': str(self.persist_dir)
        }
        
        if self.index:
            # Añadir estadísticas del índice activo
            stats['index_loaded'] = True
        else:
            stats['index_loaded'] = False
        
        return stats


# Funciones helper
def create_index_builder(
    vector_store_manager,
    embed_model,
    persist_dir: str = 'data/indexes',
    index_name: str = 'main_index'
) -> IndexBuilder:
    """
    Factory function para crear index builder
    
    Args:
        vector_store_manager: Gestor del vector store
        embed_model: Modelo de embeddings
        persist_dir: Directorio de persistencia
        index_name: Nombre del índice
        
    Returns:
        Instancia de IndexBuilder
    """
    return IndexBuilder(
        vector_store_manager=vector_store_manager,
        embed_model=embed_model,
        persist_dir=persist_dir,
        index_name=index_name
    )


def build_complete_pipeline(
    documents: List[Document],
    chunking_strategy: str = 'sentence',
    embedding_model: str = 'openai-small',
    vector_store_backend: str = 'qdrant',
    **kwargs
):
    """
    Pipeline completo de construcción de índice
    
    Args:
        documents: Lista de documentos
        chunking_strategy: Estrategia de chunking
        embedding_model: Modelo de embeddings
        vector_store_backend: Backend del vector store
        **kwargs: Parámetros adicionales
        
    Returns:
        Tupla (index_builder, index, statistics)
    """
    from .chunking import ChunkingStrategy
    from .embeddings import EmbeddingGenerator
    from .vector_store import VectorStoreManager
    
    logger.info("Iniciando pipeline completo de indexación")
    
    # 1. Chunking
    chunker = ChunkingStrategy(strategy=chunking_strategy)
    nodes = chunker.chunk_documents(documents)
    
    # 2. Embeddings
    embedder = EmbeddingGenerator(model_name=embedding_model)
    nodes = embedder.embed_nodes(nodes)
    
    # 3. Vector Store
    vector_store = VectorStoreManager(
        backend=vector_store_backend,
        dimension=embedder.dimensions
    )
    
    # 4. Index Builder
    builder = IndexBuilder(
        vector_store_manager=vector_store,
        embed_model=embedder.embed_model
    )
    
    # 5. Construir índice
    index = builder.build_index(nodes)
    
    # 6. Persistir
    builder.persist()
    
    # 7. Estadísticas
    stats = {
        'documents': len(documents),
        'nodes': len(nodes),
        'chunking': chunker.get_statistics(nodes),
        'embedding': embedder.get_model_info(),
        'vector_store': vector_store.get_statistics(),
        'index': builder.get_statistics()
    }
    
    logger.info("Pipeline completado exitosamente")
    
    return builder, index, stats
