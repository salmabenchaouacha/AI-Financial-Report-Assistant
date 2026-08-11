import os
from dotenv import load_dotenv
import google.generativeai as genai

# Charger le fichier .env
load_dotenv()

# Récupérer la clé
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY introuvable dans .env")

genai.configure(api_key=api_key)

for model in genai.list_models():
    if "generateContent" in model.supported_generation_methods:
        print(model.name)