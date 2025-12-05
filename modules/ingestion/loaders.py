# modules/ingestion/loaders.py
"""
1.1 Document Loaders
Càrrega de diferents formats de documents
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
from llama_index.core import SimpleDirectoryReader, Document
from llama_index.core.schema import Document as LlamaDocument
import logging

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Gestor de càrrega de documents amb suport per múltiples formats
    """
    
    SUPPORTED_FORMATS = {
        '.pdf', '.txt', '.md', '.docx', '.doc', 
        '.csv', '.json', '.html', '.xml'
    }
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Inicialitza el carregador de documents
        
        Args:
            base_path: Directori base per carregar documents
        """
        self.base_path = Path(base_path) if base_path else None
        
    def load_directory(
        self, 
        directory: str,
        recursive: bool = True,
        required_exts: Optional[List[str]] = None,
        exclude_hidden: bool = True
    ) -> List[LlamaDocument]:
        """
        Carrega tots els documents d'un directori
        
        Args:
            directory: Path del directori
            recursive: Carregar subdirectoris
            required_exts: Extensions específiques a carregar
            exclude_hidden: Excloure fitxers ocults
            
        Returns:
            Llista de documents carregats
        """
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directori no trobat: {directory}")
            
            logger.info(f"Carregant documents de: {directory}")
            
            # Configurar SimpleDirectoryReader
            reader = SimpleDirectoryReader(
                input_dir=str(dir_path),
                recursive=recursive,
                required_exts=required_exts or list(self.SUPPORTED_FORMATS),
                exclude_hidden=exclude_hidden,
                errors='ignore'
            )
            
            documents = reader.load_data()
            logger.info(f"Carregats {len(documents)} documents")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error carregant directori {directory}: {e}")
            raise
    
    def load_file(self, file_path: str) -> LlamaDocument:
        """
        Carrega un document individual
        
        Args:
            file_path: Path del fitxer
            
        Returns:
            Document carregat
        """
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"Fitxer no trobat: {file_path}")
            
            if path.suffix.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Format no suportat: {path.suffix}")
            
            logger.info(f"Carregant fitxer: {file_path}")
            
            reader = SimpleDirectoryReader(input_files=[str(path)])
            documents = reader.load_data()
            
            if not documents:
                raise ValueError(f"No s'ha pogut carregar: {file_path}")
            
            return documents[0]
            
        except Exception as e:
            logger.error(f"Error carregant fitxer {file_path}: {e}")
            raise
    
    def get_file_stats(self, directory: str) -> Dict[str, Any]:
        """
        Obté estadístiques dels fitxers en un directori
        
        Args:
            directory: Path del directori
            
        Returns:
            Diccionari amb estadístiques
        """
        dir_path = Path(directory)
        stats = {
            'total_files': 0,
            'by_extension': {},
            'total_size_mb': 0
        }
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in self.SUPPORTED_FORMATS:
                    stats['total_files'] += 1
                    stats['by_extension'][ext] = stats['by_extension'].get(ext, 0) + 1
                    stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats