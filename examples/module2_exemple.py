# examples/module2_example.py
"""
Exemple complet d'ús del Mòdul 2: Document Processing & Indexing
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.ingestion.docstore import DocumentStoreManager
from modules.processing import (
    ChunkingStrategy,
    EmbeddingGenerator,
    VectorStoreManager,
    IndexBuilder,
    MetadataIndex,
    hybrid_search,
    build_complete_pipeline
)
from llama_index.core import Document
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_chunking():
    """
    Exemple 1: Chunking amb diferents estratègies
    """
    print("\n" + "="*70)
    print("EXEMPLE 1: CHUNKING STRATEGIES")
    print("="*70)
    
    # Document de prova
    text = """
    # Política de Vacances
    
    Els empleats tenen dret a 30 dies de vacances a l'any. Les vacances s'han de
    sol·licitar amb un mínim de 15 dies d'antelació. Durant els mesos de juliol i
    agost, es requereix una antelació de 30 dies.
    
    ## Procediment
    
    1. Sol·licitar les vacances al sistema
    2. Esperar aprovació del supervisor
    3. Confirmar les dates
    
    Les vacances no gaudides es poden acumular fins a un màxim de 5 dies per al
    següent any fiscal.
    """
    
    doc = Document(
        text=text,
        metadata={'filename': 'vacances.md', 'department': 'HR'}
    )
    
    strategies = ['sentence', 'fixed_size', 'recursive']
    
    for strategy in strategies:
        print(f"\n🔧 Estratègia: {strategy}")
        
        chunker = ChunkingStrategy(
            strategy=strategy,
            chunk_size=200,
            chunk_overlap=20
        )
        
        nodes = chunker.chunk_documents([doc], show_progress=False)
        
        print(f"  ✓ Chunks generats: {len(nodes)}")
        
        stats = chunker.get_statistics(nodes)
        print(f"  ✓ Longitud mitjana: {stats['avg_chunk_length']:.0f} chars")
        print(f"  ✓ Min/Max: {stats['min_chunk_length']}/{stats['max_chunk_length']}")
        
        # Mostrar primer chunk
        if nodes:
            print(f"  📄 Primer chunk:")
            print(f"     {nodes[0].get_content()[:100]}...")


def example_2_embeddings():
    """
    Exemple 2: Generació d'embeddings
    """
    print("\n" + "="*70)
    print("EXEMPLE 2: EMBEDDING GENERATION")
    print("="*70)
    
    # Crear alguns nodes
    text_samples = [
        "Política de vacances: 30 dies a l'any",
        "Procediment de sol·licitud de vacances",
        "Acumulació de dies no gaudits"
    ]
    
    nodes = [
        Document(text=text, metadata={'id': i})
        for i, text in enumerate(text_samples)
    ]
    
    # Chunking simple
    chunker = ChunkingStrategy(strategy='sentence', chunk_size=100)
    nodes = chunker.chunk_documents(nodes, show_progress=False)
    
    print(f"\n📊 Nodes preparats: {len(nodes)}")
    
    # Provar amb model local (no requereix API key)
    print("\n🤖 Model: BGE-M3 (multilingüe, local)")
    
    try:
        embedder = EmbeddingGenerator(
            model_name='bge-m3',
            batch_size=10
        )
        
        print(f"  ✓ Model info:")
        info = embedder.get_model_info()
        print(f"    - Dimensions: {info['dimensions']}")
        print(f"    - Multilingüe: {info['multilingual']}")
        print(f"    - Max tokens: {info['max_tokens']}")
        
        # Generar embeddings
        print(f"\n  🔄 Generant embeddings...")
        nodes = embedder.embed_nodes(nodes, show_progress=False)
        
        print(f"  ✓ Embeddings generats!")
        print(f"  ✓ Dimensions: {len(nodes[0].embedding)}")
        print(f"  ✓ Primer embedding (preview): {nodes[0].embedding[:5]}...")
        
    except Exception as e:
        print(f"  ⚠️  Error amb BGE-M3: {e}")
        print(f"  💡 Instal·la: pip install sentence-transformers torch")


def example_3_vector_store():
    """
    Exemple 3: Vector Store amb ChromaDB (fàcil)
    """
    print("\n" + "="*70)
    print("EXEMPLE 3: VECTOR STORE (ChromaDB)")
    print("="*70)
    
    try:
        # Crear vector store
        print("\n💾 Inicialitzant ChromaDB...")
        
        vector_store = VectorStoreManager(
            backend='chroma',
            collection_name='test_collection',
            persist_path='data/vector_stores/test',
            dimension=384  # Per bge-small o similar
        )
        
        print(f"  ✓ Vector store creat")
        print(f"  ✓ Backend: {vector_store.backend}")
        print(f"  ✓ Col·lecció: {vector_store.collection_name}")
        
        # Crear nodes amb embeddings dummy
        from llama_index.core.schema import TextNode
        import random
        
        nodes = []
        for i in range(5):
            node = TextNode(
                text=f"Document {i} sobre política de vacances",
                metadata={'doc_id': i, 'department': 'HR'}
            )
            # Embedding dummy (random)
            node.embedding = [random.random() for _ in range(384)]
            nodes.append(node)
        
        print(f"\n  📥 Afegint {len(nodes)} nodes...")
        results = vector_store.add_nodes(nodes, show_progress=False)
        
        print(f"  ✓ Nodes afegits: {results['added']}")
        
        # Query
        print(f"\n  🔍 Provant cerca vectorial...")
        query_embedding = [random.random() for _ in range(384)]
        
        results = vector_store.query(
            query_embedding=query_embedding,
            top_k=3
        )
        
        print(f"  ✓ Resultats trobats: {len(results.nodes)}")
        
        for i, node in enumerate(results.nodes):
            print(f"    {i+1}. {node.text[:50]}... (score: {results.similarities[i]:.3f})")
        
        # Estadístiques
        print(f"\n  📊 Estadístiques:")
        stats = vector_store.get_statistics()
        for key, value in stats.items():
            print(f"    - {key}: {value}")
        
    except ImportError:
        print("  ⚠️  ChromaDB no instal·lat")
        print("  💡 Instal·la: pip install chromadb")
    except Exception as e:
        print(f"  ❌ Error: {e}")


def example_4_metadata_index():
    """
    Exemple 4: Metadata Index
    """
    print("\n" + "="*70)
    print("EXEMPLE 4: METADATA INDEX")
    print("="*70)
    
    from llama_index.core.schema import TextNode
    
    # Crear nodes amb metadata
    nodes = [
        TextNode(
            text="Document IT sobre seguretat",
            metadata={
                'department': 'IT',
                'category': 'security',
                'language': 'ca',
                'year': 2024
            }
        ),
        TextNode(
            text="Document Legal sobre contractes",
            metadata={
                'department': 'Legal',
                'category': 'contracts',
                'language': 'ca',
                'year': 2024
            }
        ),
        TextNode(
            text="Document IT sobre xarxes",
            metadata={
                'department': 'IT',
                'category': 'network',
                'language': 'es',
                'year': 2023
            }
        )
    ]
    
    print(f"\n📋 Indexant metadata de {len(nodes)} nodes...")
    
    # Crear metadata index
    metadata_index = MetadataIndex(
        persist_path='data/indexes/metadata/test'
    )
    
    metadata_index.index_nodes(nodes)
    
    print(f"  ✓ Nodes indexats: {len(nodes)}")
    
    # Cerca 1: Departament IT
    print(f"\n  🔍 Cerca: department='IT'")
    results = metadata_index.search({'department': 'IT'})
    print(f"  ✓ Resultats: {len(results)} nodes")
    
    # Cerca 2: IT en català
    print(f"\n  🔍 Cerca: department='IT' AND language='ca'")
    results = metadata_index.search(
        {'department': 'IT', 'language': 'ca'},
        match_all=True
    )
    print(f"  ✓ Resultats: {len(results)} nodes")
    
    # Valors únics
    print(f"\n  📊 Valors únics:")
    departments = metadata_index.get_unique_values('department')
    print(f"    - Departaments: {departments}")
    
    # Value counts
    counts = metadata_index.get_value_counts('department')
    print(f"    - Conteos: {counts}")
    
    # Estadístiques
    print(f"\n  📊 Estadístiques:")
    stats = metadata_index.get_statistics()
    print(f"    - Total nodes: {stats['total_nodes']}")
    print(f"    - Camps indexats: {stats['indexed_fields']}")


def example_5_complete_pipeline():
    """
    Exemple 5: Pipeline complet
    """
    print("\n" + "="*70)
    print("EXEMPLE 5: PIPELINE COMPLET")
    print("="*70)
    
    # Carregar documents del DocStore (Mòdul 1)
    print("\n📂 Carregant documents del DocStore...")
    
    try:
        docstore = DocumentStoreManager(
            backend='simple',
            persist_path='data/docstore'
        )
        
        documents = docstore.get_all_documents()
        
        if not documents:
            print("  ⚠️  No hi ha documents al DocStore")
            print("  💡 Executa primer el Mòdul 1 per processar PDFs")
            
            # Crear documents dummy
            print("\n  📝 Creant documents de prova...")
            documents = [
                Document(
                    text="Política de vacances: 30 dies anuals",
                    metadata={'filename': 'vacances.txt', 'department': 'HR'}
                ),
                Document(
                    text="Procediment de contractació de personal",
                    metadata={'filename': 'contractacio.txt', 'department': 'HR'}
                )
            ]
        
        print(f"  ✓ Documents carregats: {len(documents)}")
        
        # Pipeline simplificat
        print(f"\n🔄 Executant pipeline complet...")
        print(f"  💡 Això pot trigar uns minuts la primera vegada...")
        
        try:
            builder, index, stats = build_complete_pipeline(
                documents=documents[:2],  # Només 2 per rapidesa
                chunking_strategy='sentence',
                embedding_model='bge-small',  # Més ràpid que bge-m3
                vector_store_backend='chroma'
            )
            
            print(f"\n✅ Pipeline completat!")
            print(f"\n📊 Estadístiques:")
            print(f"  - Documents processats: {stats['documents']}")
            print(f"  - Chunks generats: {stats['nodes']}")
            print(f"  - Model embeddings: {stats['embedding']['name']}")
            print(f"  - Dimensions: {stats['embedding']['dimensions']}")
            print(f"  - Vector store: {stats['vector_store']['backend']}")
            
            # Provar query
            print(f"\n🔍 Provant consulta...")
            query_engine = builder.get_query_engine(similarity_top_k=3)
            
            response = query_engine.query("Quants dies de vacances tenim?")
            
            print(f"  ✓ Resposta: {response}")
            
        except Exception as e:
            print(f"  ❌ Error en pipeline: {e}")
            print(f"  💡 Verifica que tens instal·lats: chromadb, sentence-transformers")
        
    except Exception as e:
        print(f"  ❌ Error carregant DocStore: {e}")


def example_6_hybrid_search():
    """
    Exemple 6: Cerca híbrida (vectorial + metadata)
    """
    print("\n" + "="*70)
    print("EXEMPLE 6: HYBRID SEARCH")
    print("="*70)
    
    from llama_index.core.schema import TextNode
    import random
    
    # Crear nodes amb embeddings i metadata
    nodes = []
    departments = ['IT', 'Legal', 'HR', 'Finance']
    languages = ['ca', 'es', 'en']
    
    for i in range(10):
        node = TextNode(
            text=f"Document {i} amb contingut important",
            metadata={
                'department': departments[i % len(departments)],
                'language': languages[i % len(languages)],
                'priority': random.choice(['high', 'medium', 'low'])
            }
        )
        node.embedding = [random.random() for _ in range(384)]
        nodes.append(node)
    
    print(f"\n📋 Creats {len(nodes)} nodes amb metadata")
    
    # Crear metadata index
    metadata_index = MetadataIndex()
    metadata_index.index_nodes(nodes)
    
    print(f"  ✓ Metadata indexada")
    
    # Simular resultats vectorials
    vector_node_ids = [n.node_id for n in nodes[:7]]  # Top 7 de vectorial
    
    print(f"\n🔍 Cerca híbrida:")
    print(f"  - Resultats vectorials: {len(vector_node_ids)}")
    
    # Aplicar filtres
    filtered = hybrid_search(
        vector_results=vector_node_ids,
        metadata_index=metadata_index,
        metadata_filters={
            'department': 'IT',
            'language': 'ca'
        }
    )
    
    print(f"  - Després de filtres: {len(filtered)}")
    
    # Mostrar nodes filtrats
    for node_id in filtered:
        node_meta = metadata_index.get_node_metadata(node_id)
        print(f"    ✓ {node_id[:8]}... → {node_meta}")


def main():
    """Executar tots els exemples"""
    print("\n" + "🚀 " + "="*68)
    print("   EXEMPLES DEL MÒDUL 2: DOCUMENT PROCESSING & INDEXING")
    print("="*70 + "\n")
    
    examples = [
        ("Chunking Strategies", example_1_chunking),
        ("Embedding Generation", example_2_embeddings),
        ("Vector Store", example_3_vector_store),
        ("Metadata Index", example_4_metadata_index),
        ("Complete Pipeline", example_5_complete_pipeline),
        ("Hybrid Search", example_6_hybrid_search)
    ]
    
    for name, func in examples:
        try:
            func()
        except KeyboardInterrupt:
            print(f"\n⚠️  Interromput per l'usuari")
            break
        except Exception as e:
            print(f"\n❌ Error en '{name}': {e}")
            logger.exception(f"Error en exemple {name}")
            continue
    
    print("\n" + "="*70)
    print("✅ EXEMPLES COMPLETATS")
    print("="*70 + "\n")
    
    print("💡 PROPERS PASSOS:")
    print("  1. Revisa els resultats dels exemples")
    print("  2. Ajusta configuració al fitxer .env")
    print("  3. Executa el pipeline complet amb els teus documents")
    print("  4. Passa al Mòdul 3: Query & Retrieval")
    print()


if __name__ == "__main__":
    main()
