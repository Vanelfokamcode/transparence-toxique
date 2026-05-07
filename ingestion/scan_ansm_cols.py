import pandas as pd
import io

print("🔎 Scan des colonnes du catalogue ANSM...")
with open('data/raw/ansm/CIS_bdpm.txt', 'rb') as f:
    content = f.read().decode('latin-1', errors='ignore')

# On lit juste 5 lignes pour voir
df_sample = pd.read_csv(io.StringIO(content), sep='\t', header=None, nrows=5)

for i, val in enumerate(df_sample.iloc[0]):
    print(f"Colonne {i} : {val}")
