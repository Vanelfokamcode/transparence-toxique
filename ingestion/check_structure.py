import duckdb
con = duckdb.connect("data/pharma.duckdb")

# On liste TOUTES les colonnes présentes
cols = con.execute("PRAGMA table_info('raw_prescriptions')").fetchall()
column_names = [c[1] for c in cols]
print(f"📋 Colonnes réelles : {column_names}")

# On cherche une colonne géographique
geo_cols = [c for c in column_names if 'dep' in c or 'reg' in c or 'dpt' in c]
print(f"📍 Colonnes géo trouvées : {geo_cols}")

# On regarde à quoi ressemble 'psp_spe' (la spécialité)
print("\n🩺 Exemple de spécialités (psp_spe) :")
print(con.execute("SELECT DISTINCT psp_spe FROM raw_prescriptions LIMIT 10").df())