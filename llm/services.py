from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class PromptTemplateManager:
    """Manages prompt templates for different use cases."""
    
    @staticmethod
    def create_qa_prompt():
        """Create a prompt template for generating answers based on retrieved documents."""
        system_prompt = (
            "You are an assistant for question answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Keep the answer concise.\n\n{context}"
        )
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
    
    @staticmethod
    def create_contextualize_q_prompt():
        """Create a prompt template for contextualizing questions based on chat history."""
        system_prompt = (
            "Given a chat history and the latest user question, "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do not answer the question, "
            "just reformulate it if needed otherwise return as it is."
        )
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
    
    @staticmethod
    def create_summary_prompt():
        """Create a prompt template for summarizing document content."""
        system_prompt = (
            "You are a helpful assistant that summarizes documents. "
            "Please provide a concise summary of the following content:"
            "\n\n{context}"
        )
        return ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "Please summarize this content."),
        ])
    
    @staticmethod
    def get_prompt_from_template(template_text):
        """Create a ChatPromptTemplate from custom template text."""
        return ChatPromptTemplate.from_template(template_text)