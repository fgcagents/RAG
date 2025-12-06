# config/ingestion_config.py
"""
Configuración para el Módulo 1: Data Ingestion Pipeline
VERSIÓN CORREGIDA - Compatible con .env
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


class IngestionConfig(BaseSettings):
    """
    Configuración del proceso de ingestión de documentos
    """
    
    # Directorios
    RAW_DATA_DIR: str = "data/raw"
    PROCESSED_DATA_DIR: str = "data/processed"
    MARKDOWN_OUTPUT_DIR: str = "data/processed/markdown"
    IMAGES_DIR: str = "data/images"
    
    # Document Loader - FORMATO STRING, parseamos manualmente
    SUPPORTED_FORMATS_STR: str = ".pdf,.txt,.md,.docx,.doc,.csv,.json,.html,.xml"
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
    REQUIRED_METADATA_FIELDS_STR: str = "filename,source,file_type"
    CUSTOM_METADATA_FIELDS_JSON: str = "{}"
    DETECT_LANGUAGE: bool = True
    CALCULATE_FILE_HASH: bool = True
    
    # Document Validator
    MIN_TEXT_LENGTH: int = 100
    MAX_TEXT_LENGTH: int = 10_000_000
    CHECK_DUPLICATES: bool = True
    STOP_ON_VALIDATION_ERROR: bool = False
    
    # Document Store
    DOCSTORE_BACKEND: str = "simple"
    DOCSTORE_PATH: str = "data/docstore"
    
    # MongoDB (opcional)
    MONGODB_URI: Optional[str] = None
    MONGODB_DATABASE: Optional[str] = None
    MONGODB_COLLECTION: Optional[str] = None
    
    # Redis (opcional)
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_DB: Optional[int] = None
    REDIS_PASSWORD: Optional[str] = None
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/ingestion.log"
    LOG_FORMAT: str = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
    
    # Performance
    BATCH_SIZE: int = 10
    MAX_WORKERS: int = 4
    OPERATION_TIMEOUT: int = 300
    
    # Seguridad
    MAX_FILE_SIZE_MB: int = 100
    REQUIRE_AUTHENTICATION: bool = False
    ALLOWED_FILE_EXTENSIONS_STR: Optional[str] = None
    
    # Entorno
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Features experimentales
    ENABLE_EXPERIMENTAL_FEATURES: bool = False
    ENABLE_DETAILED_METRICS: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="INGESTION_",
        case_sensitive=True,
        extra="ignore"  # Ignorar campos extra del .env
    )
    
    # Propiedades computadas para parsear strings a listas/dicts
    @property
    def SUPPORTED_FORMATS(self) -> List[str]:
        """Parsea SUPPORTED_FORMATS_STR a lista"""
        return [fmt.strip() for fmt in self.SUPPORTED_FORMATS_STR.split(",")]
    
    @property
    def REQUIRED_METADATA_FIELDS(self) -> List[str]:
        """Parsea REQUIRED_METADATA_FIELDS_STR a lista"""
        return [field.strip() for field in self.REQUIRED_METADATA_FIELDS_STR.split(",")]
    
    @property
    def CUSTOM_METADATA_FIELDS(self) -> Dict[str, Any]:
        """Parsea CUSTOM_METADATA_FIELDS_JSON a diccionario"""
        try:
            return json.loads(self.CUSTOM_METADATA_FIELDS_JSON)
        except json.JSONDecodeError:
            return {}
    
    @property
    def ALLOWED_FILE_EXTENSIONS(self) -> List[str]:
        """Parsea ALLOWED_FILE_EXTENSIONS_STR a lista"""
        if not self.ALLOWED_FILE_EXTENSIONS_STR:
            return self.SUPPORTED_FORMATS
        return [ext.strip() for ext in self.ALLOWED_FILE_EXTENSIONS_STR.split(",")]


# Instancia global de configuración
config = IngestionConfig()


# Funciones helper
def setup_directories():
    """Crea los directorios necesarios para la ingestión"""
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
    
    print("✓ Directorios creados correctamente")


# Configuración por entornos
class DevelopmentConfig(IngestionConfig):
    """Configuración para entorno de desarrollo"""
    LOG_LEVEL: str = "DEBUG"
    CHECK_DUPLICATES: bool = False
    BATCH_SIZE: int = 5
    MAX_WORKERS: int = 2
    MIN_TEXT_LENGTH: int = 50


class ProductionConfig(IngestionConfig):
    """Configuración para entorno de producción"""
    LOG_LEVEL: str = "WARNING"
    CHECK_DUPLICATES: bool = True
    BATCH_SIZE: int = 20
    MAX_WORKERS: int = 8
    STOP_ON_VALIDATION_ERROR: bool = True
    DEBUG: bool = False


class TestingConfig(IngestionConfig):
    """Configuración para entorno de testing"""
    LOG_LEVEL: str = "DEBUG"
    CHECK_DUPLICATES: bool = False
    MIN_TEXT_LENGTH: int = 10
    BATCH_SIZE: int = 2
    MAX_WORKERS: int = 1
    RAW_DATA_DIR: str = "tests/fixtures/raw"
    PROCESSED_DATA_DIR: str = "tests/fixtures/processed"
    MARKDOWN_OUTPUT_DIR: str = "tests/fixtures/markdown"
    IMAGES_DIR: str = "tests/fixtures/images"


def get_config(environment: str = "development") -> IngestionConfig:
    """
    Obtiene la configuración según el entorno
    
    Args:
        environment: 'development', 'testing' o 'production'
        
    Returns:
        Instancia de configuración
    """
    configs = {
        'development': DevelopmentConfig(),
        'testing': TestingConfig(),
        'production': ProductionConfig(),
    }
    
    return configs.get(environment.lower(), IngestionConfig())


# Función de validación
def validate_config():
    """Valida que la configuración sea correcta"""
    errors = []
    
    # Validar directorios
    if not config.RAW_DATA_DIR:
        errors.append("RAW_DATA_DIR no puede estar vacío")
    
    # Validar rangos
    if config.MIN_TEXT_LENGTH < 0:
        errors.append("MIN_TEXT_LENGTH debe ser >= 0")
    
    if config.MAX_TEXT_LENGTH < config.MIN_TEXT_LENGTH:
        errors.append("MAX_TEXT_LENGTH debe ser >= MIN_TEXT_LENGTH")
    
    if config.BATCH_SIZE < 1:
        errors.append("BATCH_SIZE debe ser >= 1")
    
    if config.MAX_WORKERS < 1:
        errors.append("MAX_WORKERS debe ser >= 1")
    
    # Validar formatos
    if not config.SUPPORTED_FORMATS:
        errors.append("SUPPORTED_FORMATS no puede estar vacío")
    
    if errors:
        raise ValueError(f"Errores de configuración:\n" + "\n".join(f"  - {e}" for e in errors))
    
    return True


# Validar al cargar
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  ADVERTENCIA: {e}")