import duckdb

con = duckdb.connect("data/pharma.duckdb")

print("🗺️ Construction du pont géographique (Villes -> Régions)...")

# Table de correspondance officielle Dept -> Region
con.execute("""
    CREATE OR REPLACE TABLE ref_dept_to_reg (dept_code VARCHAR, region_code VARCHAR);
    INSERT INTO ref_dept_to_reg VALUES 
    ('01','84'), ('02','32'), ('03','84'), ('04','93'), ('05','93'), ('06','93'),
    ('07','84'), ('08','44'), ('09','76'), ('10','44'), ('11','76'), ('12','76'),
    ('13','93'), ('14','28'), ('15','84'), ('16','75'), ('17','75'), ('18','24'),
    ('19','75'), ('21','27'), ('22','53'), ('23','75'), ('24','75'), ('25','27'),
    ('26','84'), ('27','28'), ('28','24'), ('29','53'), ('30','76'), ('31','76'),
    ('32','76'), ('33','75'), ('34','76'), ('35','53'), ('36','24'), ('37','24'),
    ('38','84'), ('39','27'), ('40','75'), ('41','24'), ('42','84'), ('43','84'),
    ('44','52'), ('45','24'), ('46','76'), ('47','75'), ('48','76'), ('49','52'),
    ('50','28'), ('51','44'), ('52','44'), ('53','52'), ('54','44'), ('55','44'),
    ('56','53'), ('57','44'), ('58','27'), ('59','32'), ('60','32'), ('61','28'),
    ('62','32'), ('63','84'), ('64','75'), ('65','76'), ('66','76'), ('67','44'),
    ('68','44'), ('69','84'), ('70','27'), ('71','27'), ('72','52'), ('73','84'),
    ('74','84'), ('75','11'), ('76','28'), ('77','11'), ('78','11'), ('79','75'),
    ('80','32'), ('81','76'), ('82','76'), ('83','93'), ('84','93'), ('85','52'),
    ('86','75'), ('87','75'), ('88','44'), ('89','27'), ('90','27'), ('91','11'),
    ('92','11'), ('93','11'), ('94','11'), ('95','11'), ('2A','94'), ('2B','94');
""")

# Mise à jour de stg_transparence
# On extrait le département du code_postal
print("🔄 Liaison des cadeaux à leurs régions respectives...")
con.execute("""
    -- On crée une vue pour extraire le département
    CREATE OR REPLACE VIEW v_transparence_geo AS 
    SELECT 
        *,
        SUBSTRING(LPAD(CAST(code_postal AS VARCHAR), 5, '0'), 1, 2) as dept_code
    FROM read_csv_auto('data/raw/transparence_sante/transparence_sante.csv', all_varchar=True);

    -- On crée la table finale de Transparence avec la région
    CREATE OR REPLACE TABLE stg_transparence_geo AS 
    SELECT 
        t.*,
        r.region_code
    FROM stg_transparence t
    LEFT JOIN v_transparence_geo v ON t.nom = v.identite AND t.date = v.date
    LEFT JOIN ref_dept_to_reg r ON v.dept_code = r.dept_code;
""")

print("✅ Pont géographique terminé.")
