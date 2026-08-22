import os
import google.generativeai as genai
import math

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def build_context_from_chunks(search_results: dict) -> str:
    documents = search_results.get("documents", [[]])[0]
    metadatas = search_results.get("metadatas", [[]])[0]

    context_parts = []
    for doc, meta in zip(documents, metadatas):
        filename = meta.get("filename") or meta.get("document_id", "")[:8]
        source_tag = f"[Source: {filename}, page {meta['page']}, type {meta['type']}]"
        context_parts.append(f"{source_tag}\n{doc}")

    return "\n\n---\n\n".join(context_parts)

def answer_question(question: str, search_results: dict) -> str:
    """
    Envoie la question + le contexte retrouvé au LLM, avec des instructions
    qui l'encouragent à analyser, comparer et calculer à partir des données
    présentes, plutôt que de se limiter à une lecture littérale.
    """
    context = build_context_from_chunks(search_results)

    prompt = f"""Tu es un analyste financier senior spécialisé dans l'étude de rapports bancaires.

MISSION
Ne te contente jamais de recopier un chiffre isolé si la question implique une comparaison,
un calcul, un classement ou une synthèse. Ton rôle est d'ANALYSER les données du contexte,
pas seulement de les retrouver telles quelles.

CE QUE TU DOIS FAIRE
- Si la réponse nécessite de comparer plusieurs chiffres présents dans le contexte (même
  répartis sur plusieurs extraits différents), fais cette comparaison toi-même.
- Si la réponse nécessite un calcul (somme, différence, pourcentage, ratio, part du total),
  effectue-le toi-même à partir des chiffres du contexte, et montre le calcul.
- Si plusieurs extraits parlent du même sujet sous des angles différents (texte, tableau,
  graphique), croise-les pour construire une réponse plus complète qu'un seul extrait seul.
- Structure ta réponse en deux temps quand la question l'exige :
  1. **Analyse** — les faits et chiffres pertinents que tu as identifiés et croisés
  2. **Conclusion** — la réponse synthétique à la question posée

CE QUE TU NE DOIS JAMAIS FAIRE
- Inventer un chiffre qui n'apparaît nulle part, sous aucune forme, dans le contexte
- Dire "l'information n'est pas présente" alors qu'elle peut être déduite ou calculée
  à partir de chiffres qui, eux, sont bien présents dans le contexte
- Confondre une extrapolation (donnée absente du contexte) avec un calcul (opération sur
  des données présentes) — la première est interdite, le second est encouragé

EXEMPLE DE BON RAISONNEMENT
Question : "Quelle filiale a le plus contribué à la hausse du Groupe ?"
Contexte disponible : un tableau avec les variations par filiale, un texte commentant la
hausse globale.
Mauvaise réponse (à éviter) : "L'information n'est pas explicitement donnée dans le contexte."
Bonne réponse : identifier dans le tableau la filiale avec la plus forte variation positive
en valeur absolue et en %, croiser avec le commentaire du texte s'il la mentionne, puis
conclure clairement en citant les deux chiffres comparés.

Cite le nom du document ET la page source de chaque donnée BRUTE que tu utilises.
Précise clairement quand un chiffre est CALCULÉ par toi (et à partir de quelles données),
par opposition à un chiffre directement extrait du document.

Si, après une vraie tentative de calcul et de croisement, l'information reste réellement
absente ou impossible à déduire du contexte, dis-le clairement — mais seulement dans ce cas,
jamais par défaut.

Structure ta réponse en markdown clair (puces, tableaux, gras sur les chiffres clés).

CONTEXTE :
{context}

QUESTION : {question}

RÉPONSE :"""

    model = genai.GenerativeModel("gemini-flash-lite-latest")
    response = model.generate_content(prompt)
    return response.text

def build_sources_from_results(search_results: dict) -> list[dict]:
    """
    Transforme les résultats bruts de ChromaDB en sources exploitables
    par le front pour le mode audit : document, page, type, score de
    similarité cosinus (%) et extrait.

    Avec la distance cosinus, similarité = (1 - distance) * 100.
    Le cosinus étant borné à 1 au maximum, la distance cosinus (1 - cos)
    est bornée à 0 au minimum, donc la similarité ne peut jamais dépasser 100%.
    """
    documents = search_results.get("documents", [[]])[0]
    metadatas = search_results.get("metadatas", [[]])[0]
    distances = search_results.get("distances", [[]])[0]

    sources = []
    for doc, meta, dist in zip(documents, metadatas, distances):
        similarity = round((1 - dist) * 100, 1)
        similarity = max(0.0, min(100.0, similarity))

        sources.append({
            "filename": meta.get("filename") or f"document {meta.get('document_id', '')[:8]}",
            "document_id": meta.get("document_id"),
            "page": meta.get("page"),
            "type": meta.get("type"),
            "similarity": similarity,
            "excerpt": doc[:500] + ("…" if len(doc) > 500 else ""),
        })
    return sources