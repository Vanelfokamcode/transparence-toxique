import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧪 Nettoyage forensic : Élimination des doublons de la source d'État...")

con.execute("""
    CREATE OR REPLACE TABLE search_medecins_clean AS
    WITH raw_distinct AS (
        -- Étape 1 : On nettoie les doublons administratifs du CSV (SELECT DISTINCT)
        SELECT DISTINCT 
            identite, prenom, ville, profession_libelle, raison_sociale, montant, code_postal, date
        FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        WHERE montant IS NOT NULL
    ),
    aggregated AS (
        -- Étape 2 : On cumule par duo Bénéficiaire/Laboratoire
        SELECT 
            identite as nom,
            prenom,
            ville,
            profession_libelle as specialite,
            raison_sociale as labo_source,
            SUM(CAST(REPLACE(CAST(montant AS VARCHAR), ',', '.') AS DECIMAL(18,2))) as montant_total
        FROM raw_distinct
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT 
        a.nom, 
        COALESCE(NULLIF(a.prenom, 'null'), '') as prenom, 
        a.ville, 
        a.specialite,
        a.labo_source,
        m.name_ansm as labo_normalise,
        -- On récupère la région via un lien sur la ville (on évite le produit cartésien)
        (SELECT MAX(region_code) FROM stg_transparence_geo g WHERE g.nom = a.nom AND g.ville = a.ville) as region_code,
        a.montant_total as montant_cumule
    FROM aggregated a
    LEFT JOIN map_labos m ON a.labo_source = m.name_transparence
    WHERE a.montant_total > 500
    ORDER BY montant_cumule DESC;
""")

con.execute("COPY search_medecins_clean TO 'exports/parquet/search_medecins.parquet' (FORMAT PARQUET);")

# Calcul du total avec conversion en float pour éviter le crash TypeError
raw_total = con.execute("SELECT SUM(montant_cumule) FROM search_medecins_clean").fetchone()[0]
new_total = float(raw_total) if raw_total is not None else 0.0

print(f"✅ Audit purifié. Nouvelle masse identifiée : {new_total / 1e6:.1f} M€")
