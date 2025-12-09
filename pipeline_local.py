#!/usr/bin/env python3
# pipeline_local.py
"""
Pipeline 100% LOCAL - Sin OpenAI, sin API keys
Usa BGE-M3 para embeddings y solo recupera documentos (sin generar respuestas)
"""

import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent))

from modules.ingestion.docstore import DocumentStoreManager
from modules.processing import (
    ChunkingStrategy,
    EmbeddingGenerator,
    VectorStoreManager,
    IndexBuilder
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("🚀 PIPELINE 100% LOCAL (Sin OpenAI)")
    print("="*70 + "\n")
    
    try:
        # 1. Cargar documentos del DocStore
        print("📚 Paso 1: Cargando documentos del DocStore...")
        docstore = DocumentStoreManager(backend='simple', persist_path='data/docstore')
        documents = docstore.get_all_documents()
        
        if not documents:
            print("❌ No hay documentos en el DocStore")
            print("💡 Primero ejecuta el Módulo 1 para procesar PDFs")
            return
        
        print(f"✅ Documentos cargados: {len(documents)}\n")
        
        # 2. Chunking
        print("🔪 Paso 2: Chunking...")
        chunker = ChunkingStrategy(strategy='sentence', chunk_size=512, chunk_overlap=50)
        nodes = chunker.chunk_documents(documents, show_progress=False)
        print(f"✅ Chunks generados: {len(nodes)}\n")
        
        # 3. Embeddings (LOCAL - BGE-M3)
        print("🤖 Paso 3: Generando embeddings (BGE-M3 local)...")
        print("   ⏳ Primera vez puede tardar 2-5 min (descarga modelo)...")
        
        embedder = EmbeddingGenerator(
            model_name='bge-m3',
            batch_size=50
        )
        
        nodes = embedder.embed_nodes(nodes, show_progress=True)
        print(f"✅ Embeddings generados: {len(nodes)}\n")
        
        # 4. Vector Store (LOCAL - ChromaDB)
        print("💾 Paso 4: Creando vector store (ChromaDB local)...")
        vector_store = VectorStoreManager(
            backend='chroma',
            collection_name='rag_documents',
            dimension=embedder.dimensions
        )
        print(f"✅ Vector store creado\n")
        
        # 5. Construir índice
        print("🏗️  Paso 5: Construyendo índice...")
        builder = IndexBuilder(
            vector_store_manager=vector_store,
            embed_model=embedder.embed_model
        )
        
        index = builder.build_index(nodes, show_progress=False)
        print(f"✅ Índice construido\n")
        
        # 6. Persistir
        print("💾 Paso 6: Guardando índice...")
        builder.persist()
        print(f"✅ Índice guardado en: data/indexes\n")
        
        # 7. Probar búsquedas (SOLO RECUPERACIÓN, sin generar respuestas)
        print("="*70)
        print("🔍 PROBANDO BÚSQUEDAS")
        print("="*70 + "\n")
        
        retriever = builder.get_retriever(similarity_top_k=3)
        
        test_queries = [
            "Quina és la política de vacances?",
            "Com sol·licitar vacances?",
            "Quants dies de vacances tinc?"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{'='*70}")
            print(f"Query {i}: '{query}'")
            print("="*70)
            
            try:
                # Recuperar documentos similares
                results = retriever.retrieve(query)
                
                print(f"\n✅ Documentos encontrados: {len(results)}\n")
                
                for j, node in enumerate(results, 1):
                    score = node.score if hasattr(node, 'score') else 0
                    text = node.text if hasattr(node, 'text') else node.node.text
                    
                    print(f"[{j}] Similitud: {score:.3f}")
                    print(f"    {text[:200]}...")
                    print()
                
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        # Resumen final
        print("\n" + "="*70)
        print("✅ PIPELINE COMPLETADO EXITOSAMENTE")
        print("="*70)
        print(f"\n📊 RESUMEN:")
        print(f"  • Documentos: {len(documents)}")
        print(f"  • Chunks: {len(nodes)}")
        print(f"  • Embedding model: {embedder.model_name} (LOCAL)")
        print(f"  • Vector store: {vector_store.backend} (LOCAL)")
        print(f"\n💾 Datos guardados en:")
        print(f"  • DocStore: data/docstore")
        print(f"  • Vector Store: data/vector_stores")
        print(f"  • Índice: data/indexes")
        print(f"\n💡 CÓMO HACER CONSULTAS:")
        print("""
from modules.processing import IndexBuilder, VectorStoreManager, EmbeddingGenerator

# Recrear componentes
embedder = EmbeddingGenerator(model_name='bge-m3')
vector_store = VectorStoreManager(backend='chroma', dimension=embedder.dimensions)
builder = IndexBuilder(vector_store_manager=vector_store, embed_model=embedder.embed_model)

# Cargar índice
index = builder.load_index()

# Hacer búsquedas (sin generar respuestas)
retriever = builder.get_retriever(similarity_top_k=5)
results = retriever.retrieve("tu pregunta aquí")

# Mostrar resultados
for node in results:
    print(f"Score: {node.score:.3f}")
    print(f"Texto: {node.text[:200]}...")
    print()
""")
        print("="*70 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
