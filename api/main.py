from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Blindage CORS pour GitHub Pages
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HF_USER = os.getenv("HF_USER", "pentagonaiee")
BASE_URL = f"https://huggingface.co/datasets/{HF_USER}/transparence-toxique/resolve/main"

def get_con():
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    return con

@app.get("/")
async def root():
    return {"status": "ONLINE", "investigation": "Transparence Toxique active"}

@app.get("/api/v1/search")
def search(q: str):
    con = get_con()
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
            FROM read_parquet('{BASE_URL}/search_medecins.parquet') s
            JOIN read_parquet('{BASE_URL}/ref_regions.parquet') r ON s.region_code = r.code
            LEFT JOIN read_parquet('{BASE_URL}/fact_influence.parquet') i 
              ON s.labo_normalise = i.labo AND i.region = r.libelle_reg
            LEFT JOIN read_parquet('{BASE_URL}/labo_top_meds.parquet') m
              ON s.labo_normalise = m.labo_ansm
            WHERE s.nom ILIKE '%{q}%' OR (s.ville ILIKE '{q}%' AND LENGTH('{q}') > 3)
        )
        SELECT * FROM raw_results ORDER BY priority ASC, montant_cumule DESC LIMIT 15
    """
    res = con.execute(query).df().fillna(0)
    return res.to_dict(orient="records")

@app.get("/api/v1/landing-stats")
def get_landing_stats():
    con = get_con()
    top_groups = con.execute(f"SELECT groupe, total_cadeaux_groupe FROM read_parquet('{BASE_URL}/fact_influence_groups.parquet') ORDER BY total_cadeaux_groupe DESC LIMIT 5").df()
    top_villes = con.execute(f"SELECT ville, SUM(montant_cumule) as total FROM read_parquet('{BASE_URL}/search_medecins.parquet') GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df()
    global_total = con.execute(f"SELECT SUM(total_cadeaux_groupe) FROM read_parquet('{BASE_URL}/fact_influence_groups.parquet')").fetchone()[0]
    return {
        "top_groups": top_groups.to_dict(orient="records"),
        "top_villes": top_villes.to_dict(orient="records"),
        "total_global": global_total
    }
