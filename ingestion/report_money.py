import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🔍 Analyse des flux financiers (Version Finale Ch. 3) en cours...")

# On crée la table de staging avec les colonnes que tu as listées
con.execute("""
    CREATE OR REPLACE TABLE stg_transparence AS 
    SELECT 
        raison_sociale as labo,
        identite as nom,
        prenom as prenom,
        profession_libelle as specialite,
        ville as ville,
        -- Nettoyage du montant (on gère les virgules et les types)
        CAST(REPLACE(CAST(montant AS VARCHAR), ',', '.') AS DECIMAL(18,2)) as montant,
        date,
        motif_lien_interet as motif
    FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True)
    WHERE montant IS NOT NULL
""")

print("✅ Table stg_transparence créée. Lancement des statistiques...\n")

# 1. Le Top 5 des Labos (La "Ligue des Champions" du cash)
print("🏆 LES 5 LABOS QUI DÉPENSENT LE PLUS :")
print(con.execute("""
    SELECT labo, 
           SUM(montant) as total_euros, 
           COUNT(*) as nb_declarations
    FROM stg_transparence 
    GROUP BY 1 
    ORDER BY 2 DESC 
    LIMIT 5
""").df())

# 2. Les Spécialités les plus ciblées
print("\n🩺 TOP 5 DES PROFESSIONS LES PLUS 'INVITÉES' :")
print(con.execute("""
    SELECT specialite, 
           SUM(montant) as total_euros
    FROM stg_transparence 
    WHERE specialite IS NOT NULL 
    GROUP BY 1 
    ORDER BY 2 DESC 
    LIMIT 5
""").df())

# 3. Le Motif du lien (Pourquoi paient-ils ?)
print("\n❓ POURQUOI CET ARGENT EST-IL VERSÉ ?")
print(con.execute("""
    SELECT motif, 
           COUNT(*) as nb_fois,
           SUM(montant) as total_euros
    FROM stg_transparence 
    GROUP BY 1 
    ORDER BY 3 DESC 
    LIMIT 5
""").df())