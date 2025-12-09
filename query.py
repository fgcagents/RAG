#!/usr/bin/env python3
# query.py
"""
Script para hacer consultas al sistema RAG
Funciona 100% local sin OpenAI
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from modules.processing import IndexBuilder, VectorStoreManager, EmbeddingGenerator
import logging

logging.basicConfig(level=logging.WARNING)  # Solo errores


def load_index():
    """Carga el índice guardado"""
    print("🔄 Cargando índice vectorial...\n")
    
    try:
        # Recrear componentes
        embedder = EmbeddingGenerator(model_name='bge-m3')
        
        vector_store = VectorStoreManager(
            backend='chroma',
            collection_name='rag_documents',
            dimension=embedder.dimensions
        )
        
        builder = IndexBuilder(
            vector_store_manager=vector_store,
            embed_model=embedder.embed_model,
            persist_dir='data/indexes'
        )
        
        # Cargar índice existente
        index = builder.load_index()
        
        if not index:
            print("❌ No se encontró índice guardado")
            print("💡 Primero ejecuta: python pipeline_local.py")
            return None, None
        
        print("✅ Índice cargado correctamente\n")
        return builder, embedder
        
    except Exception as e:
        print(f"❌ Error cargando índice: {e}")
        print("💡 Asegúrate de haber ejecutado primero: python pipeline_local.py")
        return None, None


def search(builder, embedder, query, top_k=5):
    """
    Hace una búsqueda en el índice
    
    Args:
        builder: IndexBuilder con índice cargado
        embedder: EmbeddingGenerator
        query: Texto de la consulta
        top_k: Número de resultados
    
    Returns:
        Lista de resultados
    """
    try:
        # Generar embedding de la query
        query_embedding = embedder.generate_query_embedding(query)
        
        # Buscar en el vector store
        results = builder.vector_store_manager.query(
            query_embedding=query_embedding,
            top_k=top_k
        )
        
        return results
        
    except Exception as e:
        print(f"❌ Error en búsqueda: {e}")
        return None


def interactive_mode():
    """Modo interactivo de consultas"""
    print("="*70)
    print("🔍 SISTEMA DE CONSULTAS RAG - Modo Interactivo")
    print("="*70)
    print()
    
    # Cargar índice
    builder, embedder = load_index()
    
    if not builder:
        return
    
    print("💡 Escribe 'salir' para terminar")
    print("💡 Escribe 'ejemplos' para ver consultas de ejemplo")
    print()
    
    while True:
        try:
            # Pedir consulta
            query = input("🔍 Tu consulta: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                break
            
            if query.lower() == 'ejemplos':
                print("\n📝 Ejemplos de consultas:")
                print("  • Quina és la política de vacances?")
                print("  • Com sol·licitar vacances?")
                print("  • Quants dies de vacances tinc?")
                print("  • Procediment de contractació")
                print("  • Política de teletrebal")
                print()
                continue
            
            # Hacer búsqueda
            print(f"\n🔄 Buscando...\n")
            
            results = search(builder, embedder, query, top_k=5)
            
            if not results or not results.nodes:
                print("❌ No se encontraron resultados")
                print()
                continue
            
            # Mostrar resultados
            print("="*70)
            print(f"✅ Encontrados {len(results.nodes)} resultados")
            print("="*70)
            
            for i, node in enumerate(results.nodes, 1):
                score = results.similarities[i-1] if results.similarities else 0
                text = node.get_content()
                
                # Metadata
                metadata = node.metadata
                filename = metadata.get('filename', 'N/A')
                
                print(f"\n[{i}] Similitud: {score:.3f} | Archivo: {filename}")
                print("-"*70)
                print(text[:400] + ("..." if len(text) > 400 else ""))
                print()
            
            print("="*70)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            continue


def single_query_mode(query, top_k=5):
    """Modo de consulta única"""
    print("="*70)
    print("🔍 SISTEMA DE CONSULTAS RAG")
    print("="*70)
    print()
    
    # Cargar índice
    builder, embedder = load_index()
    
    if not builder:
        return
    
    print(f"🔍 Consulta: '{query}'\n")
    
    # Hacer búsqueda
    results = search(builder, embedder, query, top_k=top_k)
    
    if not results or not results.nodes:
        print("❌ No se encontraron resultados\n")
        return
    
    # Mostrar resultados
    print("="*70)
    print(f"✅ Encontrados {len(results.nodes)} resultados")
    print("="*70)
    
    for i, node in enumerate(results.nodes, 1):
        score = results.similarities[i-1] if results.similarities else 0
        text = node.get_content()
        
        # Metadata
        metadata = node.metadata
        filename = metadata.get('filename', 'N/A')
        
        print(f"\n[{i}] Similitud: {score:.3f} | Archivo: {filename}")
        print("-"*70)
        print(text[:400] + ("..." if len(text) > 400 else ""))
        print()
    
    print("="*70)
    print()


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de consultas RAG')
    parser.add_argument('query', nargs='*', help='Consulta a realizar')
    parser.add_argument('--top-k', type=int, default=5, help='Número de resultados')
    parser.add_argument('--interactive', '-i', action='store_true', help='Modo interactivo')
    
    args = parser.parse_args()
    
    if args.interactive or not args.query:
        # Modo interactivo
        interactive_mode()
    else:
        # Consulta única
        query = ' '.join(args.query)
        single_query_mode(query, top_k=args.top_k)


if __name__ == "__main__":
    main()
