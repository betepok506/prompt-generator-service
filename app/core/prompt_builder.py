class PromptBuilder:
    DEFAULT_TEMPLATE = """
    Ты помощник службы поддержки. Используй следующие фрагменты документации, чтобы ответить на вопрос.

    Контекст:
    {context}

    Вопрос: {question}
    Ответ:
    """

    def build_prompt(self, context: list[str], question: str) -> str:
        context_str = "\n".join(context)
        return self.DEFAULT_TEMPLATE.format(context=context_str, question=question)
