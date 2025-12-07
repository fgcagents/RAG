# Mòdul 2: Document Processing & Indexing

## Descripció

El Mòdul 2 és responsable del **processament avançat i emmagatzematge vectorial** de documents per al sistema RAG. Gestiona el chunking intel·ligent, generació d'embeddings multilingües, emmagatzematge vectorial amb múltiples backends, construcció d'índexs i cerca híbrida amb metadata.

---

## Components

### 2.1 Chunking Strategy
Divisió intel·ligent de documents amb múltiples estratègies.

**Estratègies disponibles:**
- **Sentence**: Divisió per sentències (default)
- **Semantic**: Divisió semàntica basada en similaritat
- **Sentence Window**: Finestres de sentències amb context
- **Fixed Size**: Mida fixa amb overlap
- **Recursive**: Recursiu per estructura de document

**Funcionalitats:**
- Adaptació automàtica segons tipus de document
- Preservació de metadata del document original
- Estadístiques detallades de chunking
- Configuració flexible de chunk_size i overlap

### 2.2 Embedding Generator
Generació d'embeddings amb models multilingües.

**Models suportats:**

**OpenAI:**
- text-embedding-3-small (1536D, multilingüe)
- text-embedding-3-large (3072D, multilingüe)
- text-embedding-ada-002 (1536D, multilingüe)

**HuggingFace - BGE:**
- BAAI/bge-large-en-v1.5 (1024D, anglès)
- BAAI/bge-small-en-v1.5 (384D, anglès)
- BAAI/bge-m3 (1024D, multilingüe) ⭐ Recomanat català/espanyol

**E5 Models:**
- intfloat/e5-large-v2 (1024D, anglès)
- intfloat/multilingual-e5-large (1024D, multilingüe) ⭐

**Sentence Transformers:**
- paraphrase-multilingual-mpnet-base-v2 (768D, multilingüe)

**Característiques:**
- Processament en batch
- Suport multilingüe (català, espanyol, anglès)
- Models locals i en cloud
- Embedding híbrid (combinar models)

### 2.3 Vector Store Manager
Gestió unificada de bases de dades vectorials.

**Backends suportats:**
- **Qdrant** ⭐ Recomanat - Local i cloud, escalable
- **ChromaDB** - Lightweight, fàcil d'usar
- **Pinecone** - Cloud managed, escala automàtica
- **FAISS** - Alta velocitat, no persistent

**Operacions:**
- `add_nodes()` - Afegir nodes amb embeddings
- `query()` - Cerca vectorial amb filtres
- `delete_nodes()` - Eliminar nodes
- `clear_collection()` - Netejar col·lecció
- `persist()` - Persistir a disc

### 2.4 Index Builder
Construcció i actualització d'índexs vectorials.

**Funcionalitats:**
- Construcció d'índex des de documents
- Actualització incremental
- Persistència i càrrega d'índexs
- Query engine i retriever
- Metadata de versionat

**Operacions:**
- `build_index()` - Construir des de nodes
- `build_from_documents()` - Pipeline complet
- `update_index()` - Actualitzar amb nous nodes
- `load_index()` - Carregar índex existent
- `rebuild_index()` - Reconstruir completament

### 2.5 Metadata Index
Índex de metadata per filtres i cerca avançada.

**Funcionalitats:**
- Índexs invertits per camp
- Cerca per metadata
- Cerca per rang de valors
- Estadístiques de camps
- Persistència eficient

**Operacions:**
- `index_nodes()` - Indexar metadata
- `search()` - Cerca amb filtres
- `range_search()` - Cerca per rang
- `get_unique_values()` - Valors únics d'un camp
- `hybrid_search()` - Cerca híbrida vectorial+metadata

---

## Instal·lació

### Requisits
```bash
Python 3.10+
```

### Dependències
```bash
pip install -r modules/processing/module2_requirements.txt
```

**Dependències principals:**
- `llama-index>=0.10.0` - Framework base
- `llama-index-embeddings-openai>=0.1.0` - Embeddings OpenAI
- `llama-index-embeddings-huggingface>=0.1.0` - Embeddings HF
- `llama-index-vector-stores-qdrant>=0.1.0` - Vector store Qdrant
- `qdrant-client>=1.7.0` - Cliente Qdrant
- `sentence-transformers>=2.2.0` - Modelos de embeddings
- `torch>=2.0.0` - Backend neural

### Setup inicial
```bash
python scripts/setup_module2.py
```

---

## Ús Bàsic

### 1. Pipeline Complet: Documents → Índex Vectorial

```python
from modules.ingestion.docstore import DocumentStoreManager
from modules.processing import (
    ChunkingStrategy,
    EmbeddingGenerator,
    VectorStoreManager,
    IndexBuilder
)

# 1. Carregar documents del DocStore (Mòdul 1)
docstore = DocumentStoreManager(backend='simple', persist_path='data/docstore')
documents = docstore.get_all_documents()

# 2. Chunking
chunker = ChunkingStrategy(
    strategy='sentence',
    chunk_size=512,
    chunk_overlap=50
)
nodes = chunker.chunk_documents(documents)

# 3. Embeddings
embedder = EmbeddingGenerator(
    model_name='bge-m3',  # Multilingüe: català, espanyol, anglès
    batch_size=100
)
nodes = embedder.embed_nodes(nodes)

# 4. Vector Store
vector_store = VectorStoreManager(
    backend='qdrant',
    collection_name='rag_documents',
    dimension=embedder.dimensions
)

# 5. Index Builder
builder = IndexBuilder(
    vector_store_manager=vector_store,
    embed_model=embedder.embed_model
)
index = builder.build_index(nodes)

# 6. Persistir
builder.persist()

print(f"Índex creat amb {len(nodes)} chunks!")
```

### 2. Pipeline Simplificat amb Helper

```python
from modules.processing import build_complete_pipeline

# Tot en una funció!
builder, index, stats = build_complete_pipeline(
    documents=documents,
    chunking_strategy='sentence',
    embedding_model='bge-m3',
    vector_store_backend='qdrant'
)

print(f"Pipeline completat:")
print(f"  - Documents: {stats['documents']}")
print(f"  - Chunks: {stats['nodes']}")
print(f"  - Model: {stats['embedding']['name']}")
```

### 3. Cerca Vectorial

```python
# Obtenir query engine
query_engine = builder.get_query_engine(similarity_top_k=10)

# Fer una consulta
response = query_engine.query("Quina és la política de vacances?")

print(f"Resposta: {response}")
print(f"Sources: {response.source_nodes}")
```

### 4. Cerca amb Filtres de Metadata

```python
from modules.processing import MetadataIndex, hybrid_search

# Crear metadata index
metadata_index = MetadataIndex()
metadata_index.index_nodes(nodes)

# Cerca vectorial
retriever = builder.get_retriever(similarity_top_k=20)
query_embedding = embedder.generate_query_embedding("política de vacances")
vector_results = vector_store.query(query_embedding, top_k=20)

# Aplicar filtres de metadata
filtered_results = hybrid_search(
    vector_results=[n.node_id for n in vector_results.nodes],
    metadata_index=metadata_index,
    metadata_filters={
        'department': 'HR',
        'language': 'ca'
    }
)

print(f"Resultats filtrats: {len(filtered_results)}")
```

### 5. Actualització Incremental

```python
# Nous documents
new_documents = docstore.get_all_documents()  # Amb nous afegits

# Chunk només els nous
new_nodes = chunker.chunk_documents(new_documents[-5:])

# Embeddings
new_nodes = embedder.embed_nodes(new_nodes)

# Actualitzar índex
results = builder.update_index(new_nodes)

print(f"Actualització: {results['nodes_added']} nous chunks")
```

---

## Configuració

### Variables d'entorn (.env)

```bash
# =================================================================
# MÓDULO 2: PROCESSING & INDEXING
# =================================================================

# Chunking
PROCESSING_CHUNKING_STRATEGY=sentence
PROCESSING_CHUNK_SIZE=512
PROCESSING_CHUNK_OVERLAP=50

# Embeddings
PROCESSING_EMBEDDING_MODEL=bge-m3
PROCESSING_EMBEDDING_BATCH_SIZE=100
PROCESSING_OPENAI_API_KEY=sk-...  # Si uses OpenAI

# Vector Store
PROCESSING_VECTOR_STORE_BACKEND=qdrant
PROCESSING_VECTOR_STORE_PATH=data/vector_stores
PROCESSING_COLLECTION_NAME=rag_documents

# Qdrant (si uses cloud)
# PROCESSING_QDRANT_URL=https://your-cluster.qdrant.io
# PROCESSING_QDRANT_API_KEY=your-key

# Index
PROCESSING_INDEX_PERSIST_DIR=data/indexes
PROCESSING_INDEX_NAME=main_index

# Retrieval
PROCESSING_SIMILARITY_TOP_K=10

# Metadata Index
PROCESSING_METADATA_INDEX_PATH=data/indexes/metadata
PROCESSING_METADATA_FIELDS_TO_INDEX=filename,file_type,department,category,language

# Performance
PROCESSING_MAX_WORKERS_EMBEDDING=4
PROCESSING_BATCH_SIZE_INDEXING=100

# Entorn
ENVIRONMENT=development
DEBUG=true
```

### Configuració programàtica

```python
from config.processing_config import ProcessingConfig

config = ProcessingConfig(
    CHUNKING_STRATEGY='semantic',
    EMBEDDING_MODEL='openai-small',
    VECTOR_STORE_BACKEND='chroma',
    CHUNK_SIZE=256
)
```

---

## Exemples Avançats

### Chunking Adaptatiu

```python
from modules.processing import AdaptiveChunker

# Detecta automàticament millor estratègia
adaptive = AdaptiveChunker()
nodes = adaptive.chunk_document(document, auto_detect=True)
```

### Embedding Híbrid

```python
from modules.processing import HybridEmbeddingGenerator

# Combinar dos models
hybrid = HybridEmbeddingGenerator(
    primary_model='openai-small',
    secondary_model='bge-m3'
)

# Usar secundari per català/espanyol
nodes_es = hybrid.embed_nodes(nodes_espanyol, use_secondary=True)
```

### Cerca Avançada amb Metadata

```python
# Cerca per rang de dates
node_ids = metadata_index.range_search(
    field='created_at',
    min_value='2024-01-01',
    max_value='2024-12-31'
)

# Obtenir valor counts
departments = metadata_index.get_value_counts('department')
print(departments)  # {'IT': 45, 'Legal': 23, 'HR': 18}
```

---

## Bones Pràctiques

### ✅ DO

- **Usar models multilingües** per català/espanyol (bge-m3, e5-multilingual)
- **Chunk size segons model** - 512 per OpenAI, 384 per bge-small
- **Persistir índexs regularment** - Evita reprocessar
- **Usar Qdrant local** per desenvolupament, cloud per producció
- **Indexar metadata important** - Accelera cerca híbrida
- **Validar embeddings** - Verificar dimensions correctes
- **Batch processing** - Processar en lots per eficiència
- **Mantenir sincronització** - DocStore ↔ VectorStore
- **Actualitzacions incrementals** - Només nous/modificats

### ❌ DON'T

- **No usar chunk_size massa petit** - Perd context (<128)
- **No usar chunk_size massa gran** - Perd precisió (>1024)
- **No oblidar overlap** - Millora continuïtat (recomanat: 10-20%)
- **No barrejar dimensions** - Embeddings incompatibles
- **No processar tot cada vegada** - Usa actualitzacions incrementals
- **No usar FAISS per persistència** - No és persistent
- **No ignorar metadata** - Essencial per filtres
- **No oblidar API keys** - OpenAI/Pinecone requereixen keys
- **No usar models no multilingües** per català - Pèrdua de qualitat

---

## Comparativa de Models d'Embeddings

| Model | Dimensions | Multilingüe | Local | Cost | Qualitat CA/ES |
|-------|-----------|-------------|-------|------|----------------|
| **OpenAI Small** | 1536 | ✅ | ❌ | 💰 | ⭐⭐⭐⭐⭐ |
| **OpenAI Large** | 3072 | ✅ | ❌ | 💰💰 | ⭐⭐⭐⭐⭐ |
| **BGE-M3** | 1024 | ✅ | ✅ | Gratuït | ⭐⭐⭐⭐⭐ |
| **E5-Multilingual** | 1024 | ✅ | ✅ | Gratuït | ⭐⭐⭐⭐ |
| **BGE-Large** | 1024 | ❌ | ✅ | Gratuït | ⭐⭐⭐ (EN) |
| **Paraphrase-ML** | 768 | ✅ | ✅ | Gratuït | ⭐⭐⭐ |

**Recomanació:**
- **Desenvolupament**: BGE-M3 (gratuït, local, multilingüe)
- **Producció amb pressupost**: OpenAI Small
- **Producció sense pressupost**: E5-Multilingual

---

## Comparativa de Vector Stores

| Backend | Local | Cloud | Persistent | Escalabilitat | Dificultat |
|---------|-------|-------|-----------|--------------|------------|
| **Qdrant** | ✅ | ✅ | ✅ | Alta | Fàcil |
| **ChromaDB** | ✅ | ❌ | ✅ | Mitjana | Molt fàcil |
| **Pinecone** | ❌ | ✅ | ✅ | Molt alta | Fàcil |
| **FAISS** | ✅ | ❌ | ❌ | Baixa | Mitjà |

**Recomanació:**
- **Desenvolupament**: ChromaDB o Qdrant local
- **Producció petita**: Qdrant local
- **Producció gran**: Qdrant cloud o Pinecone

---

## Troubleshooting

### Error: "OpenAI API key not found"
```bash
# Afegir al .env
PROCESSING_OPENAI_API_KEY=sk-your-key-here
```

### Error: "Qdrant connection refused"
```bash
# Iniciar Qdrant local amb Docker
docker run -p 6333:6333 qdrant/qdrant

# O instal·lar localment
pip install qdrant-client
```

### Error: "CUDA out of memory"
```python
# Usar models més petits o batch_size menor
embedder = EmbeddingGenerator(
    model_name='bge-small',  # Més petit
    batch_size=10  # Batch més petit
)
```

### Error: "Embedding dimensions mismatch"
```python
# Verificar dimensions del model
print(embedder.dimensions)  # Ex: 1024

# Crear vector store amb dimensions correctes
vector_store = VectorStoreManager(
    backend='qdrant',
    dimension=embedder.dimensions  # ✅ Correcte
)
```

### Chunks massa grans o petits
```python
# Ajustar segons model
config = {
    'openai-small': 512,
    'bge-large': 512,
    'bge-small': 384,
    'e5-large': 512
}

chunker = ChunkingStrategy(
    strategy='sentence',
    chunk_size=config[model_name]
)
```

---

## Tests

### Executar tests unitaris
```bash
pytest tests/unit/test_processing.py -v
```

### Test ràpid de components
```bash
python scripts/setup_module2.py
```

---

## Rendiment

### Benchmark (ordinador mitjà)

| Operació | Temps | Notes |
|----------|-------|-------|
| Chunking 100 docs | ~5s | Sentence strategy |
| Embeddings 1000 chunks (OpenAI) | ~10s | Batch 100 |
| Embeddings 1000 chunks (BGE local) | ~30s | CPU, batch 100 |
| Vector Store insert 1000 | ~2s | Qdrant local |
| Query top-10 | ~0.05s | Qdrant local |

### Optimitzacions

**Processament en batch:**
```python
# Processar en lots grans
embedder = EmbeddingGenerator(
    model_name='bge-m3',
    batch_size=200  # Més ràpid
)
```

**Parallel chunking:**
```python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor(max_workers=4) as executor:
    results = executor.map(chunker.chunk_text, texts)
```

---

## Integració amb Mòdul 1

```python
# Pipeline complet: Mòdul 1 → Mòdul 2
from modules.ingestion.docstore import DocumentStoreManager
from modules.processing import build_complete_pipeline

# 1. Carregar des del DocStore (Mòdul 1)
docstore = DocumentStoreManager(backend='simple')
documents = docstore.get_all_documents()

# 2. Processar i indexar (Mòdul 2)
builder, index, stats = build_complete_pipeline(
    documents=documents,
    chunking_strategy='sentence',
    embedding_model='bge-m3',
    vector_store_backend='qdrant'
)

# 3. Query
response = index.as_query_engine().query("La meva consulta")
print(response)
```

---

## Roadmap

- [ ] Suport per embeddings multimodals (text + imatge)
- [ ] Chunking amb Llama 3.2 per estructura
- [ ] Reranking amb Cross-Encoders
- [ ] Cache d'embeddings
- [ ] Compressió de vectors
- [ ] Suport per Weaviate
- [ ] Quantització de models
- [ ] Indexació asíncrona
- [ ] Monitoreig de qualitat d'embeddings
- [ ] A/B testing de chunking strategies

---

## Recursos

- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [BGE Models](https://huggingface.co/BAAI)
- [Sentence Transformers](https://www.sbert.net/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

---

## Suport

Per problemes o preguntes sobre el Mòdul 2:
- Revisa la secció Troubleshooting
- Consulta els exemples a `examples/module2_example.py`
- Executa `python scripts/setup_module2.py` per diagnosticar

---

**Preparat per passar al Mòdul 3?**
Un cop tinguis els documents indexats amb embeddings i emmagatzemats al VectorStore, estàs llest per al **Mòdul 3: Query & Retrieval** (Cerca avançada, reranking i generació augmentada).

---

**Última actualització:** Desembre 2024  
**Versió:** 2.0.0
