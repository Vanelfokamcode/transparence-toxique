from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import duckdb
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

HF_USER = os.getenv("HF_USER", "pentagonaiee")
BASE_URL = f"https://huggingface.co/datasets/{HF_USER}/transparence-toxique/resolve/main"

db = duckdb.connect(':memory:')
db.execute("INSTALL httpfs; LOAD httpfs;")

LANDING_CACHE = {}

@app.on_event("startup")
def startup_event():
    global LANDING_CACHE
    # ... (chargement des tables) ...
    
    # On force le cast en FLOAT pour le JSON
    res_groups = db.execute("SELECT labo_source as groupe, CAST(SUM(montant_cumule) AS FLOAT) as total FROM search_data GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df()
    top_groups = res_groups.to_dict(orient="records")
    
    raw_total = db.execute("SELECT SUM(montant_cumule) FROM search_data").fetchone()[0]
    global_total = float(raw_total) if raw_total else 0.0
    
    LANDING_CACHE = {
        "top_groups": top_groups,
        "total_global": global_total
    }
    
@app.get("/api/v1/search")
def search(q: str):
    query = f"""
        SELECT 
            s.*,
            COALESCE(i.roi_influence, 0) as roi,
            COALESCE(i.pct_princeps, 0) as part_de_marche,
            COALESCE(m.top_produits, 'leurs traitements brevetés') as medocs
        FROM search_data s
        LEFT JOIN regions r ON s.region_code = r.code
        LEFT JOIN influence i ON s.labo_normalise = i.labo AND i.region = r.libelle_reg
        LEFT JOIN meds m ON s.labo_normalise = m.labo_ansm
        WHERE s.nom ILIKE '%{q}%' OR s.ville ILIKE '%{q}%'
        ORDER BY s.montant_cumule DESC
        LIMIT 15
    """
    return db.execute(query).df().fillna(0).to_dict(orient="records")

@app.get("/api/v1/landing-stats")
def get_landing_stats(): return LANDING_CACHE

@app.get("/")
async def root(): return FileResponse('index.html')
