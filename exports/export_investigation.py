import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Purge des doublons et consolidation des montants...")

con.execute("""
    CREATE OR REPLACE TABLE search_medecins_clean AS
    WITH aggregated AS (
        -- On groupe tout par identité/labo dès la source
        SELECT 
            identite as nom,
            prenom,
            ville,
            profession_libelle as specialite,
            raison_sociale as labo_source,
            SUM(CAST(REPLACE(CAST(montant AS VARCHAR), ',', '.') AS DECIMAL(18,2))) as montant_total
        FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        WHERE montant IS NOT NULL
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT 
        a.nom, 
        COALESCE(NULLIF(a.prenom, 'null'), '') as prenom, 
        a.ville, 
        a.specialite,
        a.labo_source,
        m.name_ansm as labo_normalise,
        -- On récupère le code région via une jointure simple sur la ville/nom déjà agrégés
        (SELECT MAX(region_code) FROM stg_transparence_geo g WHERE g.nom = a.nom AND g.ville = a.ville) as region_code,
        a.montant_total as montant_cumule
    FROM aggregated a
    LEFT JOIN map_labos m ON a.labo_source = m.name_transparence
    WHERE a.montant_total > 500
    ORDER BY montant_cumule DESC;
""")

con.execute("COPY search_medecins_clean TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")
print(f"✅ Fichier de recherche purifié : {con.execute('SELECT COUNT(*) FROM search_medecins_clean').fetchone()[0]} dossiers uniques.")
