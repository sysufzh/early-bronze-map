from geoalchemy2 import Geometry
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


class ArtifactImage(Base):
    __tablename__ = "artifact_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(300), nullable=False, comment="文件名，如 二里头_M33_15_01.jpg")
    caption = Column(String(200), comment="图注，如 正面、剖面")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime, server_default=func.now())

    artifact = relationship("Artifact", back_populates="images")


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
    source_pdf = Column(String(300), comment="资料PDF文件名")
    image_url = Column(String(500), comment="图片路径")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    images = relationship("ArtifactImage", back_populates="artifact", cascade="all, delete-orphan")


class Reference(Base):
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, nullable=False, comment="关联器物ID")
    cite_key = Column(String(100), comment="Zotero cite key")
    title = Column(Text, comment="文献标题")
    authors = Column(String(500), comment="作者")
    year = Column(Integer, comment="出版年份")
    notes = Column(Text, comment="引用备注")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, comment="用户名")
    hashed_password = Column(String(200), nullable=False, comment="bcrypt哈希密码")
    is_admin = Column(Boolean, default=False, nullable=False, comment="是否为管理员")
    created_at = Column(DateTime, server_default=func.now())


class PendingEdit(Base):
    __tablename__ = "pending_edits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="提交者")
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True, comment="目标器物，新建则为空")
    action_type = Column(String(20), nullable=False, comment="create | update")
    payload = Column(JSONB, nullable=False, comment="提交的器物数据")
    status = Column(String(20), default="pending", comment="pending | approved | rejected")
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True, comment="审核人")
    review_notes = Column(Text, comment="审核意见")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    submitter = relationship("User", foreign_keys=[user_id], backref="pending_edits")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
