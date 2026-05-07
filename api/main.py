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

# Connexion DuckDB persistante en RAM
db = duckdb.connect(':memory:')
db.execute("INSTALL httpfs; LOAD httpfs;")

LANDING_CACHE = {}

@app.on_event("startup")
def startup_event():
    global LANDING_CACHE
    print("🚀 Chargement du Radar GPS en mémoire vive...")
    
    # On charge tout en RAM (les 23 Mo de search_medecins.parquet)
    db.execute(f"CREATE TABLE IF NOT EXISTS groups AS SELECT * FROM read_parquet('{BASE_URL}/fact_influence_groups.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS regions AS SELECT * FROM read_parquet('{BASE_URL}/ref_regions.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS influence AS SELECT * FROM read_parquet('{BASE_URL}/fact_influence.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS meds AS SELECT * FROM read_parquet('{BASE_URL}/labo_top_meds.parquet')")
    db.execute(f"CREATE TABLE IF NOT EXISTS search_data AS SELECT * FROM read_parquet('{BASE_URL}/search_medecins.parquet')")
    
    # Pré-calcul des stats de la page d'accueil
    top_groups = db.execute("SELECT groupe, total_cadeaux_groupe FROM groups ORDER BY total_cadeaux_groupe DESC LIMIT 5").df().to_dict(orient="records")
    global_total = db.execute("SELECT SUM(total_cadeaux_groupe) FROM groups").fetchone()[0]
    
    LANDING_CACHE = {
        "top_groups": top_groups,
        "total_global": global_total
    }
    print("✅ Radar armé. Latence : 0ms.")

@app.get("/")
async def root():
    return FileResponse('index.html')

@app.get("/api/v1/landing-stats")
def get_landing_stats():
    return LANDING_CACHE

@app.get("/api/v1/search")
def search(q: str):
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

@app.get("/api/v1/nearby")
def nearby(lat: float, lon: float):
    # Formule Haversine pour trouver les médecins à moins de 5km de l'utilisateur
    query = f"""
        SELECT 
            s.*,
            (6371 * acos(cos(radians({lat})) * cos(radians(latitude)) * cos(radians(longitude) - radians({lon})) + sin(radians({lat})) * sin(radians(latitude)))) AS distance,
            COALESCE(i.roi_influence, 0) as roi,
            COALESCE(i.pct_princeps, 0) as part_de_marche,
            COALESCE(m.top_produits, 'traitements brevetés') as medocs
        FROM search_data s
        JOIN regions r ON s.region_code = r.code
        LEFT JOIN influence i ON s.labo_normalise = i.labo AND i.region = r.libelle_reg
        LEFT JOIN meds m ON s.labo_normalise = m.labo_ansm
        WHERE latitude IS NOT NULL
        HAVING distance < 5
        ORDER BY distance ASC, montant_cumule DESC
        LIMIT 10
    """
    res = db.execute(query).df().fillna(0)
    return res.to_dict(orient="records")
