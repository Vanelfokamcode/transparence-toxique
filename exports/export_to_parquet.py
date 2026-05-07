import duckdb
import os

con = duckdb.connect("data/pharma.duckdb")

print("📦 Exportation des Marts vers Parquet (Format Cloud-Native)...")

# On s'assure que le dossier existe
os.makedirs('exports/parquet', exist_ok=True)

# On liste les tables qui serviront au Dashboard et à l'API
tables_to_export = [
    'fact_influence_groups', # Pour le Top Labos National
    'fact_influence',       # Pour le détail Labo / Région
    'marts_prescriptions_v2', # Pour les courbes de ventes
    'dim_labos',            # Pour la recherche par nom
    'ref_regions'           # Pour la navigation géographique
]

for table in tables_to_export:
    print(f"➡️ Export de {table}...")
    con.execute(f"COPY {table} TO 'exports/parquet/{table}.parquet' (FORMAT PARQUET);")

print(f"\n✅ Export terminé dans exports/parquet/")
print("📊 Poids des fichiers pour le déploiement :")
os.system("ls -lh exports/parquet/")
