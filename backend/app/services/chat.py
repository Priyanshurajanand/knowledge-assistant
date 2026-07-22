import json
import uuid
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.exceptions import HTTPException
from app.repositories.conversation import ConversationRepository
from app.services.retrieval import HybridRetrievalService
from app.services.prompts import PromptService
from app.services.llm import LLMFactory
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)

class ChatService:
    @staticmethod
    async def chat_rag(
        conversation_id: uuid.UUID,
        user_id: uuid.UUID,
        question: str
    ) -> AsyncGenerator[str, None]:
        """
        Coordinates the entire RAG pipeline: retrieves hybrid search context,
        compiles prompts, streams LLM completions via SSE, and writes conversation history.
        Yields JSON strings: first containing 'citations', then individual 'token's.
        """
        async with async_session_maker() as session:
            conv_repo = ConversationRepository(session)
            
            # 1. Ownership and existence check
            conv = await conv_repo.get(conversation_id)
            if not conv or conv.user_id != user_id:
                raise HTTPException(status_code=404, detail="Conversation not found.")

            # Save user message to PostgreSQL immediately
            await conv_repo.create_message(
                conversation_id=conversation_id,
                role="user",
                content=question
            )
            await session.commit()

            # 2. Retrieve history (limit to last 10 messages for context window efficiency)
            all_messages = await conv_repo.get_messages(conversation_id)
            # Exclude the user message we just created to prevent duplicates in current request
            history_msgs = all_messages[:-1] if len(all_messages) > 1 else []
            # Take the last 10
            history_msgs = history_msgs[-10:]
            
            history_payload = [
                {"role": msg.role, "content": msg.content}
                for msg in history_msgs
            ]

            # 3. Retrieve Context via Hybrid RRF Search
            # Determine embedding provider based on configuration
            embedding_provider = "openai" if (settings.OPENAI_API_KEY and conv.provider == "openai") else "sentencetransformer"
            if not settings.OPENAI_API_KEY and embedding_provider == "openai":
                embedding_provider = "sentencetransformer"

            top_chunks = await HybridRetrievalService.retrieve_context(
                db=session,
                conversation_id=conversation_id,
                query_text=question,
                embedding_provider=embedding_provider,
                limit=settings.TOP_K,
                rrf_k=settings.RRF_K
            )

            # 4. Extract Relevant Source Excerpts by File & Page Number
            citations = []
            seen_citations = set()
            for chunk in top_chunks:
                key = (chunk["filename"], chunk["page_number"])
                if key not in seen_citations:
                    seen_citations.add(key)
                    snippet = chunk["text"].strip()
                    # Cap snippet length to the relevant excerpt (~350 chars) if chunk is very long
                    if len(snippet) > 350:
                        snippet = snippet[:350].rsplit(' ', 1)[0] + "..."
                    citations.append({
                        "filename": chunk["filename"],
                        "page_number": chunk["page_number"],
                        "text": snippet
                    })

            # 5. Compile Prompt templates
            prompts = PromptService()
            system_prompt = prompts.compile_system_prompt()
            context_str = prompts.compile_context(top_chunks)
            user_prompt = prompts.compile_user_prompt(context_str, question)

            # 6. Yield citations list first so UI displays them immediately
            yield f"event: citations\ndata: {json.dumps(citations)}\n\n"

            # 7. Query LLM and yield token-by-token
            assistant_reply = ""
            try:
                llm = LLMFactory.get_provider(conv.provider)
                async for token in llm.generate_stream(
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    history=history_payload,
                    model=conv.model
                ):
                    assistant_reply += token
                    yield f"event: token\ndata: {json.dumps(token)}\n\n"
            except Exception as e:
                logger.exception("LLM generation stream failed.")
                error_msg = f"\n\n[Error generating response: {str(e)}]"
                assistant_reply += error_msg
                yield f"event: token\ndata: {json.dumps(error_msg)}\n\n"

            # 8. Save complete assistant response to database
            if assistant_reply.strip():
                await conv_repo.create_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_reply,
                    citations=citations
                )
                await session.commit()
                
            yield "event: end\ndata: [DONE]\n\n"
