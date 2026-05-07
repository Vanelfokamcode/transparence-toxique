import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🏢 Consolidation finale des Groupes (Version Pro)...")

con.execute("""
    CREATE OR REPLACE TABLE fact_influence_groups AS
    WITH grouped AS (
        SELECT 
            CASE 
                WHEN labo LIKE 'SANOFI%' OR labo LIKE 'OPELLA%' THEN 'SANOFI/OPELLA'
                WHEN labo LIKE 'PFIZER%' THEN 'PFIZER'
                WHEN labo LIKE 'NOVARTIS%' THEN 'NOVARTIS'
                WHEN labo LIKE 'BAYER%' THEN 'BAYER'
                WHEN labo LIKE 'MERCK%' THEN 'MERCK'
                WHEN labo LIKE 'SERVIER%' OR labo LIKE 'LES LABORATOIRES SERVIER%' THEN 'SERVIER'
                WHEN labo LIKE 'BIOGARAN%' THEN 'BIOGARAN'
                WHEN labo LIKE 'BOEHRINGER%' THEN 'BOEHRINGER INGELHEIM'
                WHEN labo LIKE 'ASTRAZENECA%' THEN 'ASTRAZENECA'
                WHEN labo LIKE 'VIATRIS%' THEN 'VIATRIS'
                ELSE split_part(REGEXP_REPLACE(labo, '^(LES |LABORATOIRES? |LABO )', '', 'i'), ' ', 1)
            END as groupe,
            SUM(total_cadeaux) as total_cadeaux_groupe,
            SUM(ventes_princeps) as total_ventes_marques_groupe
        FROM fact_influence
        GROUP BY 1
    )
    SELECT 
        UPPER(groupe) as groupe,
        total_cadeaux_groupe,
        total_ventes_marques_groupe,
        ROUND(total_ventes_marques_groupe / NULLIF(total_cadeaux_groupe, 0), 0) as roi_groupe
    FROM grouped
    WHERE total_cadeaux_groupe > 20000 
    ORDER BY roi_groupe DESC;
""")

print("✅ Table fact_influence_groups nettoyée.")
print(con.execute("SELECT * FROM fact_influence_groups LIMIT 10").df().to_string())
