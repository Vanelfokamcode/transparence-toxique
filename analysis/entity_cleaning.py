import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🧼 Nettoyage final des entités (Normalisation des noms)...")

# 1. On s'assure que les spécialités sont propres dans la table source
con.execute("""
    UPDATE stg_transparence 
    SET specialite = 'Médecin' 
    WHERE specialite ILIKE 'Médecin%' OR specialite ILIKE 'Docteur%';
    
    UPDATE stg_transparence 
    SET specialite = 'Pharmacien' 
    WHERE specialite ILIKE 'Pharmacien%';
""")

# 2. On crée une table de dimension propre pour les labos
con.execute("""
    CREATE OR REPLACE TABLE dim_labos AS
    SELECT 
        labo_ansm as labo_id,
        MIN(nom_medicament) as exemple_produit,
        COUNT(DISTINCT cip13) as nb_references
    FROM bridge_pharma
    GROUP BY 1;
""")

print("✅ Table dim_labos créée.")

# 3. VÉRIFICATION : ROI SANOFI vs PFIZER (Correction du nom de colonne)
print("\n🔎 FOCUS : ROI SANOFI vs PFIZER (Moyenne Nationale)")
print(con.execute("""
    SELECT 
        labo, 
        ROUND(AVG(roi_influence), 0) as roi_moyen,
        ROUND(SUM(ventes_princeps)/1e6, 1) as ventes_totales_Meur
    FROM fact_influence
    WHERE labo LIKE '%SANOFI%' OR labo LIKE '%PFIZER%'
    GROUP BY 1
    ORDER BY 2 DESC;
""").df().to_string())
