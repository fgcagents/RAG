#!/usr/bin/env python3
# main_pipeline.py
"""
Pipeline Complet: Mòdul 1 (Ingestion) + Mòdul 2 (Processing & Indexing)
De PDFs a Sistema de Cerca Vectorial Funcional
"""

import sys
from pathlib import Path
import logging
from datetime import datetime

# Setup paths
sys.path.insert(0, str(Path(__file__).parent))

# Imports Mòdul 1
from modules.ingestion import (
    DocumentLoader,
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor,
    DocumentValidator
)
from modules.ingestion.docstore import DocumentStoreManager

# Imports Mòdul 2
from modules.processing import (
    ChunkingStrategy,
    EmbeddingGenerator,
    VectorStoreManager,
    IndexBuilder,
    MetadataIndex,
    build_complete_pipeline
)

from llama_index.core import Document

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/pipeline_complete.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)


class CompletePipeline:
    """
    Pipeline complet que integra Mòdul 1 i Mòdul 2
    """
    
    def __init__(
        self,
        pdf_dir: str = "data/raw/pdfs",
        docstore_path: str = "data/docstore",
        vector_store_backend: str = "chroma",
        embedding_model: str = "bge-m3",
        chunking_strategy: str = "sentence",
        chunk_size: int = 512
    ):
        """
        Inicialitza el pipeline complet
        
        Args:
            pdf_dir: Directori amb PDFs
            docstore_path: Path del DocStore
            vector_store_backend: Backend del vector store
            embedding_model: Model d'embeddings
            chunking_strategy: Estratègia de chunking
            chunk_size: Mida dels chunks
        """
        self.pdf_dir = Path(pdf_dir)
        self.docstore_path = docstore_path
        self.vector_store_backend = vector_store_backend
        self.embedding_model = embedding_model
        self.chunking_strategy = chunking_strategy
        self.chunk_size = chunk_size
        
        # Components Mòdul 1
        self.pdf_converter = None
        self.text_cleaner = None
        self.metadata_extractor = None
        self.validator = None
        self.docstore = None
        
        # Components Mòdul 2
        self.chunker = None
        self.embedder = None
        self.vector_store = None
        self.index_builder = None
        self.metadata_index = None
        
        # Resultats
        self.stats = {
            'module1': {},
            'module2': {},
            'total_time': 0
        }
    
    def step1_initialize_components(self):
        """Pas 1: Inicialitzar components"""
        logger.info("="*70)
        logger.info("PAS 1: INICIALITZANT COMPONENTS")
        logger.info("="*70)
        
        # Mòdul 1
        logger.info("📦 Mòdul 1: Ingestion...")
        self.pdf_converter = PDFToMarkdownConverter(
            extract_images=True,
            image_path="data/images"
        )
        self.text_cleaner = TextCleaner(
            remove_extra_whitespace=True,
            normalize_unicode=True
        )
        self.metadata_extractor = MetadataExtractor()
        self.validator = DocumentValidator(min_text_length=100)
        self.docstore = DocumentStoreManager(
            backend='simple',
            persist_path=self.docstore_path
        )
        logger.info("  ✓ Components Mòdul 1 inicialitzats")
        
        # Mòdul 2
        logger.info("📦 Mòdul 2: Processing & Indexing...")
        self.chunker = ChunkingStrategy(
            strategy=self.chunking_strategy,
            chunk_size=self.chunk_size,
            chunk_overlap=int(self.chunk_size * 0.1)
        )
        
        try:
            self.embedder = EmbeddingGenerator(
                model_name=self.embedding_model,
                batch_size=50
            )
            logger.info(f"  ✓ Embedding model: {self.embedding_model}")
        except Exception as e:
            logger.error(f"  ✗ Error inicialitzant embeddings: {e}")
            raise
        
        self.vector_store = VectorStoreManager(
            backend=self.vector_store_backend,
            collection_name='rag_documents',
            dimension=self.embedder.dimensions
        )
        logger.info(f"  ✓ Vector store: {self.vector_store_backend}")
        
        self.metadata_index = MetadataIndex(
            persist_path='data/indexes/metadata'
        )
        logger.info("  ✓ Components Mòdul 2 inicialitzats")
    
    def step2_process_pdfs(self):
        """Pas 2: Processar PDFs (Mòdul 1)"""
        logger.info("\n" + "="*70)
        logger.info("PAS 2: PROCESSANT PDFs (MÒDUL 1)")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # Buscar PDFs
        pdf_files = list(self.pdf_dir.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"No s'han trobat PDFs a: {self.pdf_dir}")
            logger.info("💡 Copia alguns PDFs a data/raw/pdfs/")
            return []
        
        logger.info(f"📄 PDFs trobats: {len(pdf_files)}")
        
        processed_docs = []
        
        for i, pdf_file in enumerate(pdf_files, 1):
            try:
                logger.info(f"\n[{i}/{len(pdf_files)}] Processant: {pdf_file.name}")
                
                # 1. Convertir PDF → Markdown
                logger.info("  1/5 Convertint PDF → Markdown...")
                markdown = self.pdf_converter.convert_file(str(pdf_file))
                logger.info(f"      ✓ {len(markdown):,} caràcters")
                
                # 2. Netejar text
                logger.info("  2/5 Netejant text...")
                clean_text = self.text_cleaner.clean(markdown)
                logger.info(f"      ✓ {len(clean_text):,} caràcters")
                
                # 3. Extreure metadata
                logger.info("  3/5 Extraient metadata...")
                file_metadata = self.metadata_extractor.extract_from_file(str(pdf_file))
                text_metadata = self.metadata_extractor.extract_from_text(clean_text)
                metadata = {**file_metadata, **text_metadata}
                logger.info(f"      ✓ {len(metadata)} camps")
                
                # 4. Crear document
                doc = Document(text=clean_text, metadata=metadata)
                
                # 5. Validar
                logger.info("  4/5 Validant...")
                self.validator.validate(doc)
                logger.info("      ✓ Vàlid")
                
                # 6. Guardar al DocStore
                logger.info("  5/5 Guardant al DocStore...")
                self.docstore.add_documents([doc])
                logger.info("      ✓ Guardat")
                
                processed_docs.append(doc)
                
            except Exception as e:
                logger.error(f"  ✗ Error processant {pdf_file.name}: {e}")
                continue
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"MÒDUL 1 COMPLETAT:")
        logger.info(f"  • PDFs processats: {len(processed_docs)}/{len(pdf_files)}")
        logger.info(f"  • Temps: {elapsed:.1f}s")
        logger.info(f"  • Documents al DocStore: {len(self.docstore.get_all_documents())}")
        logger.info(f"{'='*70}")
        
        self.stats['module1'] = {
            'pdfs_total': len(pdf_files),
            'pdfs_processed': len(processed_docs),
            'time_seconds': elapsed
        }
        
        return processed_docs
    
    def step3_load_from_docstore(self):
        """Pas 3: Carregar documents del DocStore"""
        logger.info("\n" + "="*70)
        logger.info("PAS 3: CARREGANT DOCUMENTS DEL DOCSTORE")
        logger.info("="*70)
        
        documents = self.docstore.get_all_documents()
        
        logger.info(f"📚 Documents carregats: {len(documents)}")
        
        if documents:
            doc_sample = documents[0]
            logger.info(f"  • Mostra: {doc_sample.metadata.get('filename', 'N/A')}")
            logger.info(f"  • Text length: {len(doc_sample.text):,} chars")
            logger.info(f"  • Metadata camps: {len(doc_sample.metadata)}")
        
        return documents
    
    def step4_chunking(self, documents):
        """Pas 4: Chunking (Mòdul 2)"""
        logger.info("\n" + "="*70)
        logger.info("PAS 4: CHUNKING (MÒDUL 2)")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        logger.info(f"🔪 Estratègia: {self.chunking_strategy}")
        logger.info(f"   Chunk size: {self.chunk_size}")
        
        nodes = self.chunker.chunk_documents(documents, show_progress=True)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # Estadístiques
        stats = self.chunker.get_statistics(nodes)
        
        logger.info(f"\n✓ Chunks generats: {len(nodes)}")
        logger.info(f"  • Longitud mitjana: {stats['avg_chunk_length']:.0f} chars")
        logger.info(f"  • Min/Max: {stats['min_chunk_length']}/{stats['max_chunk_length']}")
        logger.info(f"  • Temps: {elapsed:.1f}s")
        
        return nodes
    
    def step5_embeddings(self, nodes):
        """Pas 5: Generar embeddings (Mòdul 2)"""
        logger.info("\n" + "="*70)
        logger.info("PAS 5: GENERANT EMBEDDINGS (MÒDUL 2)")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        logger.info(f"🤖 Model: {self.embedding_model}")
        logger.info(f"   Dimensions: {self.embedder.dimensions}")
        logger.info(f"   Multilingüe: {self.embedder.is_multilingual}")
        
        nodes = self.embedder.embed_nodes(nodes, show_progress=True)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\n✓ Embeddings generats: {len(nodes)}")
        logger.info(f"  • Temps: {elapsed:.1f}s")
        logger.info(f"  • Temps/node: {elapsed/len(nodes):.3f}s")
        
        return nodes
    
    def step6_build_index(self, nodes):
        """Pas 6: Construir índex vectorial (Mòdul 2)"""
        logger.info("\n" + "="*70)
        logger.info("PAS 6: CONSTRUINT ÍNDEX VECTORIAL (MÒDUL 2)")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # Crear index builder
        self.index_builder = IndexBuilder(
            vector_store_manager=self.vector_store,
            embed_model=self.embedder.embed_model,
            persist_dir='data/indexes'
        )
        
        # Construir índex
        logger.info("🏗️  Construint índex...")
        index = self.index_builder.build_index(nodes, show_progress=True)
        
        # Indexar metadata
        logger.info("📋 Indexant metadata...")
        self.metadata_index.index_nodes(nodes)
        
        # Persistir
        logger.info("💾 Persistint...")
        self.index_builder.persist()
        self.metadata_index.persist()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"\n✓ Índex construït correctament")
        logger.info(f"  • Temps: {elapsed:.1f}s")
        
        return index
    
    def step7_test_queries(self, index):
        """Pas 7: Provar consultes"""
        logger.info("\n" + "="*70)
        logger.info("PAS 7: PROVANT CONSULTES")
        logger.info("="*70)
        
        # Queries de prova
        test_queries = [
            "Quina és la política de vacances?",
            "Com sol·licitar vacances?",
            "Quants dies de vacances tinc?"
        ]
        
        query_engine = self.index_builder.get_query_engine(similarity_top_k=3)
        
        for i, query in enumerate(test_queries, 1):
            logger.info(f"\n🔍 Query {i}: '{query}'")
            
            try:
                response = query_engine.query(query)
                
                logger.info(f"✓ Resposta:")
                logger.info(f"  {str(response)[:200]}...")
                
                if hasattr(response, 'source_nodes'):
                    logger.info(f"  Sources: {len(response.source_nodes)} nodes")
                
            except Exception as e:
                logger.error(f"✗ Error: {e}")
    
    def run(self):
        """Executar pipeline complet"""
        logger.info("\n" + "🚀 " + "="*68)
        logger.info("   PIPELINE COMPLET: MÒDUL 1 + MÒDUL 2")
        logger.info("="*70 + "\n")
        
        total_start = datetime.now()
        
        try:
            # Pas 1: Inicialitzar
            self.step1_initialize_components()
            
            # Pas 2: Processar PDFs (Mòdul 1)
            processed_docs = self.step2_process_pdfs()
            
            if not processed_docs:
                logger.warning("No hi ha documents per processar")
                return
            
            # Pas 3: Carregar del DocStore
            documents = self.step3_load_from_docstore()
            
            if not documents:
                logger.error("No s'han pogut carregar documents del DocStore")
                return
            
            # Pas 4: Chunking (Mòdul 2)
            nodes = self.step4_chunking(documents)
            
            # Pas 5: Embeddings (Mòdul 2)
            nodes = self.step5_embeddings(nodes)
            
            # Pas 6: Construir índex (Mòdul 2)
            index = self.step6_build_index(nodes)
            
            # Pas 7: Provar consultes
            self.step7_test_queries(index)
            
            # Resum final
            total_elapsed = (datetime.now() - total_start).total_seconds()
            
            logger.info("\n" + "="*70)
            logger.info("✅ PIPELINE COMPLET FINALITZAT")
            logger.info("="*70)
            logger.info(f"\n📊 RESUM:")
            logger.info(f"  • Documents processats: {len(documents)}")
            logger.info(f"  • Chunks generats: {len(nodes)}")
            logger.info(f"  • Model embeddings: {self.embedding_model}")
            logger.info(f"  • Vector store: {self.vector_store_backend}")
            logger.info(f"  • Temps total: {total_elapsed:.1f}s ({total_elapsed/60:.1f} min)")
            logger.info(f"\n💾 Dades guardades a:")
            logger.info(f"  • DocStore: {self.docstore_path}")
            logger.info(f"  • Vector Store: data/vector_stores")
            logger.info(f"  • Índex: data/indexes")
            logger.info(f"\n🎯 Pots fer consultes amb:")
            logger.info(f"  query_engine = index.as_query_engine()")
            logger.info(f"  response = query_engine.query('la teva pregunta')")
            logger.info("="*70 + "\n")
            
        except KeyboardInterrupt:
            logger.warning("\n⚠️  Pipeline interromput per l'usuari")
        except Exception as e:
            logger.error(f"\n❌ Error en el pipeline: {e}")
            logger.exception("Detalls de l'error:")


def main():
    """Funció principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pipeline Complet M1+M2')
    parser.add_argument('--pdf-dir', default='data/raw/pdfs', help='Directori amb PDFs')
    parser.add_argument('--embedding-model', default='bge-m3', help='Model d\'embeddings')
    parser.add_argument('--vector-store', default='chroma', help='Vector store backend')
    parser.add_argument('--chunk-size', type=int, default=512, help='Mida dels chunks')
    
    args = parser.parse_args()
    
    # Crear i executar pipeline
    pipeline = CompletePipeline(
        pdf_dir=args.pdf_dir,
        embedding_model=args.embedding_model,
        vector_store_backend=args.vector_store,
        chunk_size=args.chunk_size
    )
    
    pipeline.run()


if __name__ == "__main__":
    main()
