import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🛠️  Réparation de la table fact_influence...")

# On reconstruit la table avec le ROI ET le % de prescriptions de marque
con.execute("""
    CREATE OR REPLACE TABLE fact_influence AS
    SELECT 
        m.labo_ansm as labo,
        reg.libelle_reg as region,
        m.total_cadeaux,
        p.ventes_princeps,
        p.total_ventes,
        -- Part de marché : % de princeps sur le total des ventes du labo dans la région
        ROUND((p.ventes_princeps / NULLIF(p.total_ventes, 0)) * 100, 1) as pct_princeps,
        -- ROI : Pour 1€ de cadeau, combien d'€ de ventes de marque ?
        ROUND(p.ventes_princeps / NULLIF(m.total_cadeaux, 0), 0) as roi_influence
    FROM agg_money_clean m
    JOIN (
        SELECT labo_ansm, code_region, 
               SUM(total_rembourse) as total_ventes,
               SUM(CASE WHEN est_generique = '0' THEN total_rembourse ELSE 0 END) as ventes_princeps
        FROM marts_prescriptions_v2
        GROUP BY 1, 2
    ) p ON m.labo_ansm = p.labo_ansm AND m.region_code = p.code_region
    JOIN ref_regions reg ON m.region_code = reg.code;
""")

print("✅ Table fact_influence réparée avec pct_princeps.")
