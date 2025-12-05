# examples/docstore_example.py
"""
Exemple d'ús del DocumentStore per persistència
"""

from pathlib import Path
from modules.ingestion.docstore import (
    DocumentStoreManager,
    process_and_store_documents
)
from modules.ingestion import (
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor
)
from llama_index.core import Document
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_1_basic_persistence():
    """
    Exemple 1: Persistència bàsica amb SimpleDocumentStore
    """
    print("\n" + "="*70)
    print("EXEMPLE 1: Persistència bàsica")
    print("="*70 + "\n")
    
    # Crear docstore
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Crear documents de prova
    docs = [
        Document(
            text="Aquest és el primer document de prova.",
            metadata={'filename': 'doc1.txt', 'category': 'test'}
        ),
        Document(
            text="Segon document amb més contingut per testejar.",
            metadata={'filename': 'doc2.txt', 'category': 'test'}
        )
    ]
    
    # Guardar
    print("📥 Guardant documents...")
    results = docstore.add_documents(docs)
    print(f"✓ Resultats: {results}")
    
    # Recuperar
    print("\n📤 Recuperant documents...")
    all_docs = docstore.get_all_documents()
    print(f"✓ Documents recuperats: {len(all_docs)}")
    
    for doc in all_docs:
        print(f"  • {doc.metadata['filename']}: {len(doc.text)} chars")
    
    # Estadístiques
    print("\n📊 Estadístiques:")
    stats = docstore.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")


def example_2_complete_pipeline():
    """
    Exemple 2: Pipeline complet amb persistència
    """
    print("\n" + "="*70)
    print("EXEMPLE 2: Pipeline complet PDF → DocStore")
    print("="*70 + "\n")
    
    # Crear directoris
    pdf_dir = Path("data/raw/pdfs")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicialitzar docstore
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Processar i guardar
    print(f"📂 Processant PDFs de: {pdf_dir}")
    results = process_and_store_documents(
        pdf_dir=str(pdf_dir),
        docstore_manager=docstore,
        update_existing=True
    )
    
    print(f"\n✓ Documents processats: {results['processed']}")
    print(f"✓ Guardats: {results['store_results']}")
    
    if results['errors']:
        print(f"\n⚠️  Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"  • {error['file']}: {error['error']}")


def example_3_search_by_metadata():
    """
    Exemple 3: Cerca per metadades
    """
    print("\n" + "="*70)
    print("EXEMPLE 3: Cerca per metadades")
    print("="*70 + "\n")
    
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Afegir documents amb diferents metadades
    docs = [
        Document(
            text="Document del departament IT sobre seguretat.",
            metadata={
                'filename': 'security.pdf',
                'department': 'IT',
                'category': 'security',
                'language': 'ca'
            }
        ),
        Document(
            text="Document del departament Legal sobre contractes.",
            metadata={
                'filename': 'contracts.pdf',
                'department': 'Legal',
                'category': 'contracts',
                'language': 'ca'
            }
        ),
        Document(
            text="Altro documento del dipartimento IT.",
            metadata={
                'filename': 'manual.pdf',
                'department': 'IT',
                'category': 'manual',
                'language': 'es'
            }
        )
    ]
    
    print("📥 Guardant documents amb metadata...")
    docstore.add_documents(docs)
    
    # Cerca 1: Tots els documents IT
    print("\n🔍 Cerca: department='IT'")
    it_docs = docstore.search_by_metadata({'department': 'IT'})
    print(f"✓ Trobats: {len(it_docs)} documents")
    for doc in it_docs:
        print(f"  • {doc.metadata['filename']}")
    
    # Cerca 2: Documents en català del departament IT
    print("\n🔍 Cerca: department='IT' AND language='ca'")
    filtered_docs = docstore.search_by_metadata({
        'department': 'IT',
        'language': 'ca'
    }, match_all=True)
    print(f"✓ Trobats: {len(filtered_docs)} documents")
    for doc in filtered_docs:
        print(f"  • {doc.metadata['filename']}")


def example_4_incremental_updates():
    """
    Exemple 4: Actualitzacions incrementals
    """
    print("\n" + "="*70)
    print("EXEMPLE 4: Actualitzacions incrementals")
    print("="*70 + "\n")
    
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Document inicial
    doc_v1 = Document(
        doc_id="doc_updateable",
        text="Versió 1 del document.",
        metadata={'filename': 'doc.txt', 'version': 1}
    )
    
    print("📥 Guardant versió 1...")
    docstore.add_documents([doc_v1])
    
    # Recuperar i mostrar
    stored = docstore.get_document("doc_updateable")
    print(f"✓ Guardat: {stored.text}")
    print(f"  Metadata: {stored.metadata}")
    
    # Actualitzar
    doc_v2 = Document(
        doc_id="doc_updateable",
        text="Versió 2 del document amb més contingut.",
        metadata={'filename': 'doc.txt', 'version': 2}
    )
    
    print("\n📝 Actualitzant a versió 2...")
    docstore.add_documents([doc_v2], update_existing=True)
    
    # Recuperar actualitzat
    updated = docstore.get_document("doc_updateable")
    print(f"✓ Actualitzat: {updated.text}")
    print(f"  Metadata: {updated.metadata}")
    
    # Verificar timestamps
    if 'updated_at' in updated.metadata:
        print(f"  Última actualització: {updated.metadata['updated_at']}")


def example_5_delete_and_cleanup():
    """
    Exemple 5: Esborrar documents
    """
    print("\n" + "="*70)
    print("EXEMPLE 5: Esborrar documents")
    print("="*70 + "\n")
    
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Estadístiques inicials
    stats_before = docstore.get_statistics()
    print(f"📊 Documents inicials: {stats_before['total_documents']}")
    
    # Afegir document temporal
    temp_doc = Document(
        doc_id="temp_document",
        text="Document temporal per esborrar.",
        metadata={'filename': 'temp.txt'}
    )
    
    print("\n📥 Afegint document temporal...")
    docstore.add_documents([temp_doc])
    
    stats_after_add = docstore.get_statistics()
    print(f"✓ Documents després d'afegir: {stats_after_add['total_documents']}")
    
    # Esborrar
    print("\n🗑️  Esborrant document temporal...")
    success = docstore.delete_document("temp_document")
    
    if success:
        print("✓ Document esborrat correctament")
        stats_after_delete = docstore.get_statistics()
        print(f"✓ Documents finals: {stats_after_delete['total_documents']}")
    else:
        print("✗ Error esborrant document")


def example_6_monitoring_and_stats():
    """
    Exemple 6: Monitoratge i estadístiques
    """
    print("\n" + "="*70)
    print("EXEMPLE 6: Monitoratge i estadístiques")
    print("="*70 + "\n")
    
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Obtenir totes les estadístiques
    stats = docstore.get_statistics()
    
    print("📊 ESTADÍSTIQUES COMPLETES")
    print("-" * 70)
    print(f"\nTotal documents: {stats['total_documents']}")
    print(f"Total caràcters: {stats['total_chars']:,}")
    print(f"Mitjana caràcters/document: {stats['avg_chars']:,}")
    
    if stats.get('by_file_type'):
        print("\n📁 Per tipus de fitxer:")
        for file_type, count in stats['by_file_type'].items():
            print(f"  • {file_type}: {count} documents")
    
    if stats.get('by_language'):
        print("\n🌍 Per idioma:")
        for lang, count in stats['by_language'].items():
            print(f"  • {lang}: {count} documents")


def example_7_comparison_before_after():
    """
    Exemple 7: Comparació abans/després de persistència
    """
    print("\n" + "="*70)
    print("EXEMPLE 7: Comparació abans/després")
    print("="*70 + "\n")
    
    # Sense persistència (memòria)
    print("❌ SENSE PERSISTÈNCIA (només memòria):")
    print("-" * 70)
    print("• Documents es perden quan acaba el programa")
    print("• Cal reprocessar tot cada vegada")
    print("• No es poden fer actualitzacions incrementals")
    print("• Impossible compartir entre processos")
    
    # Amb persistència
    print("\n✅ AMB PERSISTÈNCIA (DocStore):")
    print("-" * 70)
    print("• Documents es mantenen entre execucions")
    print("• Actualitzacions incrementals (només nous/modificats)")
    print("• Cerca ràpida per metadades")
    print("• Versionat i tracking d'estat")
    print("• Estadístiques i monitoratge")
    print("• Base per sincronitzar amb VectorStore")
    
    # Demostració pràctica
    print("\n🔬 DEMOSTRACIÓ:")
    print("-" * 70)
    
    docstore = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'
    )
    
    # Primera execució
    print("\n1️⃣  Primera execució - Afegir 3 documents")
    docs = [
        Document(text=f"Document {i}", metadata={'id': i})
        for i in range(3)
    ]
    docstore.add_documents(docs)
    print(f"   ✓ {len(docs)} documents guardats")
    
    # Simular "reinici" - crear nou docstore apuntant al mateix path
    print("\n2️⃣  Segona execució - Recuperar documents existents")
    docstore2 = DocumentStoreManager(
        backend='simple',
        persist_path='data/docstore'  # Mateix path!
    )
    recovered = docstore2.get_all_documents()
    print(f"   ✓ {len(recovered)} documents recuperats automàticament")
    print("   ✓ No cal reprocessar res!")


if __name__ == "__main__":
    print("\n" + "🚀 " + "="*68)
    print("   EXEMPLES DE PERSISTÈNCIA AMB DOCSTORE")
    print("="*70 + "\n")
    
    try:
        example_1_basic_persistence()
        example_2_complete_pipeline()
        example_3_search_by_metadata()
        example_4_incremental_updates()
        example_5_delete_and_cleanup()
        example_6_monitoring_and_stats()
        example_7_comparison_before_after()
        
        print("\n" + "="*70)
        print("✅ TOTS ELS EXEMPLES COMPLETATS")
        print("="*70 + "\n")
        
        print("💡 AVANTATGES DE LA PERSISTÈNCIA:")
        print("  ✓ Documents es mantenen entre execucions")
        print("  ✓ Actualitzacions incrementals")
        print("  ✓ Cerca ràpida per metadades")
        print("  ✓ Versionat integrat")
        print("  ✓ Base sòlida per al VectorStore (Mòdul 2)")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.exception("Error executant exemples")