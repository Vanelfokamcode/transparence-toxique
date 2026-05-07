import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧹 Étape 3 (bis) — Reconstruction des Marts avec nettoyage double-passe...")

# On nettoie REM et BOITES : d'abord on vire le '.', puis on remplace le ',' par '.'
con.execute("""
    CREATE OR REPLACE TABLE marts_prescriptions_v2 AS
    SELECT
        r.ben_reg                                                       AS code_region,
        r.cip13,
        r.top_gen                                                       AS est_generique,
        b.labo_ansm,
        -- On traite le cas où boites ou rem pourraient être NULL ou vides
        SUM(CAST(REPLACE(REPLACE(COALESCE(r.boites, '0'), '.', ''), ',', '.') AS DOUBLE)) AS total_boites,
        SUM(CAST(REPLACE(REPLACE(COALESCE(r.rem, '0'), '.', ''), ',', '.') AS DOUBLE))    AS total_rembourse
    FROM raw_prescriptions r
    JOIN bridge_pharma b ON r.cip13 = b.cip13
    WHERE r.ben_reg IS NOT NULL
    GROUP BY r.ben_reg, r.cip13, r.top_gen, b.labo_ansm
""")

count = con.execute("SELECT COUNT(*) FROM marts_prescriptions_v2").fetchone()[0]
print(f"✅ marts_prescriptions_v2 : {count:,} lignes reconstruites.")

print("\n🏢 TOP 10 DES LABOS PAR VENTES (VÉRIFICATION DU PONT CIP13) :")
print(con.execute("""
    SELECT labo_ansm,
           ROUND(SUM(total_rembourse)/1e6, 1) as ventes_M_eur,
           COUNT(DISTINCT cip13) as nb_medicaments
    FROM marts_prescriptions_v2
    GROUP BY labo_ansm
    ORDER BY ventes_M_eur DESC
    LIMIT 10
""").df().to_string())
