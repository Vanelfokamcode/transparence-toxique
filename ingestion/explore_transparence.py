import duckdb

# On crée notre fichier de base de données final
con = duckdb.connect("data/pharma.duckdb")

# On charge Transparence Santé. 
# Note : On utilise 'all_varchar=True' au début car les fichiers admin sont mal typés
con.execute("""
    CREATE OR REPLACE VIEW raw_transparence AS 
    SELECT * FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', 
                               all_varchar=True)
""")

print("Vue Transparence Santé créée.")