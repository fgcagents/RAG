# examples/module1_example.py
"""
Exemple complet d'ús del Mòdul 1: Data Ingestion Pipeline
"""

from pathlib import Path
from modules.ingestion import (
    DocumentLoader,
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor,
    DocumentValidator
)
from llama_index.core import Document
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_pdf_conversion():
    """
    Exemple 1: Conversió bàsica de PDFs a Markdown
    """
    print("\n" + "="*60)
    print("EXEMPLE 1: Conversió bàsica PDF → Markdown")
    print("="*60)
    
    # Inicialitzar convertidor
    converter = PDFToMarkdownConverter(
        extract_images=True,
        image_path="data/images",
        dpi=150
    )
    
    # Convertir un PDF individual
    pdf_path = "data/raw/document_exemple.pdf"
    
    try:
        markdown_text = converter.convert_file(pdf_path)
        print(f"✓ PDF convertit: {len(markdown_text)} caràcters")
        print(f"Previsualització:\n{markdown_text[:500]}...")
        
    except FileNotFoundError:
        print(f"⚠️  Fitxer no trobat: {pdf_path}")
        print("   Crea aquest fitxer o canvia el path per provar")


def example_2_batch_conversion():
    """
    Exemple 2: Conversió en batch de directori complet
    """
    print("\n" + "="*60)
    print("EXEMPLE 2: Conversió en batch de directori")
    print("="*60)
    
    converter = PDFToMarkdownConverter(
        extract_images=True,
        image_path="data/images"
    )
    
    input_dir = "data/raw/pdfs"
    output_dir = "data/processed/markdown"
    
    # Crear directoris si no existeixen
    Path(input_dir).mkdir(parents=True, exist_ok=True)
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        results = converter.convert_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            add_metadata=True
        )
        
        print(f"✓ Convertits {len(results)} PDFs")
        for pdf_name, md_path in results.items():
            print(f"  • {pdf_name} → {md_path}")
            
    except Exception as e:
        print(f"⚠️  Error: {e}")


def example_3_complete_pipeline():
    """
    Exemple 3: Pipeline complet d'ingestió
    """
    print("\n" + "="*60)
    print("EXEMPLE 3: Pipeline complet d'ingestió")
    print("="*60)
    
    # 1. Configurar components
    loader = DocumentLoader()
    converter = PDFToMarkdownConverter(extract_images=True, image_path="data/images")
    cleaner = TextCleaner(
        remove_extra_whitespace=True,
        normalize_unicode=True,
        min_line_length=3
    )
    metadata_extractor = MetadataExtractor(
        custom_fields={
            'department': 'Gestió Documental',
            'category': 'Documentació Tècnica',
            'language': 'ca'
        }
    )
    validator = DocumentValidator(
        min_text_length=100,
        required_metadata=['filename', 'source'],
        check_duplicates=True
    )
    
    # 2. Processar PDFs
    pdf_dir = "data/raw/pdfs"
    processed_docs = []
    
    # Crear directori si no existeix
    Path(pdf_dir).mkdir(parents=True, exist_ok=True)
    
    for pdf_file in Path(pdf_dir).glob("*.pdf"):
        try:
            print(f"\n📄 Processant: {pdf_file.name}")
            
            # Pas 1: Convertir PDF a Markdown
            print("  1. Convertint PDF → Markdown...")
            markdown_text = converter.convert_file(str(pdf_file))
            
            # Pas 2: Netejar text
            print("  2. Netejant text...")
            clean_text = cleaner.clean(markdown_text)
            
            # Pas 3: Extreure metadata
            print("  3. Extraient metadata...")
            file_metadata = metadata_extractor.extract_from_file(str(pdf_file))
            text_metadata = metadata_extractor.extract_from_text(clean_text)
            metadata = {**file_metadata, **text_metadata}
            
            # Pas 4: Crear document
            document = Document(
                text=clean_text,
                metadata=metadata
            )
            
            # Pas 5: Validar
            print("  4. Validant document...")
            validator.validate(document)
            
            processed_docs.append(document)
            print(f"  ✓ Document processat correctament")
            print(f"    - Text: {len(clean_text)} caràcters")
            print(f"    - Paraules: {metadata['word_count']}")
            print(f"    - Idioma: {metadata.get('language', 'unknown')}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # Resum final
    print(f"\n{'='*60}")
    print(f"RESUM DEL PROCESSAMENT")
    print(f"{'='*60}")
    print(f"Documents processats correctament: {len(processed_docs)}")
    
    if processed_docs:
        total_chars = sum(len(doc.text) for doc in processed_docs)
        total_words = sum(doc.metadata.get('word_count', 0) for doc in processed_docs)
        print(f"Total caràcters: {total_chars:,}")
        print(f"Total paraules: {total_words:,}")
    
    return processed_docs


def example_4_load_and_validate():
    """
    Exemple 4: Carregar documents existents i validar
    """
    print("\n" + "="*60)
    print("EXEMPLE 4: Carregar i validar documents")
    print("="*60)
    
    loader = DocumentLoader()
    validator = DocumentValidator(
        min_text_length=50,
        required_metadata=['filename']
    )
    
    markdown_dir = "data/processed/markdown"
    
    # Crear directori si no existeix
    Path(markdown_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # Carregar documents
        print(f"📂 Carregant documents de: {markdown_dir}")
        documents = loader.load_directory(
            directory=markdown_dir,
            required_exts=['.md'],
            recursive=True
        )
        
        print(f"✓ Carregats {len(documents)} documents")
        
        # Validar en batch
        print("\n🔍 Validant documents...")
        results = validator.validate_batch(documents, stop_on_error=False)
        
        print(f"\n{'='*60}")
        print(f"RESULTATS DE VALIDACIÓ")
        print(f"{'='*60}")
        print(f"Total documents: {results['total']}")
        print(f"Vàlids: {results['valid']} ({results['valid']/results['total']*100:.1f}%)")
        print(f"Invàlids: {results['invalid']}")
        
        if results['errors']:
            print(f"\n❌ Errors trobats:")
            for error in results['errors']:
                print(f"  • {error['filename']}: {error['error']}")
        
    except Exception as e:
        print(f"⚠️  Error: {e}")


def example_5_metadata_enrichment():
    """
    Exemple 5: Enriquiment avançat de metadata
    """
    print("\n" + "="*60)
    print("EXEMPLE 5: Enriquiment de metadata")
    print("="*60)
    
    extractor = MetadataExtractor(
        custom_fields={
            'project': 'Sistema RAG',
            'version': '1.0',
            'owner': 'Equip Gestió Documental'
        }
    )
    
    # Simular un document
    test_file = "data/raw/exemple.pdf"
    
    # Crear fitxer de prova si no existeix
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    if not Path(test_file).exists():
        Path(test_file).write_text("Document de prova")
    
    try:
        # Extreure metadata base
        base_metadata = extractor.extract_from_file(test_file)
        
        # Afegir metadata personalitzada
        custom_data = {
            'department': 'IT',
            'confidentiality': 'Internal',
            'tags': ['documentació', 'rag', 'prova'],
            'reviewed_by': 'Joan Garcia',
            'approval_date': '2024-12-04'
        }
        
        enriched_metadata = extractor.enrich_metadata(base_metadata, custom_data)
        
        print("📋 Metadata extraïda i enriquida:")
        print("-" * 60)
        for key, value in enriched_metadata.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"⚠️  Error: {e}")


def example_6_document_stats():
    """
    Exemple 6: Estadístiques de documents
    """
    print("\n" + "="*60)
    print("EXEMPLE 6: Estadístiques de documents")
    print("="*60)
    
    loader = DocumentLoader()
    
    directories = [
        "data/raw/pdfs",
        "data/processed/markdown"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        print(f"\n📊 Estadístiques de: {directory}")
        print("-" * 60)
        
        try:
            stats = loader.get_file_stats(directory)
            
            print(f"Total fitxers: {stats['total_files']}")
            print(f"Mida total: {stats['total_size_mb']} MB")
            print(f"\nPer extensió:")
            for ext, count in stats['by_extension'].items():
                print(f"  {ext}: {count} fitxers")
                
        except Exception as e:
            print(f"⚠️  Error: {e}")


if __name__ == "__main__":
    """
    Executar tots els exemples
    """
    print("\n" + "🚀 "+"="*58)
    print("   EXEMPLES DEL MÒDUL 1: DATA INGESTION PIPELINE")
    print("="*60 + "\n")
    
    # Executar exemples
    example_1_basic_pdf_conversion()
    example_2_batch_conversion()
    example_3_complete_pipeline()
    example_4_load_and_validate()
    example_5_metadata_enrichment()
    example_6_document_stats()
    
    print("\n" + "="*60)
    print("✅ EXEMPLES COMPLETATS")
    print("="*60 + "\n")
    
    print("💡 PROPERS PASSOS:")
    print("  1. Afegeix els teus PDFs a data/raw/pdfs/")
    print("  2. Executa: python examples/module1_example.py")
    print("  3. Revisa els Markdown generats a data/processed/markdown/")
    print("  4. Passa al Mòdul 2: Processing & Indexing")
    print()