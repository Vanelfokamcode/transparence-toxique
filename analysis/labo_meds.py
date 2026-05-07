import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("💊 Extraction des médicaments phares par laboratoire (Version Corrigée)...")

con.execute("""
    CREATE OR REPLACE TABLE labo_top_meds AS
    WITH ranked_meds AS (
        SELECT 
            labo_ansm,
            nom_medicament,
            COUNT(*) as nb_refs,
            ROW_NUMBER() OVER(PARTITION BY labo_ansm ORDER BY COUNT(*) DESC) as rank
        FROM bridge_pharma
        GROUP BY 1, 2
    )
    SELECT 
        labo_ansm,
        string_agg(nom_medicament, ' | ') as top_produits
    FROM ranked_meds
    WHERE rank <= 3
    GROUP BY 1;
""")

con.execute("COPY labo_top_meds TO 'exports/parquet/labo_top_meds.parquet' (FORMAT PARQUET);")
print("✅ Fichier labo_top_meds.parquet généré.")
