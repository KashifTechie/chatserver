from langchain_openai import ChatOpenAI

from django.conf import settings
def chatgetllm(prompt):

    llm = ChatOpenAI(
        api_key=settings.OPENAI_API_KEY,
        model="gpt-4o-mini",
        temperature=0
        )

    result = llm.invoke(prompt)

    return result