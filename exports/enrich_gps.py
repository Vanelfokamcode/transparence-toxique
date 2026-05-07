import duckdb
import os

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Nettoyage radical et Agrégation GPS...")

# 1. On recharge le référentiel GPS proprement
url_gps = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/correspondance-code-insee-code-postal/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"
con.execute(f"CREATE OR REPLACE TABLE raw_gps_ref AS SELECT * FROM read_csv_auto('{url_gps}', delim=';')")

# 2. On crée une table CP -> GPS -> REGION unique
# On utilise la table ref_dept_to_reg qu'on a créé au Chapitre 5
con.execute("""
    CREATE OR REPLACE TABLE map_geo_ref AS 
    SELECT 
        r.cp,
        r.lat,
        r.lon,
        d.region_code
    FROM (
        SELECT 
            "Code Postal" as cp,
            CAST(split_part(geo_point_2d, ',', 1) AS DOUBLE) as lat,
            CAST(split_part(geo_point_2d, ',', 2) AS DOUBLE) as lon,
            SUBSTRING(LPAD(CAST("Code Postal" AS VARCHAR), 5, '0'), 1, 2) as dept
        FROM raw_gps_ref
        WHERE geo_point_2d IS NOT NULL
        QUALIFY ROW_NUMBER() OVER(PARTITION BY cp) = 1
    ) r
    JOIN ref_dept_to_reg d ON r.dept = d.dept_code;
""")

# 3. ON AGRÈGE TOUT DEPUIS LA SOURCE SANS DOUBLONS
con.execute("""
    CREATE OR REPLACE TABLE search_medecins_final AS
    WITH raw_aggregated AS (
        SELECT 
            identite as nom,
            prenom,
            ville,
            profession_libelle as specialite,
            raison_sociale as labo_source,
            SUBSTRING(LPAD(CAST(code_postal AS VARCHAR), 5, '0'), 1, 5) as cp,
            SUM(CAST(REPLACE(CAST(montant AS VARCHAR), ',', '.') AS DECIMAL(18,2))) as total_montant
        FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        WHERE montant IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5, 6
    )
    SELECT 
        r.nom, 
        COALESCE(NULLIF(r.prenom, 'null'), '') as prenom, 
        r.ville, 
        r.specialite,
        r.labo_source,
        m.name_ansm as labo_normalise,
        g.region_code,
        r.total_montant as montant_cumule,
        g.lat as latitude,
        g.lon as longitude
    FROM raw_aggregated r
    LEFT JOIN map_labos m ON r.labo_source = m.name_transparence
    LEFT JOIN map_geo_ref g ON r.cp = g.cp
    WHERE r.total_montant > 500;
""")

# Sauvegarde finale pour Hugging Face
con.execute("COPY search_medecins_final TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")
print(f"✅ Opération terminée. {con.execute('SELECT COUNT(*) FROM search_medecins_final').fetchone()[0]} dossiers uniques exportés.")
