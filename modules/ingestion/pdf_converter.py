# modules/ingestion/pdf_converter.py
"""
1.2 PDF to Markdown Converter
Conversió especialitzada de PDFs a Markdown
"""

from pathlib import Path
from typing import Optional, Dict, Any
import pymupdf4llm
import logging

logger = logging.getLogger(__name__)


class PDFToMarkdownConverter:
    """
    Converteix documents PDF a format Markdown mantenint l'estructura
    """
    
    def __init__(
        self,
        extract_images: bool = False,
        image_path: Optional[str] = None,
        dpi: int = 150
    ):
        """
        Inicialitza el convertidor
        
        Args:
            extract_images: Extreure imatges del PDF
            image_path: Directori per guardar imatges
            dpi: Resolució per imatges
        """
        self.extract_images = extract_images
        self.image_path = Path(image_path) if image_path else None
        self.dpi = dpi
        
        if self.extract_images and self.image_path:
            self.image_path.mkdir(parents=True, exist_ok=True)
    
    def convert_file(
        self, 
        pdf_path: str,
        pages: Optional[List[int]] = None
    ) -> str:
        """
        Converteix un fitxer PDF a Markdown
        
        Args:
            pdf_path: Path del fitxer PDF
            pages: Llista de pàgines específiques (None = totes)
            
        Returns:
            Text en format Markdown
        """
        try:
            path = Path(pdf_path)
            if not path.exists():
                raise FileNotFoundError(f"PDF no trobat: {pdf_path}")
            
            logger.info(f"Convertint PDF: {pdf_path}")
            
            # Opcions de conversió
            kwargs = {
                'write_images': self.extract_images,
                'image_path': str(self.image_path) if self.image_path else None,
                'dpi': self.dpi
            }
            
            if pages:
                kwargs['pages'] = pages
            
            # Convertir amb PyMuPDF4LLM
            markdown_text = pymupdf4llm.to_markdown(str(path), **kwargs)
            
            logger.info(f"PDF convertit: {len(markdown_text)} caràcters")
            
            return markdown_text
            
        except Exception as e:
            logger.error(f"Error convertint PDF {pdf_path}: {e}")
            raise
    
    def convert_directory(
        self,
        input_dir: str,
        output_dir: str,
        add_metadata: bool = True
    ) -> Dict[str, str]:
        """
        Converteix tots els PDFs d'un directori
        
        Args:
            input_dir: Directori amb PDFs
            output_dir: Directori per Markdowns
            add_metadata: Afegir metadata al principi del MD
            
        Returns:
            Diccionari {pdf_name: markdown_path}
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        pdf_files = list(input_path.glob("*.pdf"))
        
        logger.info(f"Convertint {len(pdf_files)} PDFs de {input_dir}")
        
        for pdf_file in pdf_files:
            try:
                # Convertir
                markdown_text = self.convert_file(str(pdf_file))
                
                # Preparar output
                output_file = output_path / f"{pdf_file.stem}.md"
                
                # Afegir metadata si cal
                if add_metadata:
                    metadata_header = self._create_metadata_header(pdf_file)
                    markdown_text = f"{metadata_header}\n\n{markdown_text}"
                
                # Guardar
                output_file.write_text(markdown_text, encoding='utf-8')
                results[pdf_file.name] = str(output_file)
                
                logger.info(f"✓ Convertit: {pdf_file.name} → {output_file.name}")
                
            except Exception as e:
                logger.error(f"✗ Error amb {pdf_file.name}: {e}")
                continue
        
        logger.info(f"Conversió completada: {len(results)}/{len(pdf_files)} PDFs")
        return results
    
    def _create_metadata_header(self, pdf_path: Path) -> str:
        """Crea capçalera amb metadata del PDF"""
        stats = pdf_path.stat()
        
        header = f"""---
title: {pdf_path.stem}
source_file: {pdf_path.name}
source_format: PDF
created_at: {stats.st_ctime}
modified_at: {stats.st_mtime}
size_bytes: {stats.st_size}
---"""
        return header