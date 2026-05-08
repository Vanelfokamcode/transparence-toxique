import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Nettoyage forensic : Agrégation et suppression des doublons...")

con.execute("""
    CREATE OR REPLACE TABLE search_medecins_final AS
    WITH raw_clean AS (
        -- On élimine les doublons de déclaration à la source
        SELECT DISTINCT 
            identite, prenom, ville, profession_libelle, raison_sociale, montant, date
        FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        WHERE montant IS NOT NULL
    ),
    aggregated AS (
        -- On cumule par duo Bénéficiaire/Labo
        SELECT 
            identite as nom,
            prenom,
            ville,
            profession_libelle as specialite,
            raison_sociale as labo_source,
            SUM(CAST(REPLACE(CAST(montant AS VARCHAR), ',', '.') AS DECIMAL(18,2))) as montant_total
        FROM raw_clean
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT 
        a.*,
        m.name_ansm as labo_normalise,
        (SELECT MAX(region_code) FROM stg_transparence_geo g WHERE g.nom = a.nom AND g.ville = a.ville) as region_code
    FROM aggregated a
    LEFT JOIN map_labos m ON a.labo_source = m.name_transparence
    WHERE a.montant_total > 500
    ORDER BY montant_total DESC;
""")

con.execute("COPY search_medecins_final TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")
print("✅ Fichier Parquet purifié et prêt.")
