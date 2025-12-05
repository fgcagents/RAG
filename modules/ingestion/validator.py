# modules/ingestion/validator.py
"""
1.5 Document Validator
Validació de qualitat dels documents
"""

from typing import Dict, List, Any, Optional
from llama_index.core.schema import Document as LlamaDocument
import logging
import hashlib

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Error de validació personalitzat"""
    pass


class DocumentValidator:
    """
    Valida la qualitat i completesa dels documents
    """
    
    def __init__(
        self,
        min_text_length: int = 100,
        max_text_length: int = 10_000_000,
        required_metadata: Optional[List[str]] = None,
        check_duplicates: bool = True
    ):
        """
        Inicialitza el validador
        
        Args:
            min_text_length: Longitud mínima de text
            max_text_length: Longitud màxima de text
            required_metadata: Camps de metadata obligatoris
            check_duplicates: Verificar duplicats
        """
        self.min_text_length = min_text_length
        self.max_text_length = max_text_length
        self.required_metadata = required_metadata or ['filename', 'source']
        self.check_duplicates = check_duplicates
        self.seen_hashes = set()
    
    def validate(self, document: LlamaDocument) -> bool:
        """
        Valida un document
        
        Args:
            document: Document a validar
            
        Returns:
            True si és vàlid
            
        Raises:
            ValidationError: Si la validació falla
        """
        errors = []
        
        # Normalitzar metadata (afegir alternatives com filename, file_hash)
        try:
            self._normalize_metadata(document)
        except Exception:
            # no fallar aquí, seguir amb la validació i recollir errors
            logger.debug("No s'ha pogut normalitzar metadata")

        # Validar text
        text_errors = self._validate_text(document.text)
        errors.extend(text_errors)
        
        # Validar metadata
        metadata_errors = self._validate_metadata(document.metadata)
        errors.extend(metadata_errors)
        
        # Verificar duplicats
        if self.check_duplicates:
            duplicate_error = self._check_duplicate(document)
            if duplicate_error:
                errors.append(duplicate_error)
        
        if errors:
            error_msg = "; ".join(errors)
            logger.warning(f"Document invàlid: {error_msg}")
            raise ValidationError(error_msg)
        
        logger.debug(f"Document vàlid: {document.metadata.get('filename', 'unknown')}")
        return True
    
    def validate_batch(
        self, 
        documents: List[LlamaDocument],
        stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Valida un lot de documents
        
        Args:
            documents: Llista de documents
            stop_on_error: Aturar en el primer error
            
        Returns:
            Diccionari amb resultats de validació
        """
        results = {
            'total': len(documents),
            'valid': 0,
            'invalid': 0,
            'errors': []
        }
        
        for i, doc in enumerate(documents):
            try:
                self.validate(doc)
                results['valid'] += 1
            except ValidationError as e:
                results['invalid'] += 1
                results['errors'].append({
                    'index': i,
                    'filename': doc.metadata.get('filename', 'unknown'),
                    'error': str(e)
                })
                
                if stop_on_error:
                    break
        
        logger.info(
            f"Validació completada: {results['valid']}/{results['total']} vàlids"
        )
        
        return results
    
    def _validate_text(self, text: str) -> List[str]:
        """Valida el contingut de text"""
        errors = []
        
        if not text or not text.strip():
            errors.append("Text buit")
            return errors
        
        text_len = len(text)
        
        if text_len < self.min_text_length:
            errors.append(
                f"Text massa curt: {text_len} < {self.min_text_length} caràcters"
            )
        
        if text_len > self.max_text_length:
            errors.append(
                f"Text massa llarg: {text_len} > {self.max_text_length} caràcters"
            )
        
        # Verificar que no sigui tot caràcters especials
        if len(text.strip()) > 0 and len(text.split()) < 5:
            errors.append("Text sense paraules vàlides")
        
        return errors
    
    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Valida les metadades"""
        errors = []
        
        if not metadata:
            errors.append("Metadata buida")
            return errors
        
        # Verificar camps obligatoris
        for field in self.required_metadata:
            if field not in metadata or not metadata[field]:
                errors.append(f"Camp obligatori absent: {field}")
        
        return errors
    
    def _check_duplicate(self, document: LlamaDocument) -> Optional[str]:
        """Verifica si el document és un duplicat"""
        file_hash = document.metadata.get('file_hash')

        if not file_hash:
            # intentar altres claus possibles
            file_hash = document.metadata.get('hash') or document.metadata.get('sha256')
        
        if not file_hash:
            return "Hash no disponible per verificar duplicats"
        
        if file_hash in self.seen_hashes:
            return f"Document duplicat (hash: {file_hash[:8]}...)"
        
        self.seen_hashes.add(file_hash)
        return None

    def _normalize_metadata(self, document: LlamaDocument) -> None:
        """Omple camps derivats a partir de variants de metadata.

        - Estableix `filename` a partir de `source_file`, `source`, `source_title` o `title` si cal.
        - Calcula `file_hash` com a SHA256 del text si no existeix.
        """
        md = document.metadata or {}

        # Calcular filename a partir d'aliases
        if not md.get('filename'):
            for key in ('source_title', 'title'):
                val = md.get(key)
                if val:
                    md['filename'] = val
                    break

        # Calcular hash a partir del text si no existeix
        if not md.get('file_hash'):
            try:
                text = document.text or ''
                h = hashlib.sha256(text.encode('utf-8')).hexdigest()
                md['file_hash'] = h
            except Exception:
                # no fallar si no es pot codificar
                pass

        # Assignar de nou (LlamaDocument.metadata normalment és dict mutable)
        document.metadata = md
    
    def reset_duplicates_check(self):
        """Reinicia el control de duplicats"""
        self.seen_hashes.clear()
        logger.info("Control de duplicats reiniciat")