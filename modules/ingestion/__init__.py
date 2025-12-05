# modules/ingestion/__init__.py
"""
Mòdul 1: Data Ingestion Pipeline
Captura, conversió i preparació de documents
"""

from .loaders import DocumentLoader
from .pdf_converter import PDFToMarkdownConverter
from .text_cleaner import TextCleaner
from .metadata_extractor import MetadataExtractor
from .validator import DocumentValidator

__all__ = [
    'DocumentLoader',
    'PDFToMarkdownConverter',
    'TextCleaner',
    'MetadataExtractor',
    'DocumentValidator'
]