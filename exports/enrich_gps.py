import duckdb
import os

con = duckdb.connect("data/pharma.duckdb")

print("🌍 Récupération du référentiel GPS (Miroir Opendatasoft)...")

# URL stable du référentiel des communes (Codes Postaux + GPS)
url_gps = "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/correspondance-code-insee-code-postal/exports/csv?lang=fr&timezone=Europe%2FBerlin&use_labels=true&delimiter=%3B"

try:
    # 1. On charge le référentiel dans une table temporaire
    con.execute(f"CREATE OR REPLACE TABLE raw_gps_ref AS SELECT * FROM read_csv_auto('{url_gps}', delim=';')")
    
    # 2. On identifie dynamiquement les colonnes (car les noms varient)
    cols = [c[0] for c in con.execute("DESCRIBE raw_gps_ref").fetchall()]
    cp_col = next((c for c in cols if 'Postal' in c), None)
    geo_col = next((c for c in cols if 'geo' in c.lower() or 'Coord' in c), None)

    if not cp_col or not geo_col:
        print(f"❌ Colonnes non trouvées dans le CSV. Colonnes dispo : {cols}")
        exit()

    print(f"✅ Colonnes identifiées : CP='{cp_col}', GPS='{geo_col}'")

    print("🎯 Reconstruction de la table de recherche (Fusion Identité + CP + GPS)...")
    
    # 3. On crée la table de recherche finale en allant chercher le CP original dans le CSV source
    con.execute(f"""
        CREATE OR REPLACE TABLE search_medecins_gps AS
        WITH gps_clean AS (
            SELECT 
                "{cp_col}" as cp,
                CAST(split_part("{geo_col}", ',', 1) AS DOUBLE) as lat,
                CAST(split_part("{geo_col}", ',', 2) AS DOUBLE) as lon
            FROM raw_gps_ref
            WHERE "{geo_col}" IS NOT NULL
            QUALIFY ROW_NUMBER() OVER(PARTITION BY "{cp_col}") = 1
        ),
        source_with_cp AS (
            -- On ré-extrait le CP du fichier source pour être sûr de la géoloc
            SELECT DISTINCT 
                identite as nom_src, 
                SUBSTRING(LPAD(CAST(code_postal AS VARCHAR), 5, '0'), 1, 5) as cp_src
            FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        )
        SELECT 
            t.nom, 
            t.prenom, 
            t.ville, 
            t.specialite,
            t.labo_source,
            t.labo_normalise,
            t.region_code,
            t.montant_cumule,
            g.lat as latitude,
            g.lon as longitude
        FROM search_medecins t
        LEFT JOIN source_with_cp src ON t.nom = src.nom_src
        LEFT JOIN gps_clean g ON src.cp_src = g.cp;
    """)

    # Sauvegarde finale pour le Cloud
    con.execute("COPY search_medecins_gps TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")
    
    check = con.execute("SELECT COUNT(*) FROM search_medecins_gps WHERE latitude IS NOT NULL").fetchone()[0]
    print(f"✅ Succès final : {check:,} entités géo-localisées.")

except Exception as e:
    print(f"❌ Erreur critique : {e}")
