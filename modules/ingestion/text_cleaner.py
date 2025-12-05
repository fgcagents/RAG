# modules/ingestion/text_cleaner.py
"""
1.3 Text Cleaner
Neteja i normalització de text
"""

import re
import unicodedata
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Neteja i normalitza text per millor processament
    """
    
    def __init__(
        self,
        remove_extra_whitespace: bool = True,
        normalize_unicode: bool = True,
        remove_special_chars: bool = False,
        min_line_length: int = 3
    ):
        """
        Inicialitza el netejador
        
        Args:
            remove_extra_whitespace: Eliminar espais excessius
            normalize_unicode: Normalitzar caràcters Unicode
            remove_special_chars: Eliminar caràcters especials
            min_line_length: Longitud mínima de línia a mantenir
        """
        self.remove_extra_whitespace = remove_extra_whitespace
        self.normalize_unicode = normalize_unicode
        self.remove_special_chars = remove_special_chars
        self.min_line_length = min_line_length
    
    def clean(self, text: str) -> str:
        """
        Neteja el text segons configuració
        
        Args:
            text: Text a netejar
            
        Returns:
            Text netejat
        """
        if not text:
            return ""
        
        original_length = len(text)
        
        # Normalitzar Unicode
        if self.normalize_unicode:
            text = unicodedata.normalize('NFKC', text)
        
        # Eliminar línies massa curtes (probablement artifacts)
        lines = text.split('\n')
        lines = [
            line for line in lines 
            if len(line.strip()) >= self.min_line_length or line.strip() == ''
        ]
        text = '\n'.join(lines)
        
        # Eliminar espais excessius
        if self.remove_extra_whitespace:
            text = re.sub(r' +', ' ', text)  # Múltiples espais → 1 espai
            text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Múltiples \n → 2 \n
            text = text.strip()
        
        # Eliminar caràcters especials (opcional, pot perdre informació)
        if self.remove_special_chars:
            text = re.sub(r'[^\w\s\-.,;:!?áéíóúàèìòùäëïöüñç]', '', text, flags=re.IGNORECASE)
        
        # Netejar patrons comuns de PDFs
        text = self._clean_pdf_artifacts(text)
        
        logger.debug(f"Text netejat: {original_length} → {len(text)} caràcters")
        
        return text
    
    def _clean_pdf_artifacts(self, text: str) -> str:
        """Elimina artifacts comuns de PDFs"""
        # Eliminar headers/footers repetitius (heurística simple)
        # Això es pot millorar amb ML o patrons específics
        
        # Eliminar línies que són només números de pàgina
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Eliminar separadors de guions excessius
        text = re.sub(r'-{5,}', '', text)
        
        return text
    
    def remove_headers_footers(
        self, 
        text: str, 
        header_pattern: Optional[str] = None,
        footer_pattern: Optional[str] = None
    ) -> str:
        """
        Elimina headers i footers amb patrons personalitzats
        
        Args:
            text: Text original
            header_pattern: Regex per header
            footer_pattern: Regex per footer
            
        Returns:
            Text sense headers/footers
        """
        if header_pattern:
            text = re.sub(header_pattern, '', text, flags=re.MULTILINE)
        
        if footer_pattern:
            text = re.sub(footer_pattern, '', text, flags=re.MULTILINE)
        
        return text