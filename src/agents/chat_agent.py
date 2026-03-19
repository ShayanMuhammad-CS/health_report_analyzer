import os
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TQDM_DISABLE"] = "1"

import streamlit as st
from groq import Groq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class ChatAgent:
    """
    RAG-powered chat agent for follow-up Q&A about a blood report.
    Uses FAISS vector store + HuggingFace embeddings + Groq LLM.
    """

    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        self.model_name = "llama-3.3-70b-versatile"

    def initialize_vector_store(self, text_content: str):
        """Create a FAISS vector store from blood report text."""
        if not text_content or not text_content.strip():
            text_content = "No report context available."

        texts = self.text_splitter.split_text(text_content)
        if not texts:
            texts = [text_content]

        vectorstore = FAISS.from_texts(texts, self.embeddings)
        return vectorstore

    def _format_chat_history(self, chat_history: list) -> list:
        """Format chat history list for Groq API messages format."""
        return [{"role": msg["role"], "content": msg["content"]} for msg in chat_history]

    def _contextualize_query(self, query: str, chat_history: list) -> str:
        """
        Reformulate a follow-up question as a standalone question using recent chat history,
        so the retriever can find the right context without needing the full conversation.
        """
        if not chat_history:
            return query

        recent_history = chat_history[-4:]  # Last 2 exchanges
        history_text = "\n".join(
            [
                f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
                for msg in recent_history
            ]
        )

        contextualize_prompt = (
            f"Given a chat history and the latest user question, "
            f"formulate a standalone question which can be understood without the chat history. "
            f"Do NOT answer the question, just reformulate it if needed and otherwise return it as is.\n\n"
            f"Chat History:\n{history_text}\n\n"
            f"Latest User Question: {query}\n\n"
            f"Standalone Question:"
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You reformulate questions to be standalone.",
                    },
                    {"role": "user", "content": contextualize_prompt},
                ],
                temperature=0.0,
                max_tokens=200,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return query  # Fallback to original query

    def get_response(self, query: str, vectorstore, chat_history: list = None) -> str:
        """
        Get a RAG-powered response to a follow-up question.
        1. Contextualize the query
        2. Retrieve relevant chunks from the vector store
        3. Generate a response using Groq with the retrieved context
        """
        if chat_history is None:
            chat_history = []

        # Step 1: Contextualize query based on chat history
        contextualized_query = self._contextualize_query(query, chat_history)

        # Step 2: Retrieve relevant document chunks
        try:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            docs = retriever.get_relevant_documents(contextualized_query)
            context = "\n\n".join([doc.page_content for doc in docs])
            if context.strip() == "No report context available.":
                context = ""
        except Exception:
            context = ""

        # Step 3: Build messages for Groq API
        qa_system_prompt = (
            "You are a knowledgeable medical assistant helping users understand their blood report. "
            "Use the following retrieved context from the report to answer the question. "
            "If you can't find the relevant information in the context, say so honestly. "
            "Keep answers concise, clear, and medically informative.\n\n"
        )
        if context:
            qa_system_prompt += f"Report Context:\n{context}"

        messages = [{"role": "system", "content": qa_system_prompt}]

        # Include recent chat history for conversational flow
        if chat_history:
            messages.extend(self._format_chat_history(chat_history[-6:]))

        messages.append({"role": "user", "content": query})

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.5,
                max_tokens=800,
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"I encountered an error while generating a response: {str(e)}"
