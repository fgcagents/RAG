# modules/processing/metadata_index.py
"""
2.5 Metadata Index
Índice de metadata para filtrado avanzado y búsqueda híbrida
"""

from typing import List, Optional, Dict, Any, Set
from pathlib import Path
from datetime import datetime
import json
from collections import defaultdict
from llama_index.core.schema import BaseNode
import logging

logger = logging.getLogger(__name__)


class MetadataIndex:
    """
    Índice de metadata para búsqueda y filtrado avanzado
    """
    
    def __init__(
        self,
        persist_path: str = 'data/indexes/metadata'
    ):
        """
        Inicializa el índice de metadata
        
        Args:
            persist_path: Path de persistencia
        """
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        # Índices invertidos por campo
        self.field_index: Dict[str, Dict[Any, Set[str]]] = defaultdict(lambda: defaultdict(set))
        
        # Metadata completa por node_id
        self.node_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Estadísticas
        self.stats = {
            'total_nodes': 0,
            'indexed_fields': set(),
            'last_updated': None
        }
        
        # Cargar si existe
        self._load()
        
        logger.info("Metadata Index inicializado")
    
    def index_nodes(
        self,
        nodes: List[BaseNode],
        fields_to_index: Optional[List[str]] = None
    ):
        """
        Indexa la metadata de los nodos
        
        Args:
            nodes: Lista de nodos
            fields_to_index: Campos específicos a indexar (None = todos)
        """
        if not nodes:
            logger.warning("No hay nodos para indexar")
            return
        
        logger.info(f"Indexando metadata de {len(nodes)} nodos")
        
        for node in nodes:
            node_id = node.node_id
            metadata = node.metadata
            
            # Guardar metadata completa
            self.node_metadata[node_id] = metadata
            
            # Indexar campos
            fields = fields_to_index or metadata.keys()
            
            for field in fields:
                if field in metadata:
                    value = metadata[field]
                    
                    # Normalizar valor para indexación
                    normalized_value = self._normalize_value(value)
                    
                    # Añadir al índice invertido
                    self.field_index[field][normalized_value].add(node_id)
                    
                    # Actualizar campos indexados
                    self.stats['indexed_fields'].add(field)
        
        # Actualizar estadísticas
        self.stats['total_nodes'] = len(self.node_metadata)
        self.stats['last_updated'] = datetime.now().isoformat()
        
        logger.info(
            f"Metadata indexada: {len(self.node_metadata)} nodos, "
            f"{len(self.stats['indexed_fields'])} campos"
        )
    
    def search(
        self,
        filters: Dict[str, Any],
        match_all: bool = True
    ) -> List[str]:
        """
        Busca nodos por metadata
        
        Args:
            filters: Diccionario de filtros {campo: valor}
            match_all: Si True, deben cumplir todos los filtros
            
        Returns:
            Lista de node_ids que cumplen los filtros
        """
        if not filters:
            return list(self.node_metadata.keys())
        
        logger.debug(f"Buscando con filtros: {filters} (match_all={match_all})")
        
        result_sets = []
        
        for field, value in filters.items():
            if field not in self.field_index:
                logger.warning(f"Campo '{field}' no indexado")
                result_sets.append(set())
                continue
            
            normalized_value = self._normalize_value(value)
            
            if normalized_value in self.field_index[field]:
                result_sets.append(self.field_index[field][normalized_value])
            else:
                result_sets.append(set())
        
        # Combinar resultados
        if match_all:
            # Intersección (AND)
            result = result_sets[0] if result_sets else set()
            for s in result_sets[1:]:
                result &= s
        else:
            # Unión (OR)
            result = set()
            for s in result_sets:
                result |= s
        
        logger.debug(f"Encontrados {len(result)} nodos")
        
        return list(result)
    
    def range_search(
        self,
        field: str,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None
    ) -> List[str]:
        """
        Búsqueda por rango de valores
        
        Args:
            field: Campo a buscar
            min_value: Valor mínimo (inclusive)
            max_value: Valor máximo (inclusive)
            
        Returns:
            Lista de node_ids
        """
        if field not in self.field_index:
            logger.warning(f"Campo '{field}' no indexado")
            return []
        
        result_ids = []
        
        for value, node_ids in self.field_index[field].items():
            # Intentar comparación numérica
            try:
                if min_value is not None and value < min_value:
                    continue
                if max_value is not None and value > max_value:
                    continue
                
                result_ids.extend(node_ids)
                
            except TypeError:
                # No se puede comparar, omitir
                continue
        
        return result_ids
    
    def get_unique_values(
        self,
        field: str
    ) -> List[Any]:
        """
        Obtiene valores únicos de un campo
        
        Args:
            field: Campo a consultar
            
        Returns:
            Lista de valores únicos
        """
        if field not in self.field_index:
            return []
        
        return list(self.field_index[field].keys())
    
    def get_value_counts(
        self,
        field: str
    ) -> Dict[Any, int]:
        """
        Obtiene conteo de valores de un campo
        
        Args:
            field: Campo a consultar
            
        Returns:
            Diccionario {valor: conteo}
        """
        if field not in self.field_index:
            return {}
        
        return {
            value: len(node_ids)
            for value, node_ids in self.field_index[field].items()
        }
    
    def get_node_metadata(
        self,
        node_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadata de un nodo
        
        Args:
            node_id: ID del nodo
            
        Returns:
            Metadata o None
        """
        return self.node_metadata.get(node_id)
    
    def delete_node(
        self,
        node_id: str
    ):
        """
        Elimina un nodo del índice
        
        Args:
            node_id: ID del nodo
        """
        if node_id not in self.node_metadata:
            return
        
        metadata = self.node_metadata[node_id]
        
        # Eliminar de índices invertidos
        for field, value in metadata.items():
            if field in self.field_index:
                normalized_value = self._normalize_value(value)
                if normalized_value in self.field_index[field]:
                    self.field_index[field][normalized_value].discard(node_id)
        
        # Eliminar metadata
        del self.node_metadata[node_id]
        
        # Actualizar stats
        self.stats['total_nodes'] = len(self.node_metadata)
        self.stats['last_updated'] = datetime.now().isoformat()
    
    def clear(self):
        """Limpia completamente el índice"""
        self.field_index.clear()
        self.node_metadata.clear()
        self.stats['total_nodes'] = 0
        self.stats['indexed_fields'] = set()
        self.stats['last_updated'] = datetime.now().isoformat()
        
        logger.info("Metadata index limpiado")
    
    def persist(self):
        """Persiste el índice a disco"""
        try:
            # Guardar field_index
            field_index_file = self.persist_path / 'field_index.json'
            with open(field_index_file, 'w') as f:
                # Convertir sets a listas para JSON
                serializable_index = {
                    field: {
                        str(value): list(node_ids)
                        for value, node_ids in values.items()
                    }
                    for field, values in self.field_index.items()
                }
                json.dump(serializable_index, f, indent=2)
            
            # Guardar node_metadata
            metadata_file = self.persist_path / 'node_metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(self.node_metadata, f, indent=2)
            
            # Guardar stats
            stats_file = self.persist_path / 'stats.json'
            with open(stats_file, 'w') as f:
                serializable_stats = {
                    **self.stats,
                    'indexed_fields': list(self.stats['indexed_fields'])
                }
                json.dump(serializable_stats, f, indent=2)
            
            logger.info("Metadata index persistido")
            
        except Exception as e:
            logger.error(f"Error persistiendo metadata index: {e}")
    
    def _load(self):
        """Carga el índice desde disco"""
        try:
            # Cargar field_index
            field_index_file = self.persist_path / 'field_index.json'
            if field_index_file.exists():
                with open(field_index_file, 'r') as f:
                    loaded_index = json.load(f)
                    
                    # Convertir listas de vuelta a sets
                    self.field_index = defaultdict(lambda: defaultdict(set))
                    for field, values in loaded_index.items():
                        for value, node_ids in values.items():
                            self.field_index[field][value] = set(node_ids)
            
            # Cargar node_metadata
            metadata_file = self.persist_path / 'node_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    self.node_metadata = json.load(f)
            
            # Cargar stats
            stats_file = self.persist_path / 'stats.json'
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    loaded_stats = json.load(f)
                    self.stats = {
                        **loaded_stats,
                        'indexed_fields': set(loaded_stats.get('indexed_fields', []))
                    }
            
            logger.info(
                f"Metadata index cargado: {self.stats['total_nodes']} nodos"
            )
            
        except Exception as e:
            logger.warning(f"No se pudo cargar metadata index: {e}")
    
    def _normalize_value(self, value: Any) -> Any:
        """
        Normaliza valor para indexación
        
        Args:
            value: Valor a normalizar
            
        Returns:
            Valor normalizado
        """
        # Strings: lowercase y strip
        if isinstance(value, str):
            return value.lower().strip()
        
        # Listas/tuplas: convertir a tupla ordenada
        if isinstance(value, (list, tuple)):
            return tuple(sorted(str(v) for v in value))
        
        # Otros: dejar como está
        return value
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas del índice
        
        Returns:
            Diccionario con estadísticas
        """
        stats = {
            **self.stats,
            'indexed_fields': list(self.stats['indexed_fields']),
            'fields_detail': {
                field: {
                    'unique_values': len(values),
                    'total_nodes': sum(len(node_ids) for node_ids in values.values())
                }
                for field, values in self.field_index.items()
            }
        }
        
        return stats


# Funciones helper
def create_metadata_index(
    persist_path: str = 'data/indexes/metadata'
) -> MetadataIndex:
    """
    Factory function para crear metadata index
    
    Args:
        persist_path: Path de persistencia
        
    Returns:
        Instancia de MetadataIndex
    """
    return MetadataIndex(persist_path=persist_path)


def hybrid_search(
    vector_results: List[str],
    metadata_index: MetadataIndex,
    metadata_filters: Dict[str, Any],
    rerank: bool = True
) -> List[str]:
    """
    Búsqueda híbrida combinando vectorial y metadata
    
    Args:
        vector_results: IDs de búsqueda vectorial
        metadata_index: Índice de metadata
        metadata_filters: Filtros de metadata
        rerank: Re-rankear por metadata
        
    Returns:
        Lista de node_ids filtrados
    """
    if not metadata_filters:
        return vector_results
    
    # Buscar por metadata
    metadata_results = metadata_index.search(metadata_filters, match_all=True)
    
    # Intersección: nodos que cumplen ambos criterios
    hybrid_results = [
        node_id for node_id in vector_results
        if node_id in metadata_results
    ]
    
    logger.info(
        f"Hybrid search: {len(vector_results)} vectorial → "
        f"{len(hybrid_results)} after metadata filter"
    )
    
    return hybrid_results
