#!/usr/bin/env python3
# main.py
"""
Sistema Principal de Pruebas - Módulo 1: Data Ingestion Pipeline
Arquitectura RAG Empresarial - MIT-Grade Design
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

# Configuración de paths
sys.path.insert(0, str(Path(__file__).parent))

# Imports del módulo
from modules.ingestion import (
    DocumentLoader,
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor,
    DocumentValidator
)
from modules.ingestion.docstore import (
    DocumentStoreManager,
    process_and_store_documents
)
from llama_index.core import Document
from config.ingestion_config import config, setup_directories

# Configuración de logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/main_execution.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class IngestionSystemTester:
    """
    Sistema profesional de testing para el pipeline de ingestión
    """
    
    def __init__(self):
        """Inicializa el sistema de testing"""
        self.docstore = None
        self.components = {}
        self.test_results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': []
        }
        
    def initialize_system(self):
        """Inicializa todos los componentes del sistema"""
        logger.info("="*80)
        logger.info("INICIALIZANDO SISTEMA DE INGESTION RAG")
        logger.info("="*80)
        
        try:
            # 1. Setup de directorios
            logger.info("📁 Configurando estructura de directorios...")
            setup_directories()
            
            # 2. Inicializar componentes
            logger.info("🔧 Inicializando componentes del pipeline...")
            self.components = {
                'loader': DocumentLoader(),
                'converter': PDFToMarkdownConverter(
                    extract_images=config.PDF_EXTRACT_IMAGES,
                    image_path=config.IMAGES_DIR,
                    dpi=config.PDF_IMAGE_DPI
                ),
                'cleaner': TextCleaner(
                    remove_extra_whitespace=config.REMOVE_EXTRA_WHITESPACE,
                    normalize_unicode=config.NORMALIZE_UNICODE,
                    min_line_length=config.MIN_LINE_LENGTH
                ),
                'extractor': MetadataExtractor(
                    custom_fields=config.CUSTOM_METADATA_FIELDS
                ),
                'validator': DocumentValidator(
                    min_text_length=config.MIN_TEXT_LENGTH,
                    max_text_length=config.MAX_TEXT_LENGTH,
                    required_metadata=config.REQUIRED_METADATA_FIELDS,
                    check_duplicates=config.CHECK_DUPLICATES
                )
            }
            
            # 3. Inicializar DocStore
            logger.info("💾 Inicializando Document Store...")
            self.docstore = DocumentStoreManager(
                backend='simple',
                persist_path='data/docstore'
            )
            
            logger.info("✅ Sistema inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando sistema: {e}")
            return False
    
    def test_01_document_loader(self):
        """TEST 01: Document Loader"""
        logger.info("\n" + "="*80)
        logger.info("TEST 01: DOCUMENT LOADER")
        logger.info("="*80)
        
        try:
            loader = self.components['loader']
            
            # Test: Estadísticas de directorio
            logger.info("📊 Obteniendo estadísticas de archivos...")
            stats = loader.get_file_stats(config.RAW_DATA_DIR)
            
            logger.info(f"✓ Total archivos: {stats['total_files']}")
            logger.info(f"✓ Tamaño total: {stats['total_size_mb']:.2f} MB")
            logger.info(f"✓ Por extensión: {stats['by_extension']}")
            
            self._record_test_pass("Document Loader")
            return True
            
        except Exception as e:
            self._record_test_fail("Document Loader", str(e))
            return False
    
    def test_02_pdf_conversion(self):
        """TEST 02: PDF to Markdown Conversion"""
        logger.info("\n" + "="*80)
        logger.info("TEST 02: PDF TO MARKDOWN CONVERSION")
        logger.info("="*80)
        
        try:
            converter = self.components['converter']
            
            # Buscar PDFs disponibles
            pdf_dir = Path(config.RAW_DATA_DIR)
            pdf_files = list(pdf_dir.glob("**/*.pdf"))
            
            if not pdf_files:
                logger.warning("⚠️  No se encontraron PDFs para convertir")
                logger.info("💡 Crea archivos PDF en: data/raw/")
                self._record_test_pass("PDF Conversion (skip - no files)")
                return True
            
            logger.info(f"📄 PDFs encontrados: {len(pdf_files)}")
            
            # Asegurar que existe el directorio de salida
            markdown_dir = Path(config.MARKDOWN_OUTPUT_DIR)
            markdown_dir.mkdir(parents=True, exist_ok=True)
            
            # Convertir primer PDF como prueba
            test_pdf = pdf_files[0]
            logger.info(f"🔄 Convirtiendo: {test_pdf.name}")
            
            markdown_text = converter.convert_file(str(test_pdf))
            
            logger.info(f"✓ Conversión exitosa")
            logger.info(f"  - Caracteres: {len(markdown_text):,}")
            logger.info(f"  - Palabras: ~{len(markdown_text.split()):,}")
            logger.info(f"  - Preview: {markdown_text[:200]}...")
            
            # GUARDAR EL MARKDOWN A DISCO
            output_file = markdown_dir / f"{test_pdf.stem}.md"
            output_file.write_text(markdown_text, encoding='utf-8')
            logger.info(f"💾 Markdown guardado en: {output_file}")
            
            self._record_test_pass("PDF Conversion")
            return True
            
        except Exception as e:
            self._record_test_fail("PDF Conversion", str(e))
            return False
    
    def test_03_text_cleaning(self):
        """TEST 03: Text Cleaning"""
        logger.info("\n" + "="*80)
        logger.info("TEST 03: TEXT CLEANING")
        logger.info("="*80)
        
        try:
            cleaner = self.components['cleaner']
            
            # Texto de prueba con problemas comunes
            dirty_text = """
            Este    es    un    texto    con    espacios    múltiples.
            
            
            
            
            Líneas vacías excesivas.
            a
            b
            Líneas demasiado cortas.
            
            Texto normal aquí con    espacios    irregulares.
            """
            
            logger.info("🧹 Limpiando texto de prueba...")
            logger.info(f"  - Original: {len(dirty_text)} caracteres")
            
            clean_text = cleaner.clean(dirty_text)
            
            logger.info(f"✓ Texto limpio: {len(clean_text)} caracteres")
            logger.info(f"  - Reducción: {len(dirty_text) - len(clean_text)} caracteres")
            logger.info(f"  - Resultado:\n{clean_text}")
            
            self._record_test_pass("Text Cleaning")
            return True
            
        except Exception as e:
            self._record_test_fail("Text Cleaning", str(e))
            return False
    
    def test_04_metadata_extraction(self):
        """TEST 04: Metadata Extraction"""
        logger.info("\n" + "="*80)
        logger.info("TEST 04: METADATA EXTRACTION")
        logger.info("="*80)
        
        try:
            extractor = self.components['extractor']
            
            # Crear archivo de prueba
            test_file = Path(config.RAW_DATA_DIR) / "test_metadata.txt"
            test_content = "Este es un documento de prueba para extracción de metadata."
            test_file.write_text(test_content, encoding='utf-8')
            
            logger.info(f"📋 Extrayendo metadata de: {test_file.name}")
            
            # Extraer metadata del archivo
            file_metadata = extractor.extract_from_file(str(test_file))
            
            # Extraer metadata del texto
            text_metadata = extractor.extract_from_text(test_content)
            
            logger.info("✓ Metadata extraída:")
            logger.info(f"  Archivo:")
            for key, value in file_metadata.items():
                logger.info(f"    - {key}: {value}")
            
            logger.info(f"  Texto:")
            for key, value in text_metadata.items():
                logger.info(f"    - {key}: {value}")
            
            # Cleanup
            test_file.unlink()
            
            self._record_test_pass("Metadata Extraction")
            return True
            
        except Exception as e:
            self._record_test_fail("Metadata Extraction", str(e))
            return False
    
    def test_05_document_validation(self):
        """TEST 05: Document Validation"""
        logger.info("\n" + "="*80)
        logger.info("TEST 05: DOCUMENT VALIDATION")
        logger.info("="*80)
        
        try:
            validator = self.components['validator']
            
            # Documentos de prueba
            docs = [
                Document(
                    text="A" * 150,  # Válido
                    metadata={'filename': 'doc1.txt', 'source': '/path/doc1.txt', 'file_type': 'text'}
                ),
                Document(
                    text="Corto",  # Inválido - muy corto
                    metadata={'filename': 'doc2.txt', 'source': '/path/doc2.txt', 'file_type': 'text'}
                ),
                Document(
                    text="B" * 200,  # Válido
                    metadata={'filename': 'doc3.txt', 'source': '/path/doc3.txt', 'file_type': 'text'}
                )
            ]
            
            logger.info(f"🔍 Validando {len(docs)} documentos...")
            
            results = validator.validate_batch(docs, stop_on_error=False)
            
            logger.info("✓ Resultados de validación:")
            logger.info(f"  - Total: {results['total']}")
            logger.info(f"  - Válidos: {results['valid']}")
            logger.info(f"  - Inválidos: {results['invalid']}")
            
            if results['errors']:
                logger.info("  - Errores:")
                for error in results['errors']:
                    logger.info(f"    • {error['filename']}: {error['error']}")
            
            self._record_test_pass("Document Validation")
            return True
            
        except Exception as e:
            self._record_test_fail("Document Validation", str(e))
            return False
    
    def test_06_docstore_operations(self):
        """TEST 06: DocStore Operations"""
        logger.info("\n" + "="*80)
        logger.info("TEST 06: DOCSTORE OPERATIONS")
        logger.info("="*80)
        
        try:
            # Crear documentos de prueba
            test_docs = [
                Document(
                    doc_id="test_doc_1",
                    text="Documento de prueba 1 para DocStore",
                    metadata={
                        'filename': 'test1.txt',
                        'source': 'test',
                        'file_type': 'text',
                        'department': 'IT'
                    }
                ),
                Document(
                    doc_id="test_doc_2",
                    text="Documento de prueba 2 para DocStore",
                    metadata={
                        'filename': 'test2.txt',
                        'source': 'test',
                        'file_type': 'text',
                        'department': 'Legal'
                    }
                )
            ]
            
            logger.info(f"💾 Guardando {len(test_docs)} documentos...")
            results = self.docstore.add_documents(test_docs)
            
            logger.info(f"✓ Documentos guardados:")
            logger.info(f"  - Añadidos: {results['added']}")
            logger.info(f"  - Actualizados: {results['updated']}")
            logger.info(f"  - Saltados: {results['skipped']}")
            
            # Recuperar documentos
            logger.info("\n📤 Recuperando documentos...")
            all_docs = self.docstore.get_all_documents()
            logger.info(f"✓ Documentos recuperados: {len(all_docs)}")
            
            # Buscar por metadata
            logger.info("\n🔍 Buscando por metadata (department='IT')...")
            it_docs = self.docstore.search_by_metadata({'department': 'IT'})
            logger.info(f"✓ Documentos encontrados: {len(it_docs)}")
            
            # Estadísticas
            logger.info("\n📊 Estadísticas del DocStore:")
            stats = self.docstore.get_statistics()
            for key, value in stats.items():
                logger.info(f"  - {key}: {value}")
            
            self._record_test_pass("DocStore Operations")
            return True
            
        except Exception as e:
            self._record_test_fail("DocStore Operations", str(e))
            return False
    
    def test_08_batch_pdf_conversion(self):
        """TEST 08: Batch PDF Conversion"""
        logger.info("\n" + "="*80)
        logger.info("TEST 08: BATCH PDF CONVERSION")
        logger.info("="*80)
        
        try:
            converter = self.components['converter']
            
            # Buscar PDFs
            pdf_dir = Path(config.RAW_DATA_DIR)
            pdf_files = list(pdf_dir.glob("**/*.pdf"))
            
            if not pdf_files:
                logger.warning("⚠️  No se encontraron PDFs para convertir")
                logger.info("💡 Añade PDFs a: data/raw/")
                self._record_test_pass("Batch PDF Conversion (skip - no files)")
                return True
            
            logger.info(f"📂 PDFs encontrados: {len(pdf_files)}")
            logger.info(f"🔄 Convirtiendo TODOS los PDFs a Markdown...")
            
            # Conversión en batch
            results = converter.convert_directory(
                input_dir=config.RAW_DATA_DIR,
                output_dir=config.MARKDOWN_OUTPUT_DIR,
                add_metadata=True
            )
            
            logger.info(f"✅ Conversión batch completada:")
            logger.info(f"  - Total PDFs: {len(pdf_files)}")
            logger.info(f"  - Convertidos: {len(results)}")
            logger.info(f"  - Tasa de éxito: {len(results)/len(pdf_files)*100:.1f}%")
            
            # Listar archivos generados
            logger.info(f"\n📄 Archivos Markdown generados:")
            for pdf_name, md_path in results.items():
                md_file = Path(md_path)
                size_kb = md_file.stat().st_size / 1024
                logger.info(f"  ✓ {pdf_name} → {md_file.name} ({size_kb:.1f} KB)")
            
            self._record_test_pass("Batch PDF Conversion")
            return True
            
        except Exception as e:
            self._record_test_fail("Batch PDF Conversion", str(e))
            return False
    
    def test_07_complete_pipeline(self):
        """TEST 07: Complete Pipeline Integration"""
        logger.info("\n" + "="*80)
        logger.info("TEST 07: COMPLETE PIPELINE INTEGRATION")
        logger.info("="*80)
        
        try:
            # Buscar PDFs
            pdf_dir = Path(config.RAW_DATA_DIR)
            pdf_files = list(pdf_dir.glob("**/*.pdf"))
            
            if not pdf_files:
                logger.info("⚠️  No hay PDFs para procesar")
                logger.info("💡 Añade PDFs a: data/raw/")
                self._record_test_pass("Complete Pipeline (skip - no files)")
                return True
            
            logger.info(f"📂 Procesando {len(pdf_files)} PDFs con pipeline completo...")
            
            processed_count = 0
            for pdf_file in pdf_files[:3]:  # Limitar a 3 para testing
                try:
                    logger.info(f"\n🔄 Procesando: {pdf_file.name}")
                    
                    # Paso 1: Convertir
                    markdown = self.components['converter'].convert_file(str(pdf_file))
                    logger.info(f"  ✓ Conversión: {len(markdown):,} chars")
                    
                    # Paso 2: Limpiar
                    clean_text = self.components['cleaner'].clean(markdown)
                    logger.info(f"  ✓ Limpieza: {len(clean_text):,} chars")
                    
                    # Paso 3: Metadata
                    file_meta = self.components['extractor'].extract_from_file(str(pdf_file))
                    text_meta = self.components['extractor'].extract_from_text(clean_text)
                    metadata = {**file_meta, **text_meta}
                    logger.info(f"  ✓ Metadata: {len(metadata)} campos")
                    
                    # Paso 4: Crear documento
                    doc = Document(text=clean_text, metadata=metadata)
                    
                    # Paso 5: Validar
                    self.components['validator'].validate(doc)
                    logger.info(f"  ✓ Validación: OK")
                    
                    # Paso 6: Guardar
                    self.docstore.add_documents([doc])
                    logger.info(f"  ✓ Almacenado: OK")
                    
                    processed_count += 1
                    
                except Exception as e:
                    logger.error(f"  ✗ Error: {e}")
                    continue
            
            logger.info(f"\n✅ Pipeline completado: {processed_count}/{len(pdf_files[:3])} documentos")
            
            self._record_test_pass("Complete Pipeline")
            return True
            
        except Exception as e:
            self._record_test_fail("Complete Pipeline", str(e))
            return False
    
    def _record_test_pass(self, test_name: str):
        """Registra un test exitoso"""
        self.test_results['total_tests'] += 1
        self.test_results['passed'] += 1
        logger.info(f"✅ TEST PASSED: {test_name}")
    
    def _record_test_fail(self, test_name: str, error: str):
        """Registra un test fallido"""
        self.test_results['total_tests'] += 1
        self.test_results['failed'] += 1
        self.test_results['errors'].append({
            'test': test_name,
            'error': error
        })
        logger.error(f"❌ TEST FAILED: {test_name} - {error}")
    
    def print_final_report(self):
        """Imprime reporte final de tests"""
        logger.info("\n" + "="*80)
        logger.info("REPORTE FINAL DE PRUEBAS")
        logger.info("="*80)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        
        logger.info(f"\n📊 ESTADÍSTICAS:")
        logger.info(f"  • Total tests ejecutados: {total}")
        logger.info(f"  • Tests exitosos: {passed} ({passed/total*100:.1f}%)")
        logger.info(f"  • Tests fallidos: {failed} ({failed/total*100:.1f}%)")
        
        if self.test_results['errors']:
            logger.info(f"\n❌ ERRORES DETECTADOS:")
            for error in self.test_results['errors']:
                logger.info(f"  • {error['test']}: {error['error']}")
        
        # Estado del DocStore
        if self.docstore:
            logger.info(f"\n💾 ESTADO DEL DOCSTORE:")
            stats = self.docstore.get_statistics()
            logger.info(f"  • Total documentos: {stats['total_documents']}")
            logger.info(f"  • Total caracteres: {stats['total_chars']:,}")
            logger.info(f"  • Promedio chars/doc: {stats['avg_chars']:,}")
        
        logger.info("\n" + "="*80)
        
        if failed == 0:
            logger.info("✅ TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        else:
            logger.warning("⚠️  ALGUNOS TESTS FALLARON - REVISAR ERRORES")
        
        logger.info("="*80 + "\n")


def interactive_menu(tester: IngestionSystemTester):
    """Menú interactivo para ejecutar tests"""
    while True:
        print("\n" + "="*80)
        print("SISTEMA DE PRUEBAS - MÓDULO 1: DATA INGESTION PIPELINE")
        print("="*80)
        print("\nOpciones disponibles:")
        print("  1. Ejecutar TODOS los tests")
        print("  2. Test 01: Document Loader")
        print("  3. Test 02: PDF Conversion (single)")
        print("  4. Test 03: Text Cleaning")
        print("  5. Test 04: Metadata Extraction")
        print("  6. Test 05: Document Validation")
        print("  7. Test 06: DocStore Operations")
        print("  8. Test 07: Complete Pipeline")
        print("  9. Test 08: Batch PDF Conversion (ALL PDFs)")
        print(" 10. Ver estadísticas DocStore")
        print(" 11. Ver archivos Markdown generados")
        print("  0. Salir")
        print()
        
        choice = input("Selecciona una opción: ").strip()
        
        if choice == '1':
            logger.info("\n🚀 Ejecutando TODOS los tests...\n")
            tester.test_01_document_loader()
            tester.test_02_pdf_conversion()
            tester.test_03_text_cleaning()
            tester.test_04_metadata_extraction()
            tester.test_05_document_validation()
            tester.test_06_docstore_operations()
            tester.test_07_complete_pipeline()
            tester.test_08_batch_pdf_conversion()
            tester.print_final_report()
            
        elif choice == '2':
            tester.test_01_document_loader()
        elif choice == '3':
            tester.test_02_pdf_conversion()
        elif choice == '4':
            tester.test_03_text_cleaning()
        elif choice == '5':
            tester.test_04_metadata_extraction()
        elif choice == '6':
            tester.test_05_document_validation()
        elif choice == '7':
            tester.test_06_docstore_operations()
        elif choice == '8':
            tester.test_07_complete_pipeline()
        elif choice == '9':
            tester.test_08_batch_pdf_conversion()
        elif choice == '10':
            if tester.docstore:
                stats = tester.docstore.get_statistics()
                print("\n📊 ESTADÍSTICAS DOCSTORE:")
                for key, value in stats.items():
                    print(f"  • {key}: {value}")
            else:
                print("⚠️  DocStore no inicializado")
        elif choice == '11':
            markdown_dir = Path(config.MARKDOWN_OUTPUT_DIR)
            if markdown_dir.exists():
                md_files = list(markdown_dir.glob("*.md"))
                if md_files:
                    print(f"\n📄 ARCHIVOS MARKDOWN GENERADOS ({len(md_files)}):")
                    for md_file in sorted(md_files):
                        size_kb = md_file.stat().st_size / 1024
                        mod_time = datetime.fromtimestamp(md_file.stat().st_mtime)
                        print(f"  ✓ {md_file.name}")
                        print(f"    - Tamaño: {size_kb:.1f} KB")
                        print(f"    - Modificado: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print("⚠️  No hay archivos Markdown generados")
                    print(f"💡 Ejecuta la opción 9 para convertir PDFs")
            else:
                print(f"⚠️  Directorio no existe: {markdown_dir}")
        elif choice == '0':
            print("\n👋 Saliendo del sistema de pruebas...")
            break
        else:
            print("❌ Opción no válida")


def main():
    """Función principal"""
    print("\n" + "🚀 " + "="*78)
    print("   SISTEMA DE PRUEBAS - MÓDULO 1: DATA INGESTION PIPELINE")
    print("   Arquitectura RAG Empresarial - MIT-Grade Design")
    print("="*80 + "\n")
    
    # Crear instancia del tester
    tester = IngestionSystemTester()
    
    # Inicializar sistema
    if not tester.initialize_system():
        logger.error("❌ Fallo en la inicialización del sistema")
        return 1
    
    # Preguntar modo de ejecución
    print("\nModos de ejecución:")
    print("  1. Interactivo (menú)")
    print("  2. Automático (todos los tests)")
    
    mode = input("\nSelecciona modo (1/2): ").strip()
    
    if mode == '1':
        interactive_menu(tester)
    else:
        logger.info("\n🚀 Ejecutando modo automático...\n")
        tester.test_01_document_loader()
        tester.test_02_pdf_conversion()
        tester.test_03_text_cleaning()
        tester.test_04_metadata_extraction()
        tester.test_05_document_validation()
        tester.test_06_docstore_operations()
        tester.test_07_complete_pipeline()
        tester.print_final_report()
    
    print("\n✅ Sistema de pruebas finalizado\n")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        logger.exception("❌ Error crítico en el sistema")
        sys.exit(1)