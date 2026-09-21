# from langchain_community.document_loaders import WebBaseLoader

# import os

# os.environ["USER_AGENT"] = "Mozilla/5.0"

# loader = WebBaseLoader(
#     "https://adventra.tech/tripDetails/0072d20e-85df-41a5-8f6d-ae55304eed60?TYPE=Trip"
# )

# docs = loader.load()

# print("Docs:", len(docs))
# print("Metadata:", docs[0].metadata)
# print("Content length:", len(docs[0].page_content))
# print(repr(docs[0].page_content[:1000]))


# from langchain_community.document_loaders import AsyncChromiumLoader
# from langchain_community.document_transformers import Html2TextTransformer

# url = ["https://adventra.tech/tripDetails/0072d20e-85df-41a5-8f6d-ae55304eed60?type=CURATED#overview"]

# # 1. Load the rendered HTML via headless browser
# loader = AsyncChromiumLoader(url)
# html_docs = loader.load()

# # 2. Transform raw HTML to clean text
# html2text = Html2TextTransformer()
# docs = html2text.transform_documents(html_docs)

# print(docs[0].page_content)


from langchain_community.document_loaders import SeleniumURLLoader

loader = SeleniumURLLoader(urls=["https://adventra.tech/tripDetails/0072d20e-85df-41a5-8f6d-ae55304eed60?type=CURATED#overview"])
docs = loader.load()

print(docs[0].page_content)
# import requests
# response = requests.get(
#         "https://adventra.tech/tripDetails/0072d20e-85df-41a5-8f6d-ae55304eed60?type=CURATED#overview",
#         headers={"User-Agent": "Mozilla/5.0"},
#         timeout=30,
#     )
# content_type = response.headers.get("Content-Type", "").lower()
# print(content_type)
