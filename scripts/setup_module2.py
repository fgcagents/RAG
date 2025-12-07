#!/usr/bin/env python3
# scripts/setup_module2.py
"""
Script per configurar i provar el Mòdul 2: Document Processing & Indexing
"""

import sys
from pathlib import Path
import logging

# Afegir directori arrel al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.processing_config import setup_directories, config

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_environment():
    """Configura l'entorn inicial"""
    print("\n" + "="*70)
    print("  CONFIGURACIÓ DEL MÒDUL 2: DOCUMENT PROCESSING & INDEXING")
    print("="*70 + "\n")
    
    print("📁 Creant estructura de directoris...")
    setup_directories()
    
    print("\n📋 Configuració actual:")
    print(f"  • Chunking strategy: {config.CHUNKING_STRATEGY}")
    print(f"  • Chunk size: {config.CHUNK_SIZE}")
    print(f"  • Chunk overlap: {config.CHUNK_OVERLAP}")
    print(f"  • Embedding model: {config.EMBEDDING_MODEL}")
    print(f"  • Vector store: {config.VECTOR_STORE_BACKEND}")
    print(f"  • Collection: {config.COLLECTION_NAME}")
    print(f"  • Similarity top-k: {config.SIMILARITY_TOP_K}")
    
    return True


def test_components():
    """Testa els components del mòdul"""
    print("\n🧪 Testant components del mòdul...\n")
    
    results = {
        'ChunkingStrategy': False,
        'EmbeddingGenerator': False,
        'VectorStoreManager': False,
        'IndexBuilder': False,
        'MetadataIndex': False
    }
    
    # Test 1: Chunking
    print("1️⃣  Testing ChunkingStrategy...")
    try:
        from modules.processing import ChunkingStrategy
        from llama_index.core import Document
        
        chunker = ChunkingStrategy(
            strategy='sentence',
            chunk_size=200,
            chunk_overlap=20
        )
        
        test_doc = Document(
            text="Aquest és un document de prova. " * 20,
            metadata={'test': True}
        )
        
        nodes = chunker.chunk_documents([test_doc], show_progress=False)
        
        print(f"   ✓ ChunkingStrategy funciona")
        print(f"     Chunks generats: {len(nodes)}")
        results['ChunkingStrategy'] = True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Embeddings
    print("\n2️⃣  Testing EmbeddingGenerator...")
    try:
        from modules.processing import EmbeddingGenerator
        
        # Intentar amb model local
        try:
            embedder = EmbeddingGenerator(
                model_name='bge-small',
                batch_size=10
            )
            
            info = embedder.get_model_info()
            print(f"   ✓ EmbeddingGenerator funciona")
            print(f"     Model: {info['name']}")
            print(f"     Dimensions: {info['dimensions']}")
            print(f"     Multilingüe: {info['multilingual']}")
            results['EmbeddingGenerator'] = True
            
        except Exception as e_inner:
            print(f"   ⚠️  Model local no disponible: {e_inner}")
            print(f"   💡 Instal·la: pip install sentence-transformers torch")
            results['EmbeddingGenerator'] = False
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Vector Store
    print("\n3️⃣  Testing VectorStoreManager...")
    try:
        from modules.processing import VectorStoreManager
        
        # Intentar amb ChromaDB (més fàcil)
        try:
            vector_store = VectorStoreManager(
                backend='chroma',
                collection_name='test_collection',
                persist_path='data/vector_stores/test',
                dimension=384
            )
            
            print(f"   ✓ VectorStoreManager funciona")
            print(f"     Backend: {vector_store.backend}")
            print(f"     Collection: {vector_store.collection_name}")
            results['VectorStoreManager'] = True
            
        except ImportError:
            print(f"   ⚠️  ChromaDB no instal·lat")
            print(f"   💡 Instal·la: pip install chromadb")
            results['VectorStoreManager'] = False
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Index Builder
    print("\n4️⃣  Testing IndexBuilder...")
    try:
        from modules.processing import IndexBuilder
        
        print(f"   ✓ IndexBuilder importat correctament")
        results['IndexBuilder'] = True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 5: Metadata Index
    print("\n5️⃣  Testing MetadataIndex...")
    try:
        from modules.processing import MetadataIndex
        from llama_index.core.schema import TextNode
        
        metadata_index = MetadataIndex(
            persist_path='data/indexes/metadata/test'
        )
        
        # Test amb nodes
        test_nodes = [
            TextNode(
                text=f"Node {i}",
                metadata={'department': 'IT', 'category': 'test'}
            )
            for i in range(3)
        ]
        
        metadata_index.index_nodes(test_nodes)
        
        # Cerca
        results_search = metadata_index.search({'department': 'IT'})
        
        print(f"   ✓ MetadataIndex funciona")
        print(f"     Nodes indexats: {len(test_nodes)}")
        print(f"     Resultats cerca: {len(results_search)}")
        results['MetadataIndex'] = True
        
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


def check_dependencies():
    """Verifica dependències instal·lades"""
    print("\n📦 Verificant dependències...\n")
    
    dependencies = {
        'llama_index': 'llama-index',
        'qdrant_client': 'qdrant-client (opcional)',
        'chromadb': 'chromadb (opcional)',
        'sentence_transformers': 'sentence-transformers (per models locals)',
        'torch': 'torch (per models locals)'
    }
    
    installed = {}
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            installed[name] = True
            print(f"  ✅ {name}")
        except ImportError:
            installed[name] = False
            print(f"  ❌ {name} - NO INSTAL·LAT")
    
    # Recomanacions
    print("\n💡 RECOMANACIONS D'INSTAL·LACIÓ:\n")
    
    if not installed.get('chromadb (opcional)', False):
        print("  Vector Store (fàcil):")
        print("    pip install chromadb")
        print()
    
    if not installed.get('qdrant-client (opcional)', False):
        print("  Vector Store (recomanat):")
        print("    pip install qdrant-client")
        print()
    
    if not installed.get('sentence-transformers (per models locals)', False):
        print("  Models d'embeddings locals (sense API key):")
        print("    pip install sentence-transformers torch")
        print()
    
    return sum(installed.values()) > 3  # Mínim llama_index + 3 més


def show_next_steps():
    """Mostra els propers passos"""
    print("\n" + "="*70)
    print("  ✅ MÒDUL 2 CONFIGURAT")
    print("="*70 + "\n")
    
    print("🚀 PROPERS PASSOS:\n")
    
    print("1. Instal·lar dependències opcionals:")
    print("   pip install chromadb sentence-transformers torch")
    print()
    
    print("2. Configurar .env (si vols usar OpenAI):")
    print("   PROCESSING_OPENAI_API_KEY=sk-your-key")
    print("   PROCESSING_EMBEDDING_MODEL=openai-small")
    print()
    
    print("3. Executar exemples:")
    print("   python examples/module2_example.py")
    print()
    
    print("4. Pipeline complet Mòdul 1 + Mòdul 2:")
    print("   # Carregar del DocStore")
    print("   from modules.ingestion.docstore import DocumentStoreManager")
    print("   from modules.processing import build_complete_pipeline")
    print()
    print("   docstore = DocumentStoreManager(backend='simple')")
    print("   docs = docstore.get_all_documents()")
    print()
    print("   builder, index, stats = build_complete_pipeline(")
    print("       documents=docs,")
    print("       chunking_strategy='sentence',")
    print("       embedding_model='bge-m3',")
    print("       vector_store_backend='chroma'")
    print("   )")
    print()
    
    print("5. Quan estigui llest, passa al Mòdul 3:")
    print("   Query & Retrieval amb cerca avançada")
    print()
    
    print("="*70 + "\n")


def show_configuration_guide():
    """Mostra guia de configuració"""
    print("\n" + "="*70)
    print("  📚 GUIA DE CONFIGURACIÓ")
    print("="*70 + "\n")
    
    print("MODELS D'EMBEDDINGS RECOMANATS:\n")
    
    print("  Gratuïts (locals):")
    print("    • bge-m3 (1024D) - Multilingüe, excel·lent per CA/ES ⭐")
    print("    • e5-multilingual (1024D) - Multilingüe, ràpid")
    print("    • bge-small (384D) - Petit i ràpid")
    print()
    
    print("  Amb API key (millor qualitat):")
    print("    • openai-small (1536D) - Balanç qualitat/preu ⭐")
    print("    • openai-large (3072D) - Màxima qualitat")
    print()
    
    print("VECTOR STORES RECOMANATS:\n")
    
    print("  Desenvolupament:")
    print("    • chroma - Fàcil, local, persistent")
    print("    • qdrant (local) - Més potent, escalable ⭐")
    print()
    
    print("  Producció:")
    print("    • qdrant (cloud) - Managed, escalable ⭐")
    print("    • pinecone - Cloud, auto-scaling")
    print()
    
    print("CHUNK SIZE RECOMANAT:\n")
    print("    • OpenAI: 512 tokens")
    print("    • BGE/E5: 384-512 tokens")
    print("    • Overlap: 10-20% del chunk_size")
    print()


def main():
    """Funció principal"""
    print("\n" + "🚀 " + "="*68)
    print("   SETUP MÒDUL 2: DOCUMENT PROCESSING & INDEXING")
    print("="*70 + "\n")
    
    try:
        # Setup inicial
        if not setup_environment():
            print("❌ Error durant el setup")
            return 1
        
        # Verificar dependències
        if not check_dependencies():
            print("\n⚠️  Falten dependències importants")
            response = input("\nVols continuar igualment? (s/n): ")
            if response.lower() != 's':
                return 1
        
        # Testejar components
        if not test_components():
            print("\n⚠️  Alguns tests han fallat")
            response = input("\nVols veure la guia de configuració? (s/n): ")
            if response.lower() == 's':
                show_configuration_guide()
        
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
