import os
import uuid
from typing import List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import HTTPException, DocumentParsingError
from app.models.document import Document
from app.repositories.document import DocumentRepository
from app.repositories.conversation import ConversationRepository
from app.services.parser import FileParserService
from app.services.chunker import RecursiveChunkerService
from app.services.embedding import EmbeddingFactory
from app.services.vectorstore import QdrantService

class DocumentService:
    @staticmethod
    async def upload_and_process(
        db: AsyncSession,
        file: UploadFile,
        conversation_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> Document:
        """
        Orchestrator: Saves file, extracts text, chunks it, embeds it,
        upserts vectors to Qdrant, and saves metadata to PostgreSQL.
        """
        # 1. Validation
        if file.content_type not in settings.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: PDF, DOCX, TXT."
            )

        # Temp read to check file size
        file.file.seek(0, os.SEEK_END)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="File is too large. Max size is 15MB."
            )

        # Verify conversation ownership
        conv_repo = ConversationRepository(db)
        conv = await conv_repo.get(conversation_id)
        if not conv or conv.user_id != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found.")

        # Create localized directory for conversation storage
        conv_dir = os.path.join(settings.UPLOAD_DIR, str(conversation_id))
        os.makedirs(conv_dir, exist_ok=True)

        doc_id = uuid.uuid4()
        safe_filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(conv_dir, safe_filename)

        # 2. Write physical file locally
        try:
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to write file locally: {str(e)}")

        # 3. Parse File
        try:
            pages = FileParserService.parse(file_path, file.filename)
            if not pages:
                # Remove file if parsing failed completely (no text extracted)
                if os.path.exists(file_path):
                    os.remove(file_path)
                raise HTTPException(status_code=400, detail="The document contains no extractable text.")
        except DocumentParsingError as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e

        # 4. Chunk text
        chunks = RecursiveChunkerService.chunk_document(pages)

        # 5. Generate embeddings & upsert to Qdrant
        # We determine embedding provider based on conversation settings.
        # OpenAI model uses OpenAI embeddings. Groq/Gemini/Claude can use OpenAI or local sentence-transformers.
        # Let's map dynamically: if conversation is using OpenAI, use OpenAI.
        # Otherwise, if settings.OPENAI_API_KEY is available, we can use OpenAI, or fall back to local sentence-transformer.
        # Let's default to 'openai' if API key is present, otherwise 'local' for a clean local-first setup!
        embedding_provider = "openai" if (settings.OPENAI_API_KEY and conv.provider == "openai") else "sentencetransformer"
        if not settings.OPENAI_API_KEY and embedding_provider == "openai":
            embedding_provider = "sentencetransformer"

        try:
            # Instantiate embedding model
            embedder = EmbeddingFactory.get_embedding_provider(embedding_provider)
            chunk_texts = [c["text"] for c in chunks]
            
            # Generate vectors
            embeddings = await embedder.embed_documents(chunk_texts)
            
            # Upsert into Qdrant
            qdrant = QdrantService()
            await qdrant.upsert_chunks(
                conversation_id=conversation_id,
                document_id=doc_id,
                user_id=user_id,
                filename=file.filename,
                chunks=chunks,
                embeddings=embeddings,
                embedding_provider=embedding_provider
            )
        except Exception as e:
            # Clean up uploaded file if Qdrant pipeline fails
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate embeddings or index vectors: {str(e)}"
            )

        # 6. Save metadata to PostgreSQL
        doc_repo = DocumentRepository(db)
        doc_data = {
            "id": doc_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "filename": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "mime_type": file.content_type
        }
        
        db_doc = await doc_repo.create_document(doc_data, chunks)
        return db_doc

    @staticmethod
    async def delete_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID
    ):
        """Delete physical file, vectors from Qdrant, and PostgreSQL records."""
        doc_repo = DocumentRepository(db)
        doc = await doc_repo.get(document_id)
        if not doc or doc.user_id != user_id:
            raise HTTPException(status_code=404, detail="Document not found.")

        # Determine conversation settings to clean up the correct Qdrant collection
        conv_repo = ConversationRepository(db)
        conv = await conv_repo.get(doc.conversation_id)
        embedding_provider = "openai" if (settings.OPENAI_API_KEY and conv and conv.provider == "openai") else "sentencetransformer"
        if not settings.OPENAI_API_KEY and embedding_provider == "openai":
            embedding_provider = "sentencetransformer"

        # 1. Delete vectors from Qdrant
        try:
            qdrant = QdrantService()
            await qdrant.delete_document_vectors(
                conversation_id=doc.conversation_id,
                document_id=document_id,
                embedding_provider=embedding_provider
            )
        except Exception as e:
            # Log Qdrant failure but proceed to remove local file & db record
            pass

        # 2. Delete local physical file
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception:
                pass

        # 3. Delete DB record (cascade will clean up document_chunks)
        await doc_repo.delete(document_id)
