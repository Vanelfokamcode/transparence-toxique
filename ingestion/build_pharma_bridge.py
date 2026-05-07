import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("💊 Liaison des médicaments aux laboratoires (Fichiers nettoyés)...")

# 1. Chargement du catalogue (CIS) - Désormais en UTF-8 propre
con.execute("""
    CREATE OR REPLACE TABLE raw_ansm_cis AS 
    SELECT 
        column0 as cis, 
        column1 as nom_medicament, 
        column8 as labo_ansm 
    FROM read_csv('data/raw/ansm/CIS_bdpm_clean.txt', 
                  sep='\t', 
                  header=False, 
                  quote='', 
                  encoding='UTF8');
""")

# 2. Chargement de la correspondance (CIP13)
con.execute("""
    CREATE OR REPLACE TABLE raw_ansm_cip AS 
    SELECT 
        column0 as cis, 
        column6 as cip13 
    FROM read_csv('data/raw/ansm/CIS_CIP_bdpm_clean.txt', 
                  sep='\t', 
                  header=False, 
                  quote='', 
                  encoding='UTF8');
""")

# 3. Le Pont Final
con.execute("""
    CREATE OR REPLACE TABLE bridge_pharma AS 
    SELECT 
        TRIM(cip.cip13) as cip13, 
        TRIM(cis.nom_medicament) as nom_medicament, 
        TRIM(cis.labo_ansm) as labo_ansm
    FROM raw_ansm_cip cip
    INNER JOIN raw_ansm_cis cis ON TRIM(cip.cis) = TRIM(cis.cis)
    WHERE cip.cip13 IS NOT NULL AND cip.cip13 != '';
""")

print("✅ Chapitre 5 : Le pont industriel est ENFIN terminé.")

# Le verdict des noms
res = con.execute("SELECT labo_ansm, COUNT(*) as nb FROM bridge_pharma GROUP BY 1 ORDER BY 2 DESC LIMIT 5").df()
print("\n🏢 LES MAÎTRES DU CATALOGUE (ANSM) :")
print(res)
