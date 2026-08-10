import os
from e2b_code_interpreter import Sandbox


def run_chart_code(code: str, max_retries: int = 3) -> dict:
    """
    Exécute le code dans un sandbox E2B isolé.
    Retourne les bytes du fichier chart.png généré, ou une erreur.
    """
    sandbox = Sandbox.create(api_key=os.environ.get("E2B_API_KEY"))

    try:
        for attempt in range(max_retries):
            execution = sandbox.run_code(code)

            if not execution.error:
                try:
                    # format="bytes" est essentiel : sans ça, files.read()
                    # essaie de décoder le PNG en texte et le corrompt
                    chart_bytes = sandbox.files.read("chart.png", format="bytes")
                    return {"success": True, "chart_bytes": chart_bytes, "attempts": attempt + 1}
                except Exception as e:
                    return {"success": False, "error": f"Code exécuté mais chart.png introuvable : {e}"}

            error_msg = execution.error.value if execution.error else "Erreur inconnue"
            code = ask_llm_to_fix_code(code, error_msg)

        return {"success": False, "error": "Échec après plusieurs tentatives de correction"}

    finally:
        sandbox.kill()


def ask_llm_to_fix_code(code: str, error_message: str) -> str:
    import google.generativeai as genai

    prompt = f"""Le code Python suivant a produit une erreur lors de son exécution.
Corrige le code. Réponds UNIQUEMENT avec le code corrigé, sans explication.

CODE :
{code}

ERREUR :
{error_message}

CODE CORRIGÉ :"""

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)
    fixed_code = response.text.strip().replace("```python", "").replace("```", "").strip()
    return fixed_code