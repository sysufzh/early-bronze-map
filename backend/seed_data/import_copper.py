"""Import data from copper.xlsx into the artifacts table."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.database import SessionLocal
from app.models import Artifact

# Read Excel, skip first row (all NaN), use second row as header
df = pd.read_excel(
    '/Users/fanzihao/apps/map/early-bronze-map/copper.xlsx',
    header=1,
)
df.columns = ['序号', '区域', '所属考古学文化', '所属遗址', '器物号', '名称', '数量', '制作方式', '材质', '资料出处']

# Drop the header-row duplicate if present
if str(df.iloc[0]['名称']).strip() == '名称':
    df = df.iloc[1:]

# Normalization: 制作方式
def normalize_production_method(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    mapping = {
        '铸造': '铸造',
        '热锻': '热锻',
        '锻造': '锻造',
        '冷锻': '冷锻',
        '锤击': '锤击',
        '锻制': '锻制',
        '锻打': '锻打',
        '热锻+冷锻': '热锻+冷锻',
        '热锻后冷加工': '热锻+冷加工',
        '铸造冷加工': '铸造+冷加工',
        '铸造+锻打': '铸造+锻打',
        '铸造+热锻': '铸造+热锻',
        '铸造+冷锻': '铸造+冷锻',
        '铸造+局部锻': '铸造+局部锻',
        '铸造，锻制': '铸造+锻制',
        '热锻,冷加工': '热锻+冷加工',
        '铸造(冷加工)': '铸造+冷加工',
        '铸造(热锻,冷加工)': '铸造+热锻+冷加工',
        '铸造(热锻)': '铸造+热锻',
        '铸造，冷锻': '铸造+冷锻',
        '铸造、锻制': '铸造+锻制',
        '铸造、冷锻': '铸造+冷锻',
        '热冷加工': '热加工+冷加工',
        '热加工': '热加工',
        '分铸': '分铸',
        '单范铸造': '单范铸造',
        '铸造后冷加工': '铸造+冷加工',
        '铸造热锻后冷加工': '铸造+热锻+冷加工',
        '退火': '退火',
        '冷锻成形，退火': '冷锻+退火',
        '热锻、冷锻': '热锻+冷锻',
        '热锻，冷加工': '热锻+冷加工',
        '热锻残留铸造组织': '热锻+铸造',
        '冷锻+热锻残留铸造组织': '铸造+热锻+冷锻',
        '热锻+冷锻残留铸造组织': '热锻+冷锻',
        '铸造+冷锻残留铸造组织': '铸造+冷锻',
        '热加工2': '热加工',
        '冰铜铸造': '铸造',
        '组织不清': None,
    }
    return mapping.get(val, val)


# Normalization: 材质
def normalize_material(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    mapping = {
        '锡青铜': '锡青铜',
        '红铜': '红铜',
        '铅锡青铜': '铅锡青铜',
        '砷铜': '砷铜',
        '砷青铜': '砷青铜',
        '铅青铜': '铅青铜',
        '青铜': '青铜',
        '黄铜': '黄铜',
        '铜锡铅三元合金': '铜锡铅三元合金',
        '锡砷青铜': '锡砷青铜',
        '冰铜': '冰铜',
        '含砷锡青铜': '含砷锡青铜',
        '铜锡砷三元合金': '铜锡砷三元合金',
        '砷铜(含铅)': '砷铜（含铅）',
        '红铜(含砷)': '红铜（含砷）',
        '类砷铜': '类砷铜',
        '铅': '铅',
        '锡铅砷青铜': '锡铅砷青铜',
        '锡铅青铜': '锡铅青铜',
        '锡青铜2铅锡青铜1': '锡青铜+铅锡青铜',
        '铅青铜(含砷)': '铅青铜（含砷）',
        '锑青铜': '锑青铜',
        '锡锑青铜': '锡锑青铜',
        '铜锡砷合金': '铜锡砷合金',
        '含锡铜铅砷合金': '含锡铜铅砷合金',
        '红铜,红铜(含砷)': '红铜+红铜（含砷）',
        '铅青铜,红铜(含砷)': '铅青铜+红铜（含砷）',
        '红铜,锡青铜': '红铜+锡青铜',
        '锡青铜（铅）': '锡青铜（含铅）',
        '铜砷铅三元合金': '铜砷铅三元合金',
        '铅锡砷青铜': '铅锡砷青铜',
        '白铜': '白铜',
        '镍黄铜': '镍黄铜',
    }
    return mapping.get(val, val)


# Normalization: 区域
def normalize_region(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    return val


print(f"Total rows in Excel: {len(df)}")

db = SessionLocal()
try:
    imported = 0
    skipped = 0
    for idx, row in df.iterrows():
        name = str(row['名称']).strip() if pd.notna(row['名称']) else None
        if not name or name in ('名称', 'nan'):
            skipped += 1
            continue

        site = str(row['所属遗址']).strip() if pd.notna(row['所属遗址']) else None
        if site and site.lower() == 'nan':
            site = None

        catalog = str(row['器物号']).strip() if pd.notna(row['器物号']) else None
        if catalog and catalog.lower() == 'nan':
            catalog = None

        quantity = str(row['数量']).strip() if pd.notna(row['数量']) else None
        if quantity and quantity.lower() == 'nan':
            quantity = None

        region = normalize_region(row['区域'])
        culture = str(row['所属考古学文化']).strip() if pd.notna(row['所属考古学文化']) else None
        if culture and culture.lower() == 'nan':
            culture = None
        mat = normalize_material(row['材质'])
        prod = normalize_production_method(row['制作方式'])
        ref = str(row['资料出处']).strip() if pd.notna(row['资料出处']) else None
        if ref and ref.lower() == 'nan':
            ref = None

        a = Artifact(
            name=name,
            catalog_number=catalog,
            quantity=quantity,
            region=region,
            site_name=site,
            culture=culture,
            material=mat,
            production_method=prod,
            source_reference=ref,
        )
        db.add(a)
        imported += 1
        if imported % 100 == 0:
            db.commit()
            print(f"  Imported {imported}...")

    db.commit()
    print(f"Import complete! Imported {imported}, skipped {skipped}")
finally:
    db.close()
