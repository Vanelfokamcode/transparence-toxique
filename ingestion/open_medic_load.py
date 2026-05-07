import duckdb
import os

con = duckdb.connect("data/pharma.duckdb")

print("🐘 Ingestion massive d'Open Medic (2021-2023)...")

# On définit le pattern exact pour tes fichiers en majuscules
path = "data/raw/open_medic/*.CSV"

# Ingestion brute avec DuckDB
# On utilise delim=';' car Open Medic est historiquement en points-virgules
con.execute(f"""
    CREATE OR REPLACE TABLE raw_prescriptions AS 
    SELECT * FROM read_csv_auto(
        '{path}', 
        union_by_name=True, 
        all_varchar=True,
        ignore_errors=True
    )
""")

# Normalisation des colonnes en minuscules
cols = con.execute("PRAGMA table_info('raw_prescriptions')").fetchall()
for col in cols:
    old_name = col[1]
    new_name = old_name.lower()
    if old_name != new_name:
        con.execute(f'ALTER TABLE raw_prescriptions RENAME "{old_name}" TO "{new_name}"')

print("✅ Table raw_prescriptions créée et normalisée.")

# --- ANALYSE DE DÉPART ---

count = con.execute("SELECT COUNT(*) FROM raw_prescriptions").fetchone()[0]
print(f"📊 Total de lignes chargées : {count:,}")

# On vérifie les colonnes critiques
print("\n🔍 Vérification des colonnes pour le croisement :")
res_check = con.execute("""
    SELECT 
        COUNT(DISTINCT pfs_exe_num) as nb_medecins,
        COUNT(DISTINCT l_cip13) as nb_medicaments
    FROM raw_prescriptions
""").df()
print(res_check)

# Le Top 5 des médicaments les plus prescrits (en volume de boîtes)
print("\n💊 TOP 5 DES MÉDICAMENTS (PAR VOLUME) :")
# On tente de caster 'boite' qui est en texte
print(con.execute("""
    SELECT l_cip13, SUM(CAST(REPLACE(boite, ',', '.') AS DECIMAL)) as total_boites
    FROM raw_prescriptions
    WHERE l_cip13 IS NOT NULL
    GROUP BY 1 ORDER BY 2 DESC LIMIT 5
""").df())