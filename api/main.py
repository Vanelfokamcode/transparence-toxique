from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_USER = os.getenv("HF_USER", "pentagonaiee")
BASE_URL = f"https://huggingface.co/datasets/{HF_USER}/transparence-toxique/resolve/main"

# --- CACHE EN MÉMOIRE ---
# On crée une connexion DuckDB persistante en RAM pour toute la durée de vie de l'API
db = duckdb.connect(':memory:')
db.execute("INSTALL httpfs; LOAD httpfs;")

@app.on_event("startup")
def startup_event():
    print("🚀 Chargement des preuves en mémoire vive...")
    # On charge les petites tables vitales en RAM une bonne fois pour toutes
    db.execute(f"CREATE TABLE IF NOT EXISTS groups AS SELECT * FROM read_parquet('{BASE_URL}/fact_influence_groups.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS regions AS SELECT * FROM read_parquet('{BASE_URL}/ref_regions.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS influence AS SELECT * FROM read_parquet('{BASE_URL}/fact_influence.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS meds AS SELECT * FROM read_parquet('{BASE_URL}/labo_top_meds.parquet')")
    # Pour la recherche, on charge aussi (ça ne fait que 1.2 Mo, c'est rien pour 512 Mo de RAM)
    db.execute(f"CREATE TABLE IF NOT EXISTS search_data AS SELECT * FROM read_parquet('{BASE_URL}/search_medecins.parquet')")
    print("✅ RAM prête. Latence éliminée.")

@app.get("/")
async def root():
    return FileResponse('index.html')

@app.get("/api/v1/landing-stats")
def get_landing_stats():
    # Ici, on requête la table en RAM (instantané)
    top_groups = db.execute("SELECT groupe, total_cadeaux_groupe FROM groups ORDER BY total_cadeaux_groupe DESC LIMIT 5").df()
    top_villes = db.execute("SELECT ville, SUM(montant_cumule) as total FROM search_data GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df()
    global_total = db.execute("SELECT SUM(total_cadeaux_groupe) FROM groups").fetchone()[0]
    
    return {
        "top_groups": top_groups.to_dict(orient="records"),
        "top_villes": top_villes.to_dict(orient="records"),
        "total_global": global_total
    }

@app.get("/api/v1/search")
def search(q: str):
    # Requête ultra-rapide sur la RAM
    query = f"""
        WITH raw_results AS (
            SELECT 
                s.nom, s.prenom, s.ville, s.specialite, s.labo_source, s.montant_cumule,
                COALESCE(i.roi_influence, 0) as roi,
                COALESCE(i.pct_princeps, 0) as part_de_marche,
                COALESCE(m.top_produits, 'traitements spécialisés') as medocs,
                CASE 
                    WHEN s.nom ILIKE '{q}' THEN 1
                    WHEN s.nom ILIKE '{q}%' THEN 2
                    WHEN s.ville ILIKE '{q}' THEN 3
                    ELSE 4
                END as priority
            FROM search_data s
            JOIN regions r ON s.region_code = r.code
            LEFT JOIN influence i 
              ON s.labo_normalise = i.labo AND i.region = r.libelle_reg
            LEFT JOIN meds m
              ON s.labo_normalise = m.labo_ansm
            WHERE s.nom ILIKE '%{q}%' OR (s.ville ILIKE '{q}%' AND LENGTH('{q}') > 3)
        )
        SELECT * FROM raw_results ORDER BY priority ASC, montant_cumule DESC LIMIT 15
    """
    res = db.execute(query).df().fillna(0)
    return res.to_dict(orient="records")
