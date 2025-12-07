# 🚀 QUICKSTART - Mòdul 2: Document Processing & Indexing

Guia ràpida per començar amb el Mòdul 2 en **menys de 10 minuts**.

---

## 📋 Pre-requisits

✅ Mòdul 1 completat (documents al DocStore)  
✅ Python 3.10+  
✅ pip actualitzat

---

## ⚡ Instal·lació Ràpida (3 minuts)

### Opció A: Setup Local (sense API keys) ⭐ RECOMANAT

```bash
# 1. Instal·lar dependències bàsiques
pip install chromadb sentence-transformers torch

# 2. Instal·lar requirements del mòdul
pip install -r modules/processing/module2_requirements.txt

# 3. Executar setup
python scripts/setup_module2.py
```

### Opció B: Setup amb OpenAI (més qualitat, requereix API key)

```bash
# 1. Instal·lar dependències
pip install chromadb openai

# 2. Configurar API key
echo "PROCESSING_OPENAI_API_KEY=sk-your-key-here" >> .env

# 3. Executar setup
python scripts/setup_module2.py
```

---

## 🎯 Test Ràpid (2 minuts)

```bash
# Executar exemples
python examples/module2_example.py
```

**Què fa?**
- ✅ Prova chunking
- ✅ Genera embeddings
- ✅ Crea vector store
- ✅ Construeix índex
- ✅ Fa cerques

---

## 🔧 Configuració Bàsica (1 minut)

Afegir al fitxer `.env`:

```bash
# CONFIGURACIÓ MÍNIMA (models locals)
PROCESSING_EMBEDDING_MODEL=bge-m3
PROCESSING_VECTOR_STORE_BACKEND=chroma
PROCESSING_CHUNK_SIZE=512
```

---

## 💻 Primer Codi (3 minuts)

### Pipeline Complet: Documents → Cerca

```python
# 1. Imports
from modules.ingestion.docstore import DocumentStoreManager
from modules.processing import build_complete_pipeline

# 2. Carregar documents (Mòdul 1)
docstore = DocumentStoreManager(backend='simple')
documents = docstore.get_all_documents()

# 3. Construir índex (tot automàtic!)
builder, index, stats = build_complete_pipeline(
    documents=documents,
    chunking_strategy='sentence',
    embedding_model='bge-m3',        # Local, gratuït
    vector_store_backend='chroma'     # Local, fàcil
)

# 4. Fer consulta
query_engine = builder.get_query_engine(similarity_top_k=5)
response = query_engine.query("Quina és la política de vacances?")

print(response)
```

**Output esperat:**
```
Els empleats tenen dret a 30 dies de vacances a l'any...
```

---

## 📊 Verificar que Funciona

```python
# Ver estadístiques
print(f"Documents processats: {stats['documents']}")
print(f"Chunks generats: {stats['nodes']}")
print(f"Model: {stats['embedding']['name']}")
```

---

## 🎨 Personalitzar

### Canviar Model d'Embeddings

```python
# Opció 1: OpenAI (millor qualitat, requereix API key)
embedding_model='openai-small'

# Opció 2: BGE-M3 (gratuït, multilingüe) ⭐ RECOMANAT
embedding_model='bge-m3'

# Opció 3: E5-Multilingual (gratuït, ràpid)
embedding_model='e5-multilingual'
```

### Canviar Vector Store

```python
# Opció 1: ChromaDB (més fàcil) ⭐ RECOMANAT per començar
vector_store_backend='chroma'

# Opció 2: Qdrant (més potent)
vector_store_backend='qdrant'

# Opció 3: Pinecone (cloud, requereix API key)
vector_store_backend='pinecone'
```

### Ajustar Chunking

```python
# Chunks petits (més precisió, més lents)
chunking_strategy='sentence'
chunk_size=256

# Chunks mitjans (balanç) ⭐ RECOMANAT
chunking_strategy='sentence'
chunk_size=512

# Chunks grans (més ràpid, menys precisió)
chunking_strategy='sentence'
chunk_size=1024
```

---

## 🔍 Cerques Avançades

### Cerca amb Filtres

```python
from modules.processing import MetadataIndex, hybrid_search

# 1. Crear metadata index
metadata_index = MetadataIndex()
metadata_index.index_nodes(nodes)

# 2. Cerca vectorial
retriever = builder.get_retriever(similarity_top_k=20)
results = retriever.retrieve("política de vacances")

# 3. Filtrar per metadata
filtered = hybrid_search(
    vector_results=[r.node_id for r in results],
    metadata_index=metadata_index,
    metadata_filters={
        'department': 'HR',
        'language': 'ca'
    }
)
```

---

## 🛠️ Troubleshooting

### Error: "No module named 'chromadb'"
```bash
pip install chromadb
```

### Error: "No module named 'sentence_transformers'"
```bash
pip install sentence-transformers torch
```

### Error: "CUDA out of memory"
```python
# Usar models més petits
embedding_model='bge-small'  # 384D en lloc de 1024D
```

### Error: "OpenAI API key not found"
```bash
# Afegir al .env
echo "PROCESSING_OPENAI_API_KEY=sk-your-key" >> .env

# O usar models locals
embedding_model='bge-m3'  # No requereix API key
```

---

## 📚 Recursos

- **README complet**: `modules/processing/module2_readme.md`
- **Exemples**: `examples/module2_example.py`
- **Configuració**: `config/processing_config.py`
- **Tests**: `python scripts/setup_module2.py`

---

## ✅ Checklist

- [ ] Mòdul 1 completat (documents al DocStore)
- [ ] Dependències instal·lades
- [ ] `.env` configurat
- [ ] `setup_module2.py` executat sense errors
- [ ] Exemples funcionen correctament
- [ ] Primer pipeline completat amb èxit

---

## 🎯 Propers Passos

1. **Experimenta** amb diferents models i estratègies
2. **Optimitza** chunk_size per als teus documents
3. **Indexa** tots els teus documents
4. **Prova** cerques amb filtres de metadata
5. **Passa** al Mòdul 3: Query & Retrieval

---

## 💡 Consells Pro

- **Usa BGE-M3** per català/espanyol (gratuït, excel·lent)
- **Chunk size 512** és un bon punt de partida
- **ChromaDB** és perfecte per començar
- **Actualitza incrementalment**, no reprocessis tot
- **Indexa metadata important** per cerca híbrida

---

## 🚨 Errors Comuns i Solucions

| Error | Solució |
|-------|---------|
| Import error | `pip install -r modules/processing/module2_requirements.txt` |
| CUDA error | Usar CPU: `embedding_model='bge-small'` |
| API key missing | Afegir al `.env` o usar models locals |
| Chunks massa grans | Reduir `chunk_size` a 256-384 |
| Vector store error | Provar amb `chroma` (més fàcil) |

---

**Temps total estimat:** 10 minuts  
**Dificultat:** ⭐⭐ (Fàcil-Mitjà)

Fet amb ❤️ per al sistema RAG empresarial
