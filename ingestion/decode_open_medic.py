import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🛠️ Mise à jour des référentiels...")

# 1. Table des Spécialités
con.execute("""
    CREATE OR REPLACE TABLE ref_specialites (code INTEGER, libelle VARCHAR);
    INSERT INTO ref_specialites VALUES 
    (1, 'Médecine Générale'), (2, 'Anesthésie-Réanimation'), (3, 'Pathologie Cardio-Vasculaire'),
    (4, 'Dermatologie'), (5, 'Gastro-entérologie'), (6, 'Radiodiagnostic et Imagerie'),
    (7, 'Gynécologie Obstétrique'), (8, 'Gastro-entérologie'), (9, 'Médecine Interne'),
    (11, 'Oto-Rhino-Laryngologie'), (12, 'Pédiatrie'), (13, 'Pneumologie'),
    (14, 'Rhumatologie'), (15, 'Ophthalmologie'), (17, 'Psychiatrie'),
    (18, 'Stomatologie'), (19, 'Chirurgie Dentaire'), (31, 'Médecine Physique et Réadaptation'),
    (32, 'Neurologie'), (33, 'Psychiatrie Infanto-Juvénile'), (35, 'Néphrologie'),
    (37, 'Anatomie-Cytopathologie'), (90, 'Pharmacie');
""")

# 2. Table des Régions
con.execute("""
    CREATE OR REPLACE TABLE ref_regions (code VARCHAR, libelle_reg VARCHAR);
    INSERT INTO ref_regions VALUES 
    ('01', 'Guadeloupe'), ('02', 'Martinique'), ('03', 'Guyane'), ('04', 'La Réunion'),
    ('06', 'Mayotte'), ('11', 'Île-de-France'), ('24', 'Centre-Val de Loire'), 
    ('27', 'Bourgogne-Franche-Comté'), ('28', 'Normandie'), ('32', 'Hauts-de-France'), 
    ('44', 'Grand Est'), ('52', 'Pays de la Loire'), ('53', 'Bretagne'), 
    ('75', 'Nouvelle-Aquitaine'), ('76', 'Occitanie'), ('84', 'Auvergne-Rhône-Alpes'), 
    ('93', 'Provence-Alpes-Côte d Azur'), ('94', 'Corse');
""")

print("🧹 Nettoyage complexe (Gestion des séparateurs de milliers)...")

# 3. Création de la table finale avec Double REPLACE
# On enlève le '.' (milliers) ET on remplace le ',' par '.' (décimal)
con.execute("""
    CREATE OR REPLACE TABLE marts_prescriptions AS 
    SELECT 
        r.ben_reg as code_region,
        reg.libelle_reg as region,
        r.psp_spe as code_spe,
        COALESCE(spec.libelle, 'Autre / Inconnu') as specialite,
        r.l_cip13 as medicament,
        r.top_gen as est_generique, 
        SUM(CAST(REPLACE(REPLACE(CAST(r.boites AS VARCHAR), '.', ''), ',', '.') AS DECIMAL(18,3))) as total_boites,
        SUM(CAST(REPLACE(REPLACE(CAST(r.rem AS VARCHAR), '.', ''), ',', '.') AS DECIMAL(18,3))) as total_rembourse
    FROM raw_prescriptions r
    LEFT JOIN ref_regions reg ON r.ben_reg = reg.code
    LEFT JOIN ref_specialites spec ON TRY_CAST(r.psp_spe AS INTEGER) = spec.code
    GROUP BY ALL
""")

print("✅ Chapitre 4 : Données nettoyées et prêtes.")

# --- TEST DE VALIDATION ---
print("\n🔎 VÉRIFICATION : DEPENSES PAR RÉGION (TOP 3)")
res = con.execute("""
    SELECT region, ROUND(SUM(total_rembourse), 2) as total
    FROM marts_prescriptions 
    WHERE region IS NOT NULL 
    GROUP BY 1 ORDER BY 2 DESC LIMIT 3
""").df()
print(res)
