from langchain_huggingface import HuggingFacePipeline
from transformers import pipeline
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def huggingface_pipeline(prompt: str):

    hug_pipe = pipeline(
        "text-generation",
        model="mistralai/Mixtral-8x7B-Instruct-v0.1",
        pad_token_id=50256,
        max_new_tokens=100,
        temperature=0.7,
        do_sample=True,
        token=settings.HUGGINGFACE_API_TOKEN
    )
    llm = HuggingFacePipeline(pipeline=hug_pipe)

    repo = llm.invoke(prompt)
    logger.info(f"Huggingface pipeline generated response: {repo}")
    return repo

