"""
RAG-based Q&A system for legal documents.
"""

import logging
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import hashlib

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage

from src.models import SourceCitation


logger = logging.getLogger(__name__)


class LegalQASystem:
    """RAG-based Q&A system for legal documents."""

    def __init__(
        self,
        collection_name: str = "legal_documents",
        chroma_persist_dir: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """
        Initialize legal Q&A system.

        Args:
            collection_name: Name of ChromaDB collection
            chroma_persist_dir: Directory to persist ChromaDB data
            openai_api_key: OpenAI API key
        """
        self.collection_name = collection_name
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # Initialize ChromaDB
        self.chroma_persist_dir = chroma_persist_dir or os.path.join(
            os.path.expanduser("~"), ".legal-compliance-agent", "chroma"
        )
        os.makedirs(self.chroma_persist_dir, exist_ok=True)

        self.chroma_client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.chroma_persist_dir,
            )
        )

        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Legal documents for Q&A"}
            )
            logger.info(f"Created new collection: {collection_name}")

        # Initialize embeddings
        if self.openai_api_key:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            self.llm = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.1,
                openai_api_key=self.openai_api_key
            )
        else:
            logger.warning("OpenAI API key not provided, using fallback embeddings")
            self.embeddings = None
            self.llm = None

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        logger.info("LegalQASystem initialized")

    def add_document(
        self,
        document_text: str,
        document_id: Optional[str] = None,
        document_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a document to the knowledge base.

        Args:
            document_text: Text of the document
            document_id: Optional document ID (generated if not provided)
            document_name: Optional document name
            metadata: Optional metadata for the document

        Returns:
            Document ID
        """
        if not document_id:
            document_id = str(uuid.uuid4())

        logger.info(f"Adding document {document_id} to knowledge base")

        # Split document into chunks
        chunks = self.text_splitter.split_text(document_text)
        logger.debug(f"Split document into {len(chunks)} chunks")

        # Prepare metadata
        chunk_metadata = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {
                "document_id": document_id,
                "document_name": document_name or document_id,
                "chunk_index": i,
                "chunk_count": len(chunks),
                "timestamp": datetime.utcnow().isoformat(),
            }
            if metadata:
                chunk_meta.update(metadata)
            chunk_metadata.append(chunk_meta)

        # Generate chunk IDs
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        # Generate embeddings and add to collection
        try:
            if self.embeddings:
                # Use OpenAI embeddings
                embeddings_list = self.embeddings.embed_documents(chunks)
                self.collection.add(
                    embeddings=embeddings_list,
                    documents=chunks,
                    metadatas=chunk_metadata,
                    ids=chunk_ids,
                )
            else:
                # Use ChromaDB default embeddings
                self.collection.add(
                    documents=chunks,
                    metadatas=chunk_metadata,
                    ids=chunk_ids,
                )

            logger.info(f"Successfully added document {document_id}")
            return document_id

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise

    def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        max_sources: int = 5,
        include_citations: bool = True,
    ) -> Dict:
        """
        Query the legal document knowledge base.

        Args:
            question: Question to answer
            document_ids: Optional list of document IDs to search within
            max_sources: Maximum number of sources to retrieve
            include_citations: Whether to include citations

        Returns:
            Dictionary with answer, confidence, and citations
        """
        logger.info(f"Processing query: {question[:100]}...")
        start_time = datetime.now()

        # Generate query embedding and search
        try:
            if self.embeddings:
                query_embedding = self.embeddings.embed_query(question)
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_sources,
                    where={"document_id": {"$in": document_ids}} if document_ids else None,
                )
            else:
                results = self.collection.query(
                    query_texts=[question],
                    n_results=max_sources,
                    where={"document_id": {"$in": document_ids}} if document_ids else None,
                )

            # Extract results
            documents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            if not documents:
                logger.warning("No relevant documents found")
                return {
                    "question": question,
                    "answer": "I couldn't find relevant information in the knowledge base to answer this question.",
                    "confidence": 0.0,
                    "citations": [],
                    "related_questions": [],
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                }

            # Generate answer using LLM
            answer, confidence = self._generate_answer(question, documents, metadatas)

            # Prepare citations
            citations = []
            if include_citations:
                citations = self._prepare_citations(documents, metadatas, distances)

            # Generate related questions
            related_questions = self._generate_related_questions(question, documents)

            processing_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Query processed in {processing_time:.2f}s with confidence {confidence:.2f}")

            return {
                "question": question,
                "answer": answer,
                "confidence": confidence,
                "citations": citations,
                "related_questions": related_questions,
                "processing_time": processing_time,
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    def _generate_answer(
        self,
        question: str,
        documents: List[str],
        metadatas: List[Dict],
    ) -> tuple[str, float]:
        """
        Generate answer using LLM.

        Returns:
            Tuple of (answer, confidence)
        """
        if not self.llm:
            # Fallback: extract most relevant excerpt
            answer = self._extract_relevant_excerpt(question, documents)
            confidence = 0.5
            return answer, confidence

        # Prepare context from documents
        context = "\n\n".join([
            f"[Source {i+1}]: {doc}"
            for i, doc in enumerate(documents)
        ])

        # Create prompt
        system_prompt = """You are a legal AI assistant helping to answer questions about legal documents.
Provide accurate, helpful answers based solely on the provided context.
If the context doesn't contain enough information to answer confidently, say so.
Always cite which source(s) you used in your answer.
This is for informational purposes only and does not constitute legal advice."""

        user_prompt = f"""Based on the following excerpts from legal documents, please answer this question:

Question: {question}

Context:
{context}

Please provide a clear, accurate answer based on the context above. Cite the source numbers you used."""

        try:
            # Generate answer
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = self.llm(messages)
            answer = response.content

            # Estimate confidence based on answer characteristics
            confidence = self._estimate_confidence(answer, question, documents)

            return answer, confidence

        except Exception as e:
            logger.error(f"Error generating answer with LLM: {e}")
            # Fallback
            answer = self._extract_relevant_excerpt(question, documents)
            return answer, 0.5

    def _extract_relevant_excerpt(self, question: str, documents: List[str]) -> str:
        """Extract most relevant excerpt when LLM is not available."""
        if not documents:
            return "No relevant information found."

        # Return first document as most relevant
        excerpt = documents[0]
        if len(excerpt) > 500:
            excerpt = excerpt[:500] + "..."

        return f"Based on the documents: {excerpt}"

    def _estimate_confidence(self, answer: str, question: str, documents: List[str]) -> float:
        """Estimate confidence in the answer."""
        confidence = 0.7  # Base confidence

        # Reduce confidence for hedging language
        hedging_words = ["may", "might", "possibly", "unclear", "not enough information", "cannot determine"]
        hedging_count = sum(1 for word in hedging_words if word in answer.lower())
        confidence -= hedging_count * 0.1

        # Increase confidence for citations
        if "source" in answer.lower():
            confidence += 0.1

        # Increase confidence for longer, detailed answers
        if len(answer) > 200:
            confidence += 0.05

        # Ensure confidence is in valid range
        confidence = max(0.1, min(1.0, confidence))

        return confidence

    def _prepare_citations(
        self,
        documents: List[str],
        metadatas: List[Dict],
        distances: List[float],
    ) -> List[SourceCitation]:
        """Prepare source citations."""
        citations = []

        for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
            # Calculate relevance score from distance (lower distance = higher relevance)
            # ChromaDB typically uses cosine distance, so we convert to similarity
            relevance_score = max(0.0, 1.0 - dist) if dist is not None else 0.5

            excerpt = doc[:300] + "..." if len(doc) > 300 else doc

            citation = SourceCitation(
                document_id=meta.get("document_id", "unknown"),
                document_name=meta.get("document_name", "Unknown Document"),
                excerpt=excerpt,
                page_number=meta.get("page_number"),
                relevance_score=relevance_score,
            )
            citations.append(citation)

        return citations

    def _generate_related_questions(self, question: str, documents: List[str]) -> List[str]:
        """Generate related questions based on the query and documents."""
        # Simple heuristic-based related questions
        related = []

        # Extract key terms from question
        question_lower = question.lower()

        if "compliance" in question_lower or "gdpr" in question_lower:
            related.extend([
                "What are the data subject rights under GDPR?",
                "How should personal data be protected?",
                "What are the requirements for data breach notification?",
            ])
        elif "contract" in question_lower:
            related.extend([
                "What are the termination clauses in this contract?",
                "What are the payment terms?",
                "What liabilities are covered?",
            ])
        elif "liability" in question_lower:
            related.extend([
                "What is the limitation of liability?",
                "What indemnification provisions are included?",
                "Are there any warranty disclaimers?",
            ])
        elif "privacy" in question_lower:
            related.extend([
                "What data is collected?",
                "How is data shared with third parties?",
                "What are users' privacy rights?",
            ])

        # Generic related questions
        if not related:
            related = [
                "What are the key provisions in this document?",
                "What are the main obligations?",
                "What are the termination conditions?",
            ]

        return related[:3]

    def delete_document(self, document_id: str):
        """
        Delete a document from the knowledge base.

        Args:
            document_id: ID of document to delete
        """
        logger.info(f"Deleting document {document_id}")

        try:
            # Get all chunk IDs for this document
            results = self.collection.get(
                where={"document_id": document_id}
            )

            if results and results.get("ids"):
                chunk_ids = results["ids"]
                self.collection.delete(ids=chunk_ids)
                logger.info(f"Deleted {len(chunk_ids)} chunks for document {document_id}")
            else:
                logger.warning(f"No chunks found for document {document_id}")

        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise

    def get_document_count(self) -> int:
        """Get total number of unique documents in the knowledge base."""
        try:
            all_items = self.collection.get()
            if all_items and all_items.get("metadatas"):
                unique_docs = set(meta.get("document_id") for meta in all_items["metadatas"])
                return len(unique_docs)
            return 0
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0

    def clear_collection(self):
        """Clear all documents from the collection. Use with caution!"""
        logger.warning("Clearing all documents from collection")
        try:
            self.chroma_client.delete_collection(self.collection_name)
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "Legal documents for Q&A"}
            )
            logger.info("Collection cleared")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise
