import os
from typing import Dict, Any, List

DEFAULT_SYSTEM_PROMPT = (
    "You are a professional Enterprise AI Knowledge Assistant. "
    "Your goal is to answer the user's questions clearly, concisely, and accurately based ONLY on the provided document context.\n\n"
    "CRITICAL RULES:\n"
    "1. Only use facts directly mentioned in the context. Do not extrapolate, assume, or bring in outside knowledge.\n"
    "2. If the context does not contain enough information to answer the question, state clearly: "
    "'I cannot find the answer to this question in the uploaded documents.' and do not output any other content.\n"
    "3. Format your answer cleanly in standard markdown. Do NOT include inline source tags, file paths, or page markers inside your response text (for example, do NOT write '(Source File: ...)' or '(Page X)' inline). Write a clean, natural response."
)

DEFAULT_CONTEXT_TEMPLATE = (
    "Source File: {filename} | Page: {page_number}\n"
    "Content:\n"
    "{text}\n"
    "=========================================\n"
)

DEFAULT_USER_TEMPLATE = (
    "Here is the context retrieved from the conversation's knowledge base:\n\n"
    "{context}\n"
    "User Question: {question}\n\n"
    "Write a clear, direct, and well-structured response based on the context above."
)

class PromptService:
    def __init__(self, templates_dir: str = "storage/prompts"):
        self.templates_dir = templates_dir
        os.makedirs(self.templates_dir, exist_ok=True)
        self._init_templates()

    def _init_templates(self):
        """Initializes/updates prompt template files on disk."""
        self._write_file("system.txt", DEFAULT_SYSTEM_PROMPT)
        self._write_file("context.txt", DEFAULT_CONTEXT_TEMPLATE)
        self._write_file("user.txt", DEFAULT_USER_TEMPLATE)

    def _write_file(self, filename: str, content: str):
        path = os.path.join(self.templates_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def _load_template(self, filename: str, default: str) -> str:
        path = os.path.join(self.templates_dir, filename)
        try:
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception:
            pass
        return default

    def compile_system_prompt(self) -> str:
        """Returns the compiled system prompt."""
        return self._load_template("system.txt", DEFAULT_SYSTEM_PROMPT)

    def compile_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Compiles multiple context chunks using the context template."""
        template = self._load_template("context.txt", DEFAULT_CONTEXT_TEMPLATE)
        context_str = ""
        for chunk in chunks:
            context_str += template.format(
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                text=chunk["text"]
            )
        return context_str

    def compile_user_prompt(self, context_str: str, question: str) -> str:
        """Compiles the final user prompt injecting context and question."""
        template = self._load_template("user.txt", DEFAULT_USER_TEMPLATE)
        return template.format(context=context_str, question=question)
