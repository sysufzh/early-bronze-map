from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Text, DateTime, func

from .database import Base


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False, comment="器物名称")
    catalog_number = Column(String(200), comment="器物号")
    quantity = Column(String(50), comment="数量")
    region = Column(String(100), comment="区域")
    site_name = Column(String(300), comment="遗址名称")
    geom = Column(Geometry("POINT", srid=4326), nullable=True, comment="空间坐标(WGS84)")
    period_label = Column(String(100), comment="时代标签")
    period_start = Column(Integer, comment="起始年代BC")
    period_end = Column(Integer, comment="结束年代BC")
    culture = Column(String(200), comment="所属考古学文化")
    material = Column(String(100), comment="材质")
    production_method = Column(String(200), comment="制作方式")
    artifact_type = Column(String(100), comment="器型")
    context_desc = Column(Text, comment="出土情境描述")
    location_desc = Column(Text, comment="具体出土地点描述")
    source_reference = Column(Text, comment="资料出处")
    image_url = Column(String(500), comment="图片路径")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class Reference(Base):
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, nullable=False, comment="关联器物ID")
    cite_key = Column(String(100), comment="Zotero cite key")
    title = Column(Text, comment="文献标题")
    authors = Column(String(500), comment="作者")
    year = Column(Integer, comment="出版年份")
    notes = Column(Text, comment="引用备注")
