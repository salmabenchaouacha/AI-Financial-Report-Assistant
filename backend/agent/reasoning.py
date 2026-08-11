import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def build_context_from_chunks(search_results: dict) -> str:
    """
    Transforme les résultats bruts de ChromaDB en texte de contexte
    lisible pour le LLM, avec la source (page, type) pour chaque chunk.
    """
    documents = search_results.get("documents", [[]])[0]
    metadatas = search_results.get("metadatas", [[]])[0]

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        source_tag = f"[Source: page {meta['page']}, type {meta['type']}]"
        context_parts.append(f"{source_tag}\n{doc}")

    return "\n\n---\n\n".join(context_parts)


def answer_question(question: str, search_results: dict) -> str:
    """
    Envoie la question + le contexte retrouvé au LLM, et retourne
    une réponse textuelle basée UNIQUEMENT sur ce contexte.
    """
    context = build_context_from_chunks(search_results)

    prompt = f"""Tu es un assistant spécialisé dans l'analyse de rapports financiers.
Réponds à la question UNIQUEMENT à partir du contexte fourni ci-dessous.
Si l'information n'est pas présente dans le contexte, dis-le clairement, n'invente jamais de chiffre.
Cite la page source de chaque chiffre que tu utilises.

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :"""

    model = genai.GenerativeModel("gemini-3.5-flash-lite")
    response = model.generate_content(prompt)
    return response.text