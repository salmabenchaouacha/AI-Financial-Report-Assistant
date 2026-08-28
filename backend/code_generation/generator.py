import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

CHART_TYPE_GUIDANCE = {
    "evolution": (
        "Type de graphique imposé : COURBE (plt.plot), un point par période (ex: 2023, 2024). "
        "Si plusieurs entités sont comparées, trace une courbe par entité avec une légende claire. "
        "Ajoute des marqueurs (marker='o') sur chaque point et une grille horizontale légère (alpha=0.3)."
    ),
    "comparaison": (
        "Type de graphique imposé : BARRES GROUPÉES (plt.bar avec décalage), une couleur par série "
        "si plusieurs indicateurs sont comparés côte à côte pour chaque entité. Ajoute une légende claire."
    ),
    "classement": (
        "Type de graphique imposé : BARRES HORIZONTALES (plt.barh), triées par ordre décroissant de "
        "valeur (la plus grande en haut, utilise plt.gca().invert_yaxis()). Affiche la valeur exacte "
        "au bout de chaque barre."
    ),
    "repartition": (
        "Type de graphique imposé : CAMEMBERT (plt.pie), avec les pourcentages affichés "
        "(autopct='%1.1f%%') et une couleur distincte par part."
    ),
    "difference": (
        "Type de graphique imposé : BARRES DIVERGENTES montrant l'écart entre deux valeurs "
        "(variation en valeur ou en %). Couleur verte pour les écarts positifs, rouge pour les "
        "écarts négatifs (liste de couleurs conditionnelle selon le signe)."
    ),
    "valeur_unique": (
        "Type de graphique imposé : UNE SEULE BARRE large, avec la valeur affichée en grand "
        "au-dessus de la barre (plt.text). Pas besoin d'axe X avec plusieurs catégories."
    ),
}

# Mots-clés déclencheurs par catégorie — rapide et gratuit, évite un appel LLM pour les cas évidents
_KEYWORDS = {
    "evolution": ["évolution", "évolué", "tendance", "progression", "au fil du temps",
                  "entre 2023 et 2024", "au cours des années", "historique"],
    "classement": ["classement", "qui a le plus", "qui a le moins", "top ", "meilleure",
                   "pire", "plus forte", "plus faible", "la plus", "la moins", "trier"],
    "repartition": ["répartition", "part de", "pourcentage", "proportion", "camembert", "secteur"],
    "difference": ["différence entre", "écart entre", "variation de", "delta"],
    "comparaison": ["compare", "comparaison", "par rapport à", "versus", " vs ", "face à"],
}


def classify_chart_intent(question: str) -> str:
    """
    Détermine le type de graphique le plus adapté à la question.
    D'abord par mots-clés (gratuit, instantané), puis en repli sur le LLM
    seulement si aucune règle ne matche clairement.
    """
    q = question.lower()

    for intent, keywords in _KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return intent

    try:
        model = genai.GenerativeModel("gemini-flash-lite-latest")
        prompt = f"""Classe cette question dans UNE SEULE catégorie parmi :
evolution, comparaison, classement, repartition, difference, valeur_unique

Réponds UNIQUEMENT avec le mot de la catégorie, rien d'autre.

QUESTION : {question}
CATÉGORIE :"""
        response = model.generate_content(prompt)
        label = response.text.strip().lower()
        if label in CHART_TYPE_GUIDANCE:
            return label
    except Exception:
        pass

    return "comparaison"  # valeur par défaut sûre

import re

def extract_numbers_from_text(text: str) -> set:
    """Extrait les nombres significatifs d'un texte, normalisés pour comparaison."""
    matches = re.findall(r'\d+(?:[.,]\d+)?', text)
    cleaned = set()
    for m in matches:
        normalized = m.replace(",", ".")
        digits_only = normalized.replace(".", "")
        if len(digits_only) >= 2:
            cleaned.add(normalized.rstrip("0").rstrip(".") if "." in normalized else normalized)
    return cleaned


def validate_chart_code_against_context(code: str, context: str) -> bool:
    """
    Vérifie qu'une part significative des nombres codés en dur dans le
    graphique généré apparaît bien dans le contexte source, pour bloquer
    les hallucinations de valeurs plausibles mais inventées.
    """
    code_numbers = extract_numbers_from_text(code)
    context_numbers = extract_numbers_from_text(context)

    # Ignore les petits nombres génériques (tailles de figure, index, DPI...)
    code_numbers = {n for n in code_numbers if len(n.replace(".", "")) >= 2}

    if not code_numbers:
        return True

    matches = sum(1 for n in code_numbers if any(n in cn or cn in n for cn in context_numbers))
    ratio = matches / len(code_numbers)
    return ratio >= 0.3

def generate_chart_code(question: str, context: str, chart_intent: str = None, max_retries: int = 2) -> str:
    if chart_intent is None:
        chart_intent = classify_chart_intent(question)

    guidance = CHART_TYPE_GUIDANCE.get(chart_intent, CHART_TYPE_GUIDANCE["comparaison"])

    base_prompt = f"""Tu es un générateur de code Python spécialisé en visualisation de données financières.

À partir du CONTEXTE ci-dessous (extrait d'un rapport financier), écris un script Python
qui génère un graphique répondant à la QUESTION.

{guidance}

RÈGLES STRICTES :
- Utilise UNIQUEMENT matplotlib (pas plotly)
- Utilise UNIQUEMENT les chiffres présents MOT POUR MOT dans le contexte, n'invente JAMAIS de valeur
- Si un chiffre nécessaire n'apparaît pas explicitement dans le contexte, affiche à la place un
  message clair "Donnée absente du contexte" plutôt que d'estimer ou d'inventer une valeur
- Le script doit sauvegarder le graphique avec : plt.savefig('chart.png')
- Ajoute un titre clair et des labels d'axes lisibles
- Réponds UNIQUEMENT avec le code Python, sans explication, sans balises markdown

CONTEXTE :
{context}

QUESTION : {question}

CODE PYTHON :"""

    model = genai.GenerativeModel("gemini-flash-lite-latest")
    prompt = base_prompt
    code = ""

    for attempt in range(max_retries + 1):
        response = model.generate_content(prompt)
        code = response.text.strip().replace("```python", "").replace("```", "").strip()

        if validate_chart_code_against_context(code, context):
            return code

        prompt = base_prompt + "\n\nATTENTION : ta réponse précédente contenait des chiffres absents du CONTEXTE fourni. Relis attentivement le CONTEXTE et n'utilise QUE des valeurs qui y apparaissent littéralement."

    return code