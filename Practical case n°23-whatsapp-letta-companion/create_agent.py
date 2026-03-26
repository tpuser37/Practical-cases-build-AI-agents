from letta_client import Letta
from dotenv import load_dotenv
import os

load_dotenv()

LETTA_TOKEN = os.getenv("LETTA_TOKEN")
PROJECT_ID= os.getenv("PROJECT_ID")

if not LETTA_TOKEN:
    raise ValueError("Merci de définir LETTA_API_KEY dans votre fichier .env")

# Initialiser le client Letta
client = Letta(api_key=LETTA_TOKEN, project_id=PROJECT_ID)

# Créer un nouvel agent
try:
    agent = client.agents.create(
        model="openai/gpt-5",  # ou le modèle que tu veux utiliser
        memory_blocks=[
            {
                "label": "persona",
                "description": "A memory block that stores the agent's persona.",
                "value": "You are a friendly agent that only answers in rhymes.",
            },
            {
                "label": "human",
                "description": "A memory block that stores information about the human user.",
                "value": "Name: Bob. Occupation: Unknown.",
            },
        ],
    )
except Exception as e:
    raise RuntimeError(f"Erreur lors de la création de l'agent : {e}")

# Récupérer l'agent_id
AGENT_ID = agent.id
print(f"✅ Nouvel Agent créé avec ID : {AGENT_ID}")

