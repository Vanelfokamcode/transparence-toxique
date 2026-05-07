import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Nettoyage des noms et nouvelle tentative de jointure...")

# On crée une fonction de nettoyage dans la requête
# On enlève : LABORATOIRE, S.A.S, FRANCE, SANTE, etc.
con.execute("""
    CREATE OR REPLACE TABLE map_labos AS 
    WITH clean_t AS (
        SELECT DISTINCT labo as orig, 
        UPPER(REGEXP_REPLACE(labo, 'LABORATOIRES?|LABO|FRANCE|SAS|S.A.S|SA|S.A|DEVELOPPEMENT|SANTE|PHARMA', '', 'g')) as clean
        FROM stg_transparence_geo
    ),
    clean_a AS (
        SELECT DISTINCT labo_ansm as orig, 
        UPPER(REGEXP_REPLACE(labo_ansm, 'LABORATOIRES?|LABO|FRANCE|SAS|S.A.S|SA|S.A|DEVELOPPEMENT|SANTE|PHARMA', '', 'g')) as clean
        FROM bridge_pharma
    )
    SELECT DISTINCT 
        t.orig as name_transparence,
        a.orig as name_ansm
    FROM clean_t t
    JOIN clean_a a ON TRIM(t.clean) = TRIM(a.clean)
    WHERE LENGTH(TRIM(t.clean)) > 3; -- On évite les noms trop courts
""")

# Vérification
count = con.execute("SELECT COUNT(*) FROM map_labos").fetchone()[0]
print(f"✅ {count} laboratoires reliés proprement.")

# Aperçu des mariages réussis
print("\n🔗 NOUVELLES CORRESPONDANCES (VÉRIFICATION) :")
print(con.execute("SELECT * FROM map_labos WHERE name_transparence LIKE 'SANOFI%' OR name_transparence LIKE 'PFIZER%' LIMIT 10").df())
