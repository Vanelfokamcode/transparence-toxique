import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

# On charge les variables du fichier .env
load_dotenv()

TOKEN = os.getenv("HF_TOKEN")
USER = os.getenv("HF_USER")
REPO_NAME = f"{USER}/transparence-toxique"

if not TOKEN or not USER:
    print("❌ Erreur : HF_TOKEN ou HF_USER manquant dans le fichier .env")
    exit()

api = HfApi()

print(f"🚀 Téléchargement sécurisé vers Hugging Face : {REPO_NAME}...")

try:
    api.upload_folder(
        folder_path="exports/parquet",
        repo_id=REPO_NAME,
        repo_type="dataset",
        token=TOKEN
    )
    print("\n✅ Succès ! Les données sont en ligne sans avoir exposé ton token.")
    print(f"🔗 URL : https://huggingface.co/datasets/{REPO_NAME}")
except Exception as e:
    print(f"❌ Erreur lors de l'upload : {e}")
