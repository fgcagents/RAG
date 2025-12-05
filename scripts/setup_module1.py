#!/usr/bin/env python3
# scripts/setup_module1.py
"""
Script per configurar i provar el Mòdul 1: Data Ingestion Pipeline
"""

import sys
from pathlib import Path
import logging

# Afegir el directori arrel al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.ingestion_config import setup_directories, config
from modules.ingestion import (
    DocumentLoader,
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor,
    DocumentValidator
)

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(config.LOG_FILE) if config.LOG_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Configura l'entorn inicial"""
    print("\n" + "="*70)
    print("  CONFIGURACIÓ DEL MÒDUL 1: DATA INGESTION PIPELINE")
    print("="*70 + "\n")
    
    print("📁 Creant estructura de directoris...")
    setup_directories()
    
    print("\n📋 Configuració actual:")
    print(f"  • Directori raw: {config.RAW_DATA_DIR}")
    print(f"  • Directori processed: {config.PROCESSED_DATA_DIR}")
    print(f"  • Directori markdown: {config.MARKDOWN_OUTPUT_DIR}")
    print(f"  • Directori imatges: {config.IMAGES_DIR}")
    print(f"  • Log level: {config.LOG_LEVEL}")
    print(f"  • Batch size: {config.BATCH_SIZE}")
    
    return True


def test_components():
    """Testa els components del mòdul"""
    print("\n🧪 Testant components del mòdul...\n")
    
    results = {
        'DocumentLoader': False,
        'PDFToMarkdownConverter': False,
        'TextCleaner': False,
        'MetadataExtractor': False,
        'DocumentValidator': False
    }
    
    # Test 1: DocumentLoader
    print("1️⃣  Testing DocumentLoader...")
    try:
        loader = DocumentLoader()
        stats = loader.get_file_stats(config.RAW_DATA_DIR)
        print(f"   ✓ DocumentLoader funciona correctament")
        print(f"     Fitxers trobats: {stats['total_files']}")
        results['DocumentLoader'] = True
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: PDFToMarkdownConverter
    print("\n2️⃣  Testing PDFToMarkdownConverter...")
    try:
        converter = PDFToMarkdownConverter(
            extract_images=config.PDF_EXTRACT_IMAGES,
            image_path=config.IMAGES_DIR
        )
        print(f"   ✓ PDFToMarkdownConverter funciona correctament")
        results['PDFToMarkdownConverter'] = True
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: TextCleaner
    print("\n3️⃣  Testing TextCleaner...")
    try:
        cleaner = TextCleaner(
            remove_extra_whitespace=config.REMOVE_EXTRA_WHITESPACE,
            normalize_unicode=config.NORMALIZE_UNICODE
        )
        test_text = "Text   amb    espais    excessius\n\n\n\n"
        cleaned = cleaner.clean(test_text)
        print(f"   ✓ TextCleaner funciona correctament")
        print(f"     Original: {len(test_text)} chars → Netejat: {len(cleaned)} chars")
        results['TextCleaner'] = True
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: MetadataExtractor
    print("\n4️⃣  Testing MetadataExtractor...")
    try:
        extractor = MetadataExtractor(
            custom_fields=config.CUSTOM_METADATA_FIELDS
        )
        
        # Crear fitxer de test temporal
        test_file = Path(config.RAW_DATA_DIR) / "test_file.txt"
        test_file.write_text("Contingut de prova")
        
        metadata = extractor.extract_from_file(str(test_file))
        print(f"   ✓ MetadataExtractor funciona correctament")
        print(f"     Camps extrets: {len(metadata)}")
        
        # Netejar
        test_file.unlink()
        results['MetadataExtractor'] = True
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: DocumentValidator
    print("\n5️⃣  Testing DocumentValidator...")
    try:
        from llama_index.core import Document
        
        validator = DocumentValidator(
            min_text_length=config.MIN_TEXT_LENGTH,
            required_metadata=config.REQUIRED_METADATA_FIELDS
        )
        
        # Document vàlid
        valid_doc = Document(
            text="A" * 200,
            metadata={'filename': 'test.txt', 'source': '/test', 'file_type': 'text'}
        )
        
        validator.validate(valid_doc)
        print(f"   ✓ DocumentValidator funciona correctament")
        results['DocumentValidator'] = True
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Resum
    print("\n" + "="*70)
    print("  RESUM DE TESTS")
    print("="*70)
    
    passed = sum(results.values())
    total = len(results)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component}")
    
    print(f"\n{'='*70}")
    print(f"Tests passats: {passed}/{total} ({passed/total*100:.0f}%)")
    print(f"{'='*70}\n")
    
    return passed == total


def create_sample_data():
    """Crea dades de mostra per testing"""
    print("\n📄 Creant fitxers de mostra...\n")
    
    raw_dir = Path(config.RAW_DATA_DIR)
    
    # Crear alguns fitxers de text de mostra
    samples = [
        ("document1.txt", "Aquest és el primer document de prova amb contingut suficient per passar la validació mínima."),
        ("document2.md", "# Document 2\n\nAquest és un document en **Markdown** amb format.\n\n- Item 1\n- Item 2"),
        ("document3.txt", "Document 3 amb contingut en català per testejar la detecció d'idioma i altres funcionalitats del sistema.")
    ]
    
    for filename, content in samples:
        file_path = raw_dir / filename
        file_path.write_text(content, encoding='utf-8')
        print(f"  ✓ Creat: {filename}")
    
    print(f"\n{'='*70}")
    print("  Fitxers de mostra creats correctament")
    print(f"{'='*70}\n")
    
    print("💡 Afegeix els teus propis PDFs a:")
    print(f"   {config.RAW_DATA_DIR}/")
    print("\n   I executa els exemples per processar-los!")


def show_next_steps():
    """Mostra els propers passos"""
    print("\n" + "="*70)
    print("  ✅ MÒDUL 1 CONFIGURAT CORRECTAMENT")
    print("="*70 + "\n")
    
    print("🚀 PROPERS PASSOS:\n")
    print("1. Afegeix documents PDF a:")
    print(f"   {config.RAW_DATA_DIR}/\n")
    
    print("2. Executa els exemples:")
    print("   python examples/module1_example.py\n")
    
    print("3. Revisa els resultats a:")
    print(f"   {config.MARKDOWN_OUTPUT_DIR}/\n")
    
    print("4. Quan estiguis llest, passa al Mòdul 2:")
    print("   Chunking, Embeddings i Vector Store\n")
    
    print("="*70 + "\n")


def main():
    """Funció principal"""
    try:
        # Setup inicial
        if not setup_environment():
            print("❌ Error durant el setup")
            return 1
        
        # Testejar components
        if not test_components():
            print("\n⚠️  Alguns tests han fallat. Revisa els errors.")
            response = input("\nVols continuar igualment? (s/n): ")
            if response.lower() != 's':
                return 1
        
        # Crear dades de mostra
        create_sample_data()
        
        # Mostrar propers passos
        show_next_steps()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Procés interromput per l'usuari")
        return 1
    except Exception as e:
        print(f"\n❌ Error inesperat: {e}")
        logger.exception("Error durant el setup")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)