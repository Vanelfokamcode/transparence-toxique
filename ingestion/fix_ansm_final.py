import duckdb
import pandas as pd
import io

con = duckdb.connect("data/pharma.duckdb")

def clean_and_load(file_path, table_name, col_indices):
    print(f"🔥 Chargement chirurgical de {file_path}...")
    with open(file_path, 'rb') as f:
        # On utilise latin-1 pour les accents français, errors='ignore' pour les bytes sales
        content = f.read().decode('latin-1', errors='ignore')
    
    # Lecture avec Pandas pour sa tolérance aux lignes mal formées
    df = pd.read_csv(io.StringIO(content), sep='\t', header=None, dtype=str, on_bad_lines='skip')
    
    # On ne garde que les colonnes vitales identifiées par le scan
    df_filtered = df[list(col_indices.keys())].rename(columns=col_indices)
    
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df_filtered")
    print(f"✅ Table {table_name} créée.")

# 1. CIS_bdpm.txt : CIS=0, Nom=1, Labo=10 (Identifié par le scan)
clean_and_load(
    'data/raw/ansm/CIS_bdpm.txt', 
    'raw_ansm_cis', 
    {0: 'cis', 1: 'nom_medicament', 10: 'labo_ansm'}
)

# 2. CIS_CIP_bdpm.txt : CIS=0, CIP13=6 (Standard immuable)
clean_and_load(
    'data/raw/ansm/CIS_CIP_bdpm.txt', 
    'raw_ansm_cip', 
    {0: 'cis', 6: 'cip13'}
)

# 3. Création du pont final (Bridge Pharma)
# On passe tout en UPPER pour faciliter le croisement avec Transparence Santé
con.execute("""
    CREATE OR REPLACE TABLE bridge_pharma AS 
    SELECT 
        TRIM(cip.cip13) as cip13, 
        TRIM(cis.nom_medicament) as nom_medicament, 
        UPPER(TRIM(cis.labo_ansm)) as labo_ansm
    FROM raw_ansm_cip cip
    INNER JOIN raw_ansm_cis cis ON TRIM(cip.cis) = TRIM(cis.cis)
    WHERE cip.cip13 IS NOT NULL AND cip.cip13 != '' 
      AND cis.labo_ansm IS NOT NULL;
""")

print("\n🏢 LES MAÎTRES DU CATALOGUE (VÉRIFICATION FINALE) :")
res = con.execute("SELECT labo_ansm, COUNT(*) as nb FROM bridge_pharma GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df()
print(res)
