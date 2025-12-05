# modules/ingestion/docstore.py
"""
1.6 Document Store - Persistència de documents processats
Gestiona l'emmagatzematge persistent dels documents amb actualitzacions incrementals
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import json
import logging

from llama_index.core import Document
from llama_index.core.storage.docstore import SimpleDocumentStore
# from llama_index.storage.docstore.mongodb import MongoDocumentStore
# from llama_index.storage.docstore.redis import RedisDocumentStore

logger = logging.getLogger(__name__)


class DocumentStoreManager:
    """
    Gestor de persistència de documents amb suport per múltiples backends
    """
    
    SUPPORTED_BACKENDS = ['simple', 'mongodb', 'redis', 'json']
    
    def __init__(
        self,
        backend: str = 'simple',
        persist_path: str = 'data/docstore',
        **backend_kwargs
    ):
        """
        Inicialitza el gestor de docstore
        
        Args:
            backend: Tipus de backend ('simple', 'mongodb', 'redis', 'json')
            persist_path: Path per persistir dades
            **backend_kwargs: Arguments específics del backend
        """
        self.backend = backend
        self.persist_path = Path(persist_path)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        
        self.docstore = self._init_docstore(backend, **backend_kwargs)
        self.metadata_index = {}  # Índex addicional per metadades
        
        # Carregar metadata index si existeix
        self._load_metadata_index()
        
        logger.info(f"DocStore inicialitzat: backend={backend}, path={persist_path}")
    
    def _init_docstore(self, backend: str, **kwargs) -> Any:
        """Inicialitza el backend específic"""
        
        if backend == 'simple':
            docstore_file = self.persist_path / "docstore.json"
            return SimpleDocumentStore.from_persist_path(
                str(docstore_file)
            ) if docstore_file.exists() else SimpleDocumentStore()
        
        elif backend == 'mongodb':
            mongo_uri = kwargs.get('mongo_uri', 'mongodb://localhost:27017')
            db_name = kwargs.get('db_name', 'rag_system')
            return MongoDocumentStore.from_uri(
                uri=mongo_uri,
                db_name=db_name
            )
        
        elif backend == 'redis':
            redis_host = kwargs.get('redis_host', 'localhost')
            redis_port = kwargs.get('redis_port', 6379)
            return RedisDocumentStore.from_host_and_port(
                host=redis_host,
                port=redis_port
            )
        
        elif backend == 'json':
            # Backend JSON custom simple
            return None  # Gestionarem manualment
        
        else:
            raise ValueError(f"Backend no suportat: {backend}")
    
    def add_documents(
        self,
        documents: List[Document],
        update_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Afegeix documents al docstore
        
        Args:
            documents: Llista de documents
            update_existing: Actualitzar si ja existeixen
            
        Returns:
            Diccionari amb resultats
        """
        results = {
            'added': 0,
            'updated': 0,
            'skipped': 0,
            'errors': []
        }
        
        for doc in documents:
            try:
                # Verificar si ja existeix
                existing = self.get_document(doc.doc_id)
                
                if existing and not update_existing:
                    results['skipped'] += 1
                    logger.debug(f"Document saltat (existeix): {doc.doc_id}")
                    continue
                
                # Afegir timestamp
                doc.metadata['stored_at'] = datetime.now().isoformat()
                if existing:
                    doc.metadata['updated_at'] = datetime.now().isoformat()
                
                # Guardar al docstore
                if self.backend == 'json':
                    self._save_json_document(doc)
                else:
                    self.docstore.add_documents([doc])
                
                # Actualitzar índex de metadata
                self._update_metadata_index(doc)
                
                if existing:
                    results['updated'] += 1
                    logger.info(f"Document actualitzat: {doc.doc_id}")
                else:
                    results['added'] += 1
                    logger.info(f"Document afegit: {doc.doc_id}")
                
            except Exception as e:
                results['errors'].append({
                    'doc_id': doc.doc_id,
                    'error': str(e)
                })
                logger.error(f"Error guardant document {doc.doc_id}: {e}")
        
        # Persistir
        self.persist()
        
        logger.info(
            f"Documents guardats: {results['added']} nous, "
            f"{results['updated']} actualitzats, {results['skipped']} saltats"
        )
        
        return results
    
    def get_document(self, doc_id: str) -> Optional[Document]:
        """
        Obté un document per ID
        
        Args:
            doc_id: ID del document
            
        Returns:
            Document o None
        """
        try:
            if self.backend == 'json':
                return self._load_json_document(doc_id)
            else:
                return self.docstore.get_document(doc_id)
        except:
            return None
    
    def get_all_documents(self) -> List[Document]:
        """
        Obté tots els documents
        
        Returns:
            Llista de documents
        """
        if self.backend == 'json':
            return self._load_all_json_documents()
        else:
            doc_dict = self.docstore.docs
            return list(doc_dict.values())
    
    def delete_document(self, doc_id: str) -> bool:
        """
        Esborra un document
        
        Args:
            doc_id: ID del document
            
        Returns:
            True si s'ha esborrat correctament
        """
        try:
            if self.backend == 'json':
                self._delete_json_document(doc_id)
            else:
                self.docstore.delete_document(doc_id)
            
            # Actualitzar metadata index
            if doc_id in self.metadata_index:
                del self.metadata_index[doc_id]
            
            self.persist()
            logger.info(f"Document esborrat: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error esborrant document {doc_id}: {e}")
            return False
    
    def search_by_metadata(
        self,
        filters: Dict[str, Any],
        match_all: bool = True
    ) -> List[Document]:
        """
        Cerca documents per metadades
        
        Args:
            filters: Diccionari de filtres {key: value}
            match_all: Si True, han de coincidir tots els filtres
            
        Returns:
            Llista de documents que coincideixen
        """
        matching_docs = []
        
        for doc_id, metadata in self.metadata_index.items():
            matches = []
            
            for key, value in filters.items():
                if key in metadata:
                    if isinstance(value, list):
                        matches.append(metadata[key] in value)
                    else:
                        matches.append(metadata[key] == value)
                else:
                    matches.append(False)
            
            if match_all and all(matches):
                doc = self.get_document(doc_id)
                if doc:
                    matching_docs.append(doc)
            elif not match_all and any(matches):
                doc = self.get_document(doc_id)
                if doc:
                    matching_docs.append(doc)
        
        logger.info(f"Cerca per metadata: {len(matching_docs)} documents trobats")
        return matching_docs
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obté estadístiques del docstore
        
        Returns:
            Diccionari amb estadístiques
        """
        docs = self.get_all_documents()
        
        if not docs:
            return {
                'total_documents': 0,
                'total_chars': 0,
                'avg_chars': 0
            }
        
        total_chars = sum(len(doc.text) for doc in docs)
        
        # Estadístiques per tipus de fitxer
        by_type = {}
        for doc_id, metadata in self.metadata_index.items():
            file_type = metadata.get('file_type', 'unknown')
            by_type[file_type] = by_type.get(file_type, 0) + 1
        
        # Estadístiques per idioma
        by_language = {}
        for doc_id, metadata in self.metadata_index.items():
            lang = metadata.get('language', 'unknown')
            by_language[lang] = by_language.get(lang, 0) + 1
        
        return {
            'total_documents': len(docs),
            'total_chars': total_chars,
            'avg_chars': total_chars // len(docs),
            'by_file_type': by_type,
            'by_language': by_language
        }
    
    def persist(self):
        """Persisteix el docstore a disc"""
        try:
            if self.backend == 'simple':
                docstore_file = self.persist_path / "docstore.json"
                self.docstore.persist(persist_path=str(docstore_file))
            elif self.backend in ['mongodb', 'redis']:
                pass  # Ja persisteixen automàticament
            elif self.backend == 'json':
                pass  # Ja guardem a cada operació
            
            # Guardar metadata index
            self._save_metadata_index()
            
            logger.debug("DocStore persistit correctament")
            
        except Exception as e:
            logger.error(f"Error persistint docstore: {e}")
    
    def _update_metadata_index(self, doc: Document):
        """Actualitza l'índex de metadata"""
        self.metadata_index[doc.doc_id] = doc.metadata.copy()
    
    def _load_metadata_index(self):
        """Carrega l'índex de metadata"""
        index_file = self.persist_path / "metadata_index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                self.metadata_index = json.load(f)
            logger.debug(f"Metadata index carregat: {len(self.metadata_index)} documents")
    
    def _save_metadata_index(self):
        """Guarda l'índex de metadata"""
        index_file = self.persist_path / "metadata_index.json"
        with open(index_file, 'w') as f:
            json.dump(self.metadata_index, f, indent=2)
    
    # Mètodes per backend JSON custom
    def _save_json_document(self, doc: Document):
        """Guarda document en format JSON"""
        doc_file = self.persist_path / f"{doc.doc_id}.json"
        doc_data = {
            'doc_id': doc.doc_id,
            'text': doc.text,
            'metadata': doc.metadata,
            'embedding': doc.embedding
        }
        with open(doc_file, 'w', encoding='utf-8') as f:
            json.dump(doc_data, f, indent=2, ensure_ascii=False)
    
    def _load_json_document(self, doc_id: str) -> Optional[Document]:
        """Carrega document des de JSON"""
        doc_file = self.persist_path / f"{doc_id}.json"
        if not doc_file.exists():
            return None
        
        with open(doc_file, 'r', encoding='utf-8') as f:
            doc_data = json.load(f)
        
        return Document(
            doc_id=doc_data['doc_id'],
            text=doc_data['text'],
            metadata=doc_data['metadata'],
            embedding=doc_data.get('embedding')
        )
    
    def _load_all_json_documents(self) -> List[Document]:
        """Carrega tots els documents JSON"""
        docs = []
        for doc_file in self.persist_path.glob("*.json"):
            if doc_file.name != "metadata_index.json":
                doc_id = doc_file.stem
                doc = self._load_json_document(doc_id)
                if doc:
                    docs.append(doc)
        return docs
    
    def _delete_json_document(self, doc_id: str):
        """Esborra document JSON"""
        doc_file = self.persist_path / f"{doc_id}.json"
        if doc_file.exists():
            doc_file.unlink()


# Funció helper per integrar amb el pipeline
def create_persistent_pipeline(
    backend: str = 'simple',
    persist_path: str = 'data/docstore',
    **backend_kwargs
):
    """
    Crea un pipeline amb persistència integrada
    
    Args:
        backend: Backend del docstore
        persist_path: Path de persistència
        **backend_kwargs: Arguments del backend
        
    Returns:
        DocumentStoreManager configurat
    """
    from modules.ingestion import (
        PDFToMarkdownConverter,
        TextCleaner,
        MetadataExtractor,
        DocumentValidator
    )
    
    # Components del pipeline
    components = {
        'converter': PDFToMarkdownConverter(extract_images=True, image_path="data/images"),
        'cleaner': TextCleaner(remove_extra_whitespace=True, normalize_unicode=True),
        'extractor': MetadataExtractor(),
        'validator': DocumentValidator(min_text_length=100),
        'docstore': DocumentStoreManager(backend, persist_path, **backend_kwargs)
    }
    
    logger.info("Pipeline persistent creat correctament")
    return components


# Exemple d'ús integrat
def process_and_store_documents(
    pdf_dir: str,
    docstore_manager: DocumentStoreManager,
    update_existing: bool = True
) -> Dict[str, Any]:
    """
    Processa PDFs i els guarda al docstore
    
    Args:
        pdf_dir: Directori amb PDFs
        docstore_manager: Gestor del docstore
        update_existing: Actualitzar existents
        
    Returns:
        Resultats del processament
    """
    from modules.ingestion import (
        PDFToMarkdownConverter,
        TextCleaner,
        MetadataExtractor,
        DocumentValidator
    )
    
    # Components
    converter = PDFToMarkdownConverter(extract_images=True, image_path="data/images")
    cleaner = TextCleaner(remove_extra_whitespace=True, normalize_unicode=True)
    extractor = MetadataExtractor()
    validator = DocumentValidator(min_text_length=100)
    
    processed_docs = []
    errors = []
    
    # Processar cada PDF
    for pdf_file in Path(pdf_dir).glob("*.pdf"):
        try:
            logger.info(f"Processant: {pdf_file.name}")
            
            # Pipeline
            markdown = converter.convert_file(str(pdf_file))
            clean_text = cleaner.clean(markdown)
            
            file_metadata = extractor.extract_from_file(str(pdf_file))
            text_metadata = extractor.extract_from_text(clean_text)
            metadata = {**file_metadata, **text_metadata}
            
            doc = Document(text=clean_text, metadata=metadata)
            validator.validate(doc)
            
            processed_docs.append(doc)
            
        except Exception as e:
            logger.error(f"Error processant {pdf_file.name}: {e}")
            errors.append({'file': pdf_file.name, 'error': str(e)})
    
    # Guardar al docstore
    store_results = docstore_manager.add_documents(
        processed_docs,
        update_existing=update_existing
    )
    
    return {
        'processed': len(processed_docs),
        'store_results': store_results,
        'errors': errors
    }