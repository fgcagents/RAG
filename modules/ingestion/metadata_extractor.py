# modules/ingestion/metadata_extractor.py
"""
1.4 Metadata Extractor
Extracció i enriquiment de metadades
"""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import mimetypes
import hashlib
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """
    Extreu i enriqueix metadades dels documents
    """
    
    def __init__(self, custom_fields: Optional[Dict[str, Any]] = None):
        """
        Inicialitza l'extractor
        
        Args:
            custom_fields: Camps personalitzats a afegir
        """
        self.custom_fields = custom_fields or {}
    
    def extract_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Extreu metadades d'un fitxer
        
        Args:
            file_path: Path del fitxer
            
        Returns:
            Diccionari amb metadades
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Fitxer no trobat: {file_path}")
        
        stats = path.stat()
        
        metadata = {
            # Informació bàsica
            'filename': path.name,
            'file_stem': path.stem,
            'file_extension': path.suffix.lower(),
            'source': str(path.absolute()),
            
            # Tipus i mida
            'file_type': self._get_file_type(path),
            'mime_type': mimetypes.guess_type(str(path))[0],
            'size_bytes': stats.st_size,
            'size_mb': round(stats.st_size / (1024 * 1024), 2),
            
            # Dates
            'created_at': datetime.fromtimestamp(stats.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stats.st_mtime).isoformat(),
            'accessed_at': datetime.fromtimestamp(stats.st_atime).isoformat(),
            
            # Hash per detectar duplicats
            'file_hash': self._calculate_hash(path),
            
            # Timestamp d'indexació
            'indexed_at': datetime.now().isoformat(),
        }
        
        # Afegir camps personalitzats
        metadata.update(self.custom_fields)
        
        return metadata
    
    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extreu metadades del contingut del text
        
        Args:
            text: Contingut del document
            
        Returns:
            Diccionari amb metadades extretes
        """
        metadata = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'line_count': len(text.split('\n')),
            'language': self._detect_language(text),  # Simplificat
        }
        
        return metadata
    
    def _get_file_type(self, path: Path) -> str:
        """Determina el tipus de fitxer"""
        ext = path.suffix.lower()
        
        type_map = {
            '.pdf': 'PDF Document',
            '.docx': 'Word Document',
            '.doc': 'Word Document',
            '.txt': 'Text File',
            '.md': 'Markdown',
            '.csv': 'CSV Data',
            '.json': 'JSON Data',
            '.html': 'HTML Document',
            '.xml': 'XML Document',
        }
        
        return type_map.get(ext, 'Unknown')
    
    def _calculate_hash(self, path: Path, algorithm: str = 'md5') -> str:
        """
        Calcula hash del fitxer per detectar duplicats
        
        Args:
            path: Path del fitxer
            algorithm: Algoritme de hash (md5, sha256)
            
        Returns:
            Hash del fitxer
        """
        hash_func = hashlib.new(algorithm)
        
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    def _detect_language(self, text: str) -> str:
        """
        Detecta l'idioma del text (versió simplificada)
        Per producció, usar langdetect o similar
        """
        # Heurística simple basada en paraules comunes
        catalan_words = {'amb', 'per', 'que', 'dels', 'una', 'aquesta'}
        spanish_words = {'con', 'por', 'que', 'los', 'una', 'esta'}
        english_words = {'the', 'with', 'for', 'and', 'this', 'that'}
        
        words = set(text.lower().split()[:100])  # Primeres 100 paraules
        
        cat_score = len(words & catalan_words)
        spa_score = len(words & spanish_words)
        eng_score = len(words & english_words)
        
        scores = {'ca': cat_score, 'es': spa_score, 'en': eng_score}
        detected = max(scores, key=scores.get)
        
        return detected if scores[detected] > 0 else 'unknown'
    
    def enrich_metadata(
        self,
        metadata: Dict[str, Any],
        custom_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enriqueix metadades amb informació adicional
        
        Args:
            metadata: Metadades existents
            custom_data: Dades personalitzades a afegir
            
        Returns:
            Metadades enriquides
        """
        return {**metadata, **custom_data}