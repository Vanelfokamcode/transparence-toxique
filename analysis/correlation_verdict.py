import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("⚖️  Calcul du Verdict : Croisement Argent vs Ventes...")

# 1. On prépare l'AGRÉGATION DE L'ARGENT (Nettoyée, par Région)
# On filtre sur les motifs d'influence directe (repas, transports, etc.)
con.execute("""
    CREATE OR REPLACE TABLE agg_money_clean AS
    WITH clean_money AS (
        SELECT 
            m.name_ansm as labo_ansm,
            r.region_code,
            t.montant
        FROM stg_transparence t
        JOIN map_labos m ON t.labo = m.name_transparence
        JOIN (
            -- On extrait le département du fichier source pour avoir la région
            SELECT DISTINCT identite, date, SUBSTRING(LPAD(CAST(code_postal AS VARCHAR), 5, '0'), 1, 2) as dept
            FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
        ) v ON t.nom = v.identite AND t.date = v.date
        JOIN ref_dept_to_reg r ON v.dept = r.dept_code
        WHERE t.motif IN (
            'Hospitalité - restauration', 'Hospitalité - hébergement',
            'Frais de transport', 'Frais d''inscription à une manifestation',
            'Contrat de participation à une manifestation'
        )
    )
    SELECT labo_ansm, region_code, SUM(montant) as total_cadeaux
    FROM clean_money
    GROUP BY 1, 2;
""")

# 2. On croise avec les VENTES (Princeps uniquement)
con.execute("""
    CREATE OR REPLACE TABLE fact_influence AS
    SELECT 
        m.labo_ansm as labo,
        reg.libelle_reg as region,
        m.total_cadeaux,
        p.ventes_princeps,
        -- ROI : Pour 1€ de cadeau, combien d'€ de ventes de marque ?
        ROUND(p.ventes_princeps / NULLIF(m.total_cadeaux, 0), 0) as roi_influence
    FROM agg_money_clean m
    JOIN (
        -- On agrège les ventes princeps par labo/region
        SELECT labo_ansm, code_region, SUM(total_rembourse) as ventes_princeps
        FROM marts_prescriptions_v2
        WHERE est_generique = '0'
        GROUP BY 1, 2
    ) p ON m.labo_ansm = p.labo_ansm AND m.region_code = p.code_region
    JOIN ref_regions reg ON m.region_code = reg.code
    WHERE m.total_cadeaux > 1000; -- On ignore les bruits de fond
""")

print("✅ Table fact_influence générée.")

# --- LE TOP 15 DU ROI D'INFLUENCE ---
print("\n🔥 TOP 15 : OÙ L'INFLUENCE EST-ELLE LA PLUS 'RENTABLE' ?")
print("(Pour 1€ de cadeau -> X€ de médicaments de marque prescrits)")
print(con.execute("""
    SELECT labo, region, 
           ROUND(total_cadeaux/1e3, 1) as cadeaux_keur,
           ROUND(ventes_princeps/1e6, 1) as ventes_Meur,
           roi_influence
    FROM fact_influence
    ORDER BY roi_influence DESC
    LIMIT 15
""").df().to_string())
