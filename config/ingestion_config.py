# config/ingestion_config.py
"""
Configuració per al Mòdul 1: Data Ingestion Pipeline
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
from pathlib import Path


class IngestionConfig(BaseSettings):
    """
    Configuració del procés d'ingestió de documents
    """
    
    # Directoris
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    MARKDOWN_OUTPUT_DIR: str = "data/processed/markdown"
    IMAGES_DIR: str = "data/images"
    
    # Document Loader
    SUPPORTED_FORMATS: List[str] = [
        '.pdf', '.txt', '.md', '.docx', '.doc',
        '.csv', '.json', '.html', '.xml'
    ]
    RECURSIVE_LOAD: bool = True
    EXCLUDE_HIDDEN: bool = True
    
    # PDF Converter
    PDF_EXTRACT_IMAGES: bool = True
    PDF_IMAGE_DPI: int = 150
    PDF_ADD_METADATA_HEADER: bool = True
    
    # Text Cleaner
    REMOVE_EXTRA_WHITESPACE: bool = True
    NORMALIZE_UNICODE: bool = True
    REMOVE_SPECIAL_CHARS: bool = False
    MIN_LINE_LENGTH: int = 3
    
    # Metadata Extractor
    REQUIRED_METADATA_FIELDS: List[str] = ['filename', 'source', 'file_type']
    CUSTOM_METADATA_FIELDS: Dict[str, Any] = {}
    DETECT_LANGUAGE: bool = True
    CALCULATE_FILE_HASH: bool = True
    
    # Document Validator
    MIN_TEXT_LENGTH: int = 100
    MAX_TEXT_LENGTH: int = 10_000_000
    CHECK_DUPLICATES: bool = True
    STOP_ON_VALIDATION_ERROR: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/ingestion.log"
    
    # Performance
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 4
    
    class Config:
        env_file = ".env"
        env_prefix = "INGESTION_"
        case_sensitive = True


# Instància global de configuració
config = IngestionConfig()


# Funcions helper per crear directoris
def setup_directories():
    """Crea els directoris necessaris per la ingestió"""
    directories = [
        config.RAW_DATA_DIR,
        config.PROCESSED_DATA_DIR,
        config.MARKDOWN_OUTPUT_DIR,
        config.IMAGES_DIR,
        Path(config.LOG_FILE).parent if config.LOG_FILE else None
    ]
    
    for directory in directories:
        if directory:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directoris creats correctament")


# Configuració per diferents entorns
class DevelopmentConfig(IngestionConfig):
    """Configuració per entorn de desenvolupament"""
    LOG_LEVEL: str = "DEBUG"
    CHECK_DUPLICATES: bool = False
    BATCH_SIZE: int = 5


class ProductionConfig(IngestionConfig):
    """Configuració per entorn de producció"""
    LOG_LEVEL: str = "WARNING"
    CHECK_DUPLICATES: bool = True
    BATCH_SIZE: int = 20
    MAX_WORKERS: int = 8
    STOP_ON_VALIDATION_ERROR: bool = True


# Selecció de configuració segons entorn
def get_config(environment: str = "development") -> IngestionConfig:
    """
    Obté la configuració segons l'entorn
    
    Args:
        environment: 'development' o 'production'
        
    Returns:
        Instància de configuració
    """
    configs = {
        'development': DevelopmentConfig(),
        'production': ProductionConfig(),
    }
    
    return configs.get(environment, IngestionConfig())


# ============================================================================
# EXEMPLE DE .env PER CONFIGURAR
# ============================================================================
"""
# .env file example for Ingestion Module

# Directoris
INGESTION_RAW_DATA_DIR=data/raw
INGESTION_PROCESSED_DATA_DIR=data/processed
INGESTION_MARKDOWN_OUTPUT_DIR=data/processed/markdown
INGESTION_IMAGES_DIR=data/images

# PDF Converter
INGESTION_PDF_EXTRACT_IMAGES=true
INGESTION_PDF_IMAGE_DPI=150
INGESTION_PDF_ADD_METADATA_HEADER=true

# Text Cleaner
INGESTION_REMOVE_EXTRA_WHITESPACE=true
INGESTION_NORMALIZE_UNICODE=true
INGESTION_REMOVE_SPECIAL_CHARS=false
INGESTION_MIN_LINE_LENGTH=3

# Document Validator
INGESTION_MIN_TEXT_LENGTH=100
INGESTION_MAX_TEXT_LENGTH=10000000
INGESTION_CHECK_DUPLICATES=true

# Logging
INGESTION_LOG_LEVEL=INFO
INGESTION_LOG_FILE=logs/ingestion.log

# Performance
INGESTION_BATCH_SIZE=10
INGESTION_MAX_WORKERS=4
"""