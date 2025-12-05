# Mòdul 1: Data Ingestion Pipeline

## Descripció

El Mòdul 1 és responsable de la captura, conversió, preparació i **persistència** de documents per al sistema RAG. Gestiona la càrrega de múltiples formats, la conversió especialitzada de PDFs a Markdown, la neteja de text, l'extracció de metadades, la validació de qualitat i l'emmagatzematge persistent amb actualitzacions incrementals.

---

## Components

### 1.1 DocumentLoader
Carrega documents de diversos formats amb suport per múltiples extensions.

**Formats suportats:**
- PDF (.pdf)
- Text (.txt)
- Markdown (.md)
- Word (.docx, .doc)
- CSV (.csv)
- JSON (.json)
- HTML (.html)
- XML (.xml)

**Funcionalitats:**
- Càrrega individual o en batch
- Suport per directoris recursius
- Estadístiques de fitxers
- Filtratge per extensions

### 1.2 PDFToMarkdownConverter
Conversió especialitzada de PDFs a Markdown mantenint l'estructura.

**Eina utilitzada:** PyMuPDF4LLM (recomanat)

**Característiques:**
- Preserva headers, taules i llistes
- Extracció opcional d'imatges
- Metadades automàtiques
- Suport per pàgines específiques
- Processament en batch

**Alternatives disponibles:**
- LlamaParse (pagament, millor qualitat)
- Docling (gratuït, molt potent)
- Marker (gratuït, ràpid)

### 1.3 TextCleaner
Neteja i normalització de text.

**Operacions:**
- Eliminació d'espais excessius
- Normalització Unicode
- Eliminació de línies massa curtes
- Neteja d'artifacts de PDFs
- Eliminació de headers/footers repetitius

### 1.4 MetadataExtractor
Extracció i enriquiment de metadades.

**Metadades automàtiques:**
- Informació del fitxer (nom, ruta, mida)
- Dates (creació, modificació)
- Tipus MIME
- Hash del fitxer (per duplicats)
- Estadístiques de text
- Detecció d'idioma

**Metadades personalitzables:**
- Departament
- Categoria
- Tags
- Autor
- Nivell d'accés
- Qualsevol camp personalitzat

### 1.5 DocumentValidator
Validació de qualitat i completesa.

**Validacions:**
- ✅ Text no buit (longitud mínima/màxima)
- ✅ Metadades obligatòries presents
- ✅ Format vàlid i encoding correcte
- ✅ Detecció de duplicats (hash)
- ✅ Validació en batch amb reporting

### 1.6 DocumentStore
Persistència de documents amb actualitzacions incrementals.

**Característiques:**
- Emmagatzematge persistent de documents processats
- Actualitzacions incrementals (només nous/modificats)
- Cerca ràpida per metadades
- Múltiples backends (SimpleDocStore, MongoDB, Redis, JSON)
- Tracking d'estat amb timestamps
- Estadístiques i monitoratge
- Sincronització amb VectorStore (Mòdul 2)

**Backends disponibles:**
- **SimpleDocStore** - JSON local, ideal per començar
- **MongoDB** - Base de dades documental escalable
- **Redis** - Cache distribuït d'alta velocitat
- **Custom JSON** - Implementació lleugera

**Operacions:**
- `add_documents()` - Afegir/actualitzar documents
- `get_document(doc_id)` - Recuperar document
- `get_all_documents()` - Obtenir tots
- `delete_document(doc_id)` - Esborrar document
- `search_by_metadata(filters)` - Cerca per filtres
- `get_statistics()` - Estadístiques del store

---

## Arquitectura de Persistència

El Mòdul 1 implementa una estratègia de persistència en **3 capes**:

### Capa 1: Markdown Files
```
data/processed/markdown/
├── document1.md
├── document2.md
└── document3.md
```
- ✅ Font de veritat humana (editable)
- ✅ Versionable amb Git
- ✅ Fàcil revisió manual

### Capa 2: DocStore
```
data/docstore/
├── docstore.json
└── metadata_index.json
```
- ✅ Documents processats amb metadata
- ✅ Actualitzacions incrementals
- ✅ Cerca per filtres

### Capa 3: VectorStore (Mòdul 2)
```
data/vector_stores/
└── qdrant/
```
- ✅ Embeddings per cerca semàntica
- ✅ Enllaçat amb DocStore

**Flux:**
PDF → Markdown (editable) → DocStore (gestionable) → VectorStore (cercable)

---

## Instal·lació

### Requisits
```bash
Python 3.10+
```

### Dependències
```bash
pip install -r requirements_module1.txt
```

**Dependències principals:**
- `llama-index>=0.10.0` - Framework base
- `pymupdf4llm>=0.0.5` - Conversió PDF a Markdown
- `PyMuPDF>=1.23.0` - Processament PDF
- `pydantic>=2.0.0` - Configuració i validació
- `langdetect>=1.0.9` - Detecció d'idioma

### Setup inicial
```bash
python scripts/setup_module1.py
```

Aquest script:
- Crea l'estructura de directoris
- Testa tots els components
- Crea fitxers de mostra
- Mostra instruccions

---

## Ús Bàsic

### 1. Convertir un PDF a Markdown

```python
from modules.ingestion import PDFToMarkdownConverter

converter = PDFToMarkdownConverter(
    extract_images=True,
    image_path="data/images"
)

markdown_text = converter.convert_file("document.pdf")
print(markdown_text)
```

### 2. Pipeline complet amb persistència

```python
from modules.ingestion import (
    PDFToMarkdownConverter,
    TextCleaner,
    MetadataExtractor,
    DocumentValidator
)
from modules.ingestion.docstore import DocumentStoreManager
from llama_index.core import Document

# Inicialitzar components
converter = PDFToMarkdownConverter(extract_images=True, image_path="data/images")
cleaner = TextCleaner(remove_extra_whitespace=True, normalize_unicode=True)
extractor = MetadataExtractor(custom_fields={'department': 'IT'})
validator = DocumentValidator(min_text_length=100)

# Inicialitzar DocStore
docstore = DocumentStoreManager(
    backend='simple',
    persist_path='data/docstore'
)

# Processar
markdown = converter.convert_file("document.pdf")
clean_text = cleaner.clean(markdown)
metadata = extractor.extract_from_file("document.pdf")

# Crear i validar document
doc = Document(text=clean_text, metadata=metadata)
validator.validate(doc)

# Guardar al DocStore (persistent!)
results = docstore.add_documents([doc])
print(f"Document guardat: {results}")
```

### 3. Recuperar documents existents

```python
from modules.ingestion.docstore import DocumentStoreManager

# Crear DocStore (carrega automàticament els existents)
docstore = DocumentStoreManager(
    backend='simple',
    persist_path='data/docstore'
)

# Obtenir tots
all_docs = docstore.get_all_documents()
print(f"Documents disponibles: {len(all_docs)}")

# Obtenir un específic
doc = docstore.get_document("doc_id")

# Cerca per metadata
it_docs = docstore.search_by_metadata({'department': 'IT'})
```

### 4. Actualitzacions incrementals

```python
from modules.ingestion.docstore import process_and_store_documents

# Processar i guardar (només nous o modificats)
results = process_and_store_documents(
    pdf_dir="data/raw/pdfs",
    docstore_manager=docstore,
    update_existing=True  # Actualitza si file_hash canvia
)

print(f"Nous: {results['store_results']['added']}")
print(f"Actualitzats: {results['store_results']['updated']}")
print(f"Saltats: {results['store_results']['skipped']}")
```

---

## Configuració

### Variables d'entorn (.env)

```bash
# Directoris
INGESTION_RAW_DATA_DIR=data/raw
INGESTION_PROCESSED_DATA_DIR=data/processed
INGESTION_MARKDOWN_OUTPUT_DIR=data/processed/markdown
INGESTION_IMAGES_DIR=data/images

# PDF Converter
INGESTION_PDF_EXTRACT_IMAGES=true
INGESTION_PDF_IMAGE_DPI=150

# Text Cleaner
INGESTION_REMOVE_EXTRA_WHITESPACE=true
INGESTION_NORMALIZE_UNICODE=true
INGESTION_MIN_LINE_LENGTH=3

# Validator
INGESTION_MIN_TEXT_LENGTH=100
INGESTION_CHECK_DUPLICATES=true

# Logging
INGESTION_LOG_LEVEL=INFO
INGESTION_LOG_FILE=logs/ingestion.log
```

### Configuració programàtica

```python
from config.ingestion_config import IngestionConfig

config = IngestionConfig(
    RAW_DATA_DIR="custom/path",
    MIN_TEXT_LENGTH=200,
    PDF_EXTRACT_IMAGES=False
)
```

---

## Exemples Avançats

### Processar amb filtres

```python
from modules.ingestion import DocumentLoader

loader = DocumentLoader()

# Només PDFs
documents = loader.load_directory(
    "data/raw",
    required_exts=['.pdf'],
    recursive=True
)
```

### Metadata personalitzada per departament

```python
extractor = MetadataExtractor(
    custom_fields={
        'department': 'Legal',
        'confidentiality': 'Confidential',
        'retention_years': 7
    }
)

metadata = extractor.extract_from_file("contract.pdf")
```

### Validació amb reporting detallat

```python
validator = DocumentValidator(
    min_text_length=50,
    required_metadata=['filename', 'department']
)

results = validator.validate_batch(
    documents,
    stop_on_error=False
)

print(f"Vàlids: {results['valid']}/{results['total']}")
for error in results['errors']:
    print(f"  ✗ {error['filename']}: {error['error']}")
```

---

## Bones Pràctiques

### ✅ DO

- **Convertir PDFs a Markdown primer** - Millora significativament la qualitat del chunking
- **Utilitzar DocStore per persistència** - Documents es mantenen entre execucions
- **Implementar actualitzacions incrementals** - Només processar nous/modificats
- **Mantenir metadades riques** - Essencial per filtrar i cercar
- **Validar sempre** - Detecta problemes abans d'indexar
- **Utilitzar hash per duplicats** - Evita contingut redundant
- **Preservar estructura** - Headers i taules són importants pel context
- **Fer backup de les 3 capes** - Markdown + DocStore + VectorStore
- **Sincronitzar DocStore amb VectorStore** - Mantenir consistència

### ❌ DON'T

- **No processar tot cada vegada** - Usa actualitzacions incrementals
- **No perdre la metadata** - És fonamental per cerca i filtres
- **No convertir imatges sense OCR** - Perdràs informació textual
- **No eliminar metadata automàtica** - Pot ser útil més endavant
- **No saltar la validació** - Documents invàlids causen problemes posteriors
- **No processar fitxers massa grans sense batch** - Gestiona memòria
- **No usar neteja agressiva** - Pots perdre context important
- **No oblidar sincronitzar DocStore i VectorStore** - Provoca inconsistències

---

## Troubleshooting

### Error: "PyMuPDF no trobat"
```bash
pip install PyMuPDF pymupdf4llm
```

### Error: "DocStore corrupted"
```bash
# Regenerar DocStore
rm -rf data/docstore/*
python scripts/setup_module1.py
```

### Error: "Text massa curt després de neteja"
Ajusta `MIN_TEXT_LENGTH` o revisa si el PDF conté text real:
```python
cleaner = TextCleaner(min_line_length=2)
validator = DocumentValidator(min_text_length=50)
```

### Error: "Metadata field missing"
Assegura't que els camps requerits existeixen:
```python
validator = DocumentValidator(
    required_metadata=['filename']  # Només essencials
)
```

### Documents no s'actualitzen
Verifica que el hash es calcula correctament:
```python
# Forçar actualització
docstore.add_documents(docs, update_existing=True)
```

### Cercar per metadata no funciona
Verifica que la metadata està indexada:
```python
# Comprovar metadata
stats = docstore.get_statistics()
print(stats)

# Rebuild metadata index si cal
docstore._load_metadata_index()
```

### DocStore massa gran i lent
Canviar a backend escalable:
```python
# Opció 1: MongoDB
docstore = DocumentStoreManager(
    backend='mongodb',
    persist_path='data/docstore',
    mongo_uri='mongodb://localhost:27017',
    db_name='rag_system'
)

# Opció 2: Redis
docstore = DocumentStoreManager(
    backend='redis',
    persist_path='data/docstore',
    redis_host='localhost',
    redis_port=6379
)
```

### PDFs amb taules mal convertides
Prova LlamaParse per millor qualitat:
```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key="tu_api_key",
    result_type="markdown"
)
markdown = parser.load_data("complex_table.pdf")
```

### Detecció d'idioma incorrecta
Instal·la `langdetect` per millor precisió:
```bash
pip install langdetect
```

---

## Tests

### Executar tests unitaris
```bash
pytest tests/unit/test_ingestion.py -v
```

### Tests amb coverage
```bash
pytest tests/unit/test_ingestion.py --cov=modules.ingestion --cov-report=html
```

### Test ràpid de components
```bash
python scripts/setup_module1.py
```

---

## Rendiment

### Benchmark (ordinador mitjà)

| Operació | Temps | Notes |
|----------|-------|-------|
| Convertir PDF (10 pàg) | ~2-3s | PyMuPDF4LLM |
| Neteja text (100KB) | ~0.1s | TextCleaner |
| Extracció metadata | ~0.05s | MetadataExtractor |
| Validació document | ~0.02s | DocumentValidator |

### Optimitzacions

**Processament en batch:**
```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def process_pdf(pdf_path):
    converter = PDFToMarkdownConverter()
    return converter.convert_file(pdf_path)

with ProcessPoolExecutor(max_workers=4) as executor:
    pdfs = list(Path("data/raw").glob("*.pdf"))
    results = executor.map(process_pdf, pdfs)
```

**Caching de metadata:**
```python
import pickle

# Guardar metadata
with open("metadata_cache.pkl", "wb") as f:
    pickle.dump(metadata_dict, f)

# Carregar metadata
with open("metadata_cache.pkl", "rb") as f:
    metadata_dict = pickle.load(f)
```

---

## Roadmap

- [ ] Suport per OCR (Tesseract) per imatges
- [ ] Integració amb SharePoint/Google Drive
- [ ] Processament incremental automàtic (watch folders)
- [ ] UI web per gestionar documents i DocStore
- [ ] Suport per documents escanejats
- [ ] Detecció automàtica d'idioma avançada
- [ ] Extracció d'entitats (NER) a metadata
- [ ] Sincronització bidireccional DocStore ↔ VectorStore
- [ ] Backend PostgreSQL per DocStore
- [ ] Deduplicació intel·ligent basada en contingut semàntic
- [ ] Versionat de documents amb diff visualització

---

## Recursos

- [Documentació PyMuPDF4LLM](https://pymupdf.readthedocs.io/)
- [LlamaIndex Documentation](https://docs.llamaindex.ai/)
- [LlamaParse](https://docs.cloud.llamaindex.ai/llamaparse/getting_started)
- [Docling (IBM)](https://github.com/DS4SD/docling)

---

## Suport

Per problemes o preguntes sobre el Mòdul 1:
- Revisa la secció Troubleshooting
- Consulta els exemples a `examples/module1_example.py`
- Executa `python scripts/setup_module1.py` per diagnosticar

---

**Preparat per passar al Mòdul 2?**
Un cop tinguis els documents convertits a Markdown, validats i guardats al DocStore amb persistència, estàs llest per al **Mòdul 2: Processing & Indexing** (Chunking, Embeddings i VectorStore amb sincronització).

**Avantatges de tenir persistència abans del Mòdul 2:**
- ✅ Documents processats disponibles immediatament
- ✅ Reindexar VectorStore sense reprocessar PDFs
- ✅ Actualitzacions incrementals fàcils
- ✅ Metadata rica per millor chunking
- ✅ Tracking complet del pipeline

---

**Última actualització:** Desembre 2024  
**Versió:** 1.1.0 (amb DocumentStore)