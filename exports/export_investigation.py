import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Suppression des doublons et agrégation des comptes...")

con.execute("""
    CREATE OR REPLACE TABLE search_medecins AS
    SELECT 
        t.nom, 
        COALESCE(NULLIF(t.prenom, 'null'), '') as prenom, 
        t.ville, 
        t.specialite,
        t.labo as labo_source,
        m.name_ansm as labo_normalise,
        t.region_code,
        SUM(t.montant) as montant_cumule -- On additionne TOUT pour ce duo médecin/labo
    FROM stg_transparence_geo t
    LEFT JOIN map_labos m ON t.labo = m.name_transparence
    WHERE t.montant > 500
    GROUP BY 1, 2, 3, 4, 5, 6, 7 -- On groupe par identité
    ORDER BY montant_cumule DESC
    LIMIT 50000;
""")

con.execute("COPY search_medecins TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")
print("✅ Données de recherche nettoyées et agrégées.")
