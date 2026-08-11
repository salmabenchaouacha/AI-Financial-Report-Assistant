import os
import google.generativeai as genai
from typer import prompt

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


def generate_chart_code(question: str, context: str) -> str:
    """
    Demande au LLM de générer du code Python (matplotlib) pour créer
    un graphique à partir des données présentes dans le contexte.
    Le code doit sauvegarder le résultat dans 'chart.png'.
    """
    prompt = f"""Tu es un générateur de code Python spécialisé en visualisation de données financières.

À partir du CONTEXTE ci-dessous (extrait d'un rapport financier), écris un script Python
qui génère un graphique répondant à la QUESTION.

RÈGLES STRICTES :
- Utilise UNIQUEMENT matplotlib (pas plotly)
- Utilise UNIQUEMENT les chiffres présents dans le contexte, n'invente aucune donnée
- Le script doit sauvegarder le graphique avec : plt.savefig('chart.png')
- Réponds UNIQUEMENT avec le code Python, sans explication, sans balises markdown

CONTEXTE :
{context}

QUESTION : {question}

CODE PYTHON :"""

    model = genai.GenerativeModel("gemini-3.5-flash-lite")
    response = model.generate_content(prompt)

    code = response.text.strip()
    # Nettoyage au cas où le LLM ajoute quand même des balises ```python ... ```
    code = code.replace("```python", "").replace("```", "").strip()

    return code