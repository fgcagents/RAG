# modules/processing/chunking.py
"""
2.1 Chunking Strategy
División inteligente de documentos con múltiples estrategias
"""

from typing import List, Optional, Dict, Any
from llama_index.core import Document
from llama_index.core.node_parser import (
    SentenceSplitter,
    SemanticSplitterNodeParser,
    SentenceWindowNodeParser
)
from llama_index.core.schema import BaseNode, TextNode
from llama_index.embeddings.openai import OpenAIEmbedding
import logging

logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """
    Gestor de estrategias de chunking para documentos
    """
    
    STRATEGIES = [
        'sentence',           # División por sentencias
        'semantic',          # División semántica
        'sentence_window',   # Ventanas de sentencias con contexto
        'fixed_size',        # Tamaño fijo con overlap
        'recursive'          # Recursivo por estructura
    ]
    
    def __init__(
        self,
        strategy: str = 'sentence',
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        **kwargs
    ):
        """
        Inicializa la estrategia de chunking
        
        Args:
            strategy: Estrategia a usar
            chunk_size: Tamaño del chunk en tokens
            chunk_overlap: Solapamiento entre chunks
            **kwargs: Parámetros específicos de la estrategia
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Estrategia '{strategy}' no soportada. Use: {self.STRATEGIES}")
        
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.kwargs = kwargs
        
        self.parser = self._initialize_parser()
        logger.info(f"Chunking strategy inicializada: {strategy}")
    
    def _initialize_parser(self):
        """Inicializa el parser según la estrategia"""
        
        if self.strategy == 'sentence':
            return SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator=" ",
                paragraph_separator="\n\n"
            )
        
        elif self.strategy == 'semantic':
            # Requiere embedding model
            embed_model = self.kwargs.get('embed_model')
            if not embed_model:
                logger.warning("Semantic chunking requiere embed_model, usando OpenAI por defecto")
                embed_model = OpenAIEmbedding()
            
            return SemanticSplitterNodeParser(
                embed_model=embed_model,
                buffer_size=self.kwargs.get('buffer_size', 1),
                breakpoint_percentile_threshold=self.kwargs.get('threshold', 95)
            )
        
        elif self.strategy == 'sentence_window':
            return SentenceWindowNodeParser(
                window_size=self.kwargs.get('window_size', 3),
                window_metadata_key=self.kwargs.get('metadata_key', 'window'),
                original_text_metadata_key=self.kwargs.get('original_key', 'original_text')
            )
        
        elif self.strategy == 'fixed_size':
            return SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        
        elif self.strategy == 'recursive':
            # Estrategia recursiva por headers
            return SentenceSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n\n",
                paragraph_separator="\n\n\n"
            )
        
        else:
            raise ValueError(f"Estrategia no implementada: {self.strategy}")
    
    def chunk_documents(
        self,
        documents: List[Document],
        show_progress: bool = True
    ) -> List[BaseNode]:
        """
        Divide documentos en chunks
        
        Args:
            documents: Lista de documentos
            show_progress: Mostrar progreso
            
        Returns:
            Lista de nodos (chunks)
        """
        if not documents:
            logger.warning("No hay documentos para procesar")
            return []
        
        logger.info(f"Chunking {len(documents)} documentos con estrategia '{self.strategy}'")
        
        try:
            # Parsear documentos
            nodes = self.parser.get_nodes_from_documents(
                documents,
                show_progress=show_progress
            )
            
            # Enriquecer metadata
            nodes = self._enrich_node_metadata(nodes, documents)
            
            logger.info(f"Generados {len(nodes)} chunks desde {len(documents)} documentos")
            
            return nodes
            
        except Exception as e:
            logger.error(f"Error en chunking: {e}")
            raise
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[BaseNode]:
        """
        Divide un texto individual en chunks
        
        Args:
            text: Texto a dividir
            metadata: Metadata opcional
            
        Returns:
            Lista de nodos
        """
        doc = Document(text=text, metadata=metadata or {})
        return self.chunk_documents([doc], show_progress=False)
    
    def _enrich_node_metadata(
        self,
        nodes: List[BaseNode],
        documents: List[Document]
    ) -> List[BaseNode]:
        """Enriquece la metadata de los nodos"""
        
        # Crear índice doc_id → documento
        doc_map = {doc.doc_id: doc for doc in documents}
        
        for i, node in enumerate(nodes):
            # Añadir información de chunking
            node.metadata['chunk_id'] = i
            node.metadata['chunk_strategy'] = self.strategy
            node.metadata['chunk_size'] = self.chunk_size
            node.metadata['chunk_overlap'] = self.chunk_overlap
            
            # Heredar metadata del documento original
            if hasattr(node, 'ref_doc_id') and node.ref_doc_id in doc_map:
                parent_doc = doc_map[node.ref_doc_id]
                # Merge metadata (sin sobreescribir)
                for key, value in parent_doc.metadata.items():
                    if key not in node.metadata:
                        node.metadata[key] = value
        
        return nodes
    
    def get_statistics(self, nodes: List[BaseNode]) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los chunks
        
        Args:
            nodes: Lista de nodos
            
        Returns:
            Diccionario con estadísticas
        """
        if not nodes:
            return {'total_chunks': 0}
        
        chunk_lengths = [len(node.get_content()) for node in nodes]
        
        stats = {
            'total_chunks': len(nodes),
            'avg_chunk_length': sum(chunk_lengths) / len(chunk_lengths),
            'min_chunk_length': min(chunk_lengths),
            'max_chunk_length': max(chunk_lengths),
            'total_characters': sum(chunk_lengths),
            'strategy': self.strategy,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
        
        return stats


class AdaptiveChunker:
    """
    Chunker adaptativo que selecciona estrategia según tipo de documento
    """
    
    def __init__(self):
        """Inicializa chunker adaptativo"""
        self.strategies = {}
        logger.info("Adaptive Chunker inicializado")
    
    def chunk_document(
        self,
        document: Document,
        auto_detect: bool = True
    ) -> List[BaseNode]:
        """
        Divide documento con estrategia óptima
        
        Args:
            document: Documento a procesar
            auto_detect: Detectar estrategia automáticamente
            
        Returns:
            Lista de nodos
        """
        if auto_detect:
            strategy = self._detect_best_strategy(document)
        else:
            strategy = 'sentence'  # Por defecto
        
        chunker = ChunkingStrategy(strategy=strategy)
        return chunker.chunk_documents([document], show_progress=False)
    
    def _detect_best_strategy(self, document: Document) -> str:
        """
        Detecta la mejor estrategia según el documento
        
        Heurísticas:
        - Documentos cortos (<1000 chars): fixed_size
        - Documentos técnicos/código: recursive
        - Documentos con estructura clara: sentence_window
        - Por defecto: sentence
        """
        text = document.get_content()
        metadata = document.metadata
        
        # Cortos
        if len(text) < 1000:
            return 'fixed_size'
        
        # Código o técnico
        if metadata.get('file_type') in ['code', 'xml', 'json']:
            return 'recursive'
        
        # Con headers de Markdown
        if '##' in text or '###' in text:
            return 'sentence_window'
        
        # Default
        return 'sentence'


# Funciones helper
def create_chunker(
    strategy: str = 'sentence',
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    **kwargs
) -> ChunkingStrategy:
    """
    Factory function para crear chunker
    
    Args:
        strategy: Estrategia de chunking
        chunk_size: Tamaño del chunk
        chunk_overlap: Solapamiento
        **kwargs: Parámetros adicionales
        
    Returns:
        Instancia de ChunkingStrategy
    """
    return ChunkingStrategy(
        strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        **kwargs
    )


def optimal_chunk_size_for_model(model_name: str) -> int:
    """
    Retorna tamaño óptimo de chunk según modelo
    
    Args:
        model_name: Nombre del modelo de embedding
        
    Returns:
        Tamaño de chunk recomendado
    """
    optimal_sizes = {
        'text-embedding-3-small': 512,
        'text-embedding-3-large': 512,
        'text-embedding-ada-002': 512,
        'bge-large': 512,
        'bge-small': 384,
        'e5-large': 512,
        'e5-small': 384,
        'multilingual-e5-large': 512,
    }
    
    return optimal_sizes.get(model_name, 512)
