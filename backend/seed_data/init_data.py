"""Seed data: early Chinese copper/bronze artifacts from research notes."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine, Base
from app.models import Artifact
from sqlalchemy import func

# Ensure tables exist
Base.metadata.create_all(bind=engine)

seed_data = [
    {
        "name": "黄铜片",
        "site_name": "临潼姜寨",
        "longitude": 109.20, "latitude": 34.38,
        "period_label": "仰韶早期（姜寨一期）",
        "period_start": -4700, "period_end": -4000,
        "culture": "仰韶文化",
        "material": "黄铜",
        "artifact_type": "工具",
        "context_desc": "出于F29地面上，F29地面上还摆放着其他器物，应为火灾（或捐献）倒塌而成的地面。编号T74F29:15。",
        "location_desc": "陕西省西安市临潼区姜寨遗址",
        "notes": "中国迄今发现最早的黄铜制品之一。含锌约25%，表明可能使用炉甘石（菱锌矿）与孔雀石混合冶炼。"
    },
    {
        "name": "黄铜管状物",
        "site_name": "临潼姜寨",
        "longitude": 109.20, "latitude": 34.38,
        "period_label": "仰韶早期（姜寨一期）",
        "period_start": -4700, "period_end": -4000,
        "culture": "仰韶文化",
        "material": "黄铜",
        "artifact_type": "装饰品",
        "context_desc": "出于T259第3层。编号T259(3):39。",
        "location_desc": "陕西省西安市临潼区姜寨遗址",
        "notes": "姜寨一期文化出土的第二件黄铜制品。参考文献：西安半坡博物馆1988。"
    },
    {
        "name": "黄铜遗物",
        "site_name": "渭南北刘",
        "longitude": 109.50, "latitude": 34.50,
        "period_label": "庙底沟期",
        "period_start": -3900, "period_end": -3500,
        "culture": "仰韶文化（庙底沟类型）",
        "material": "黄铜",
        "artifact_type": "工具",
        "context_desc": "上层庙底沟期出土黄铜遗物，报告中未详细介绍。",
        "location_desc": "陕西省渭南市北刘遗址",
        "notes": ""
    },
    {
        "name": "青铜刀",
        "site_name": "东乡林家",
        "longitude": 103.42, "latitude": 35.66,
        "period_label": "马家窑文化晚期",
        "period_start": -3000, "period_end": -2700,
        "culture": "马家窑文化",
        "material": "锡青铜",
        "artifact_type": "工具/兵器",
        "context_desc": "出于F20北壁下。F20中木柱测年5200BP（偏老），F21植物种子测年4700BP，故很可能与F21年代相近。",
        "location_desc": "甘肃省临夏回族自治州东乡族自治县林家遗址",
        "notes": "中国迄今发现最早的青铜器（锡青铜）之一。为单范铸造。另H54中出'铜渣'，可能为冶炼遗物。"
    },
    {
        "name": "倒勾矛",
        "site_name": "陶寺（或相关龙山遗址）",
        "longitude": 111.50, "latitude": 35.90,
        "period_label": "龙山晚期晚段",
        "period_start": -2100, "period_end": -1900,
        "culture": "龙山文化",
        "material": "锡青铜",
        "artifact_type": "兵器",
        "context_desc": "出于龙山晚期晚段H181中。与塞伊玛-图尔宾诺文化现象中的倒勾矛相似，可能受阿尔泰地区影响。",
        "location_desc": "山西省临汾市襄汾县陶寺遗址",
        "notes": "Rawson 2017认为中原地区明显模仿阿尔泰地区倒勾矛。阿尔泰倒勾矛有锋利尖端，中国的体量相对较大。"
    },
    {
        "name": "青铜器",
        "site_name": "吉木乃通天洞",
        "longitude": 86.15, "latitude": 47.50,
        "period_label": "青铜时代早期",
        "period_start": -3000, "period_end": -2000,
        "culture": "通天洞青铜时代遗存",
        "material": "锡青铜",
        "artifact_type": "工具",
        "context_desc": "出土早至公元前三千年的青铜器。",
        "location_desc": "新疆维吾尔自治区阿勒泰地区吉木乃县",
        "notes": "新疆地区最早期的青铜器之一，与欧亚草原青铜文化可能有关联。"
    },
    {
        "name": "孔雀石垂饰",
        "site_name": "昌都卡若",
        "longitude": 97.18, "latitude": 31.05,
        "period_label": "卡若文化",
        "period_start": -3300, "period_end": -2300,
        "culture": "卡若文化",
        "material": "矿石（孔雀石）",
        "artifact_type": "装饰品",
        "context_desc": "第4文化层出土，编号T62④:76，外形似蝉。",
        "location_desc": "西藏自治区昌都市卡若遗址",
        "notes": "年代距今约5300年。孔雀石作为装饰品，说明对铜矿石的认知先于冶炼技术。"
    },
    {
        "name": "孔雀石",
        "site_name": "天门龙嘴",
        "longitude": 113.18, "latitude": 30.67,
        "period_label": "油子岭文化中期",
        "period_start": -3400, "period_end": -3000,
        "culture": "油子岭文化",
        "material": "矿石（孔雀石）",
        "artifact_type": "矿石",
        "context_desc": "TG2第5层出土。编号TG2(5):24。",
        "location_desc": "湖北省天门市龙嘴遗址",
        "notes": "长江中游出土最早的孔雀石之一，年代约BC3350。大洪山区域有铜矿资源分布。"
    },
    {
        "name": "铜铃（或齿轮形器）",
        "site_name": "襄汾陶寺",
        "longitude": 111.50, "latitude": 35.90,
        "period_label": "龙山晚期",
        "period_start": -2300, "period_end": -1900,
        "culture": "陶寺文化",
        "material": "红铜",
        "artifact_type": "礼器",
        "context_desc": "陶寺遗址出土，具体层位待核实。",
        "location_desc": "山西省临汾市襄汾县陶寺遗址",
        "notes": "陶寺出土的红铜制品，是中国早期铜器的重要发现。需进一步核实具体出土单位和数量。"
    },
    {
        "name": "铜渣/炼渣",
        "site_name": "东乡林家",
        "longitude": 103.42, "latitude": 35.66,
        "period_label": "马家窑文化晚期",
        "period_start": -3000, "period_end": -2700,
        "culture": "马家窑文化",
        "material": "炼渣",
        "artifact_type": "炼渣",
        "context_desc": "H54可能是临时居住的窝棚，打破中层F12，底部出'铜渣'。南壁上设有四级台阶。",
        "location_desc": "甘肃省临夏州东乡县林家遗址",
        "notes": "铜渣的发现说明可能存在本地冶炼活动。但需进一步科学分析确认是否为冶炼渣。"
    },
]

db = SessionLocal()
try:
    for item in seed_data:
        lon = item.pop("longitude")
        lat = item.pop("latitude")
        existing = db.query(Artifact).filter(
            Artifact.name == item["name"],
            Artifact.site_name == item["site_name"],
        ).first()
        if existing:
            print(f"SKIP (exists): {item['name']} - {item['site_name']}")
            continue
        geom = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        a = Artifact(geom=geom, **item)
        db.add(a)
        print(f"ADD: {item['name']} - {item['site_name']}")
    db.commit()
    print("Seed data import complete!")
finally:
    db.close()
