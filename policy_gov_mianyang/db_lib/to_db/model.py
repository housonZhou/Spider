# -*- coding: utf-8 -*-
import traceback
traceback.print_exc()
from sqlalchemy import Column, Float, Boolean
from sqlalchemy.dialects.oracle.base import VARCHAR2, CLOB, TIMESTAMP, INTEGER
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from db_lib.to_db.settings import Config

c = Config()
DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DATABASE = c.DB_USERNAME, c.DB_PASSWORD, c.DB_HOST, c.DB_PORT, c.DATABASE
DATABASE_URL = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DATABASE
)
ENGINE = create_engine(DATABASE_URL)
Base = declarative_base()  # pylint:disable=C0103


class Mixin:
    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    TITLE = Column(VARCHAR2(4000), nullable=False, unique=True, comment='标题')
    PUBLISH_DATE = Column(TIMESTAMP(6), nullable=False, index=True, comment='发布时间')
    PUBLISH_AGENCY_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='发布机构ID')
    CONTENT = Column(CLOB, nullable=True, comment='正文内容')
    CONTENT_HTML = Column(CLOB, nullable=True, comment='HTML格式正文内容')
    WEB_LINK = Column(VARCHAR2(255), nullable=False, comment='网页链接')
    WEBSITE = Column(VARCHAR2(255), nullable=False, comment='来源网站')
    ATTACH_TITLE = Column(VARCHAR2(4000), nullable=True, comment='附件名')
    ATTACH_LINK = Column(VARCHAR2(4000), nullable=True, comment='附件链接')
    ATTACH_PATH = Column(VARCHAR2(4000), nullable=True, comment='附件路径')


# 政策文件表
class Policy(Mixin, Base):
    """
    政策表
    """
    __tablename__ = 'BIZ_GMESP_PLCY'

    FILE_NO = Column(VARCHAR2(255), nullable=True, comment='文号')
    VALID_PERIOD = Column(INTEGER, nullable=True, comment='有效时间')
    REGION_ID = Column(VARCHAR2(50), nullable=True, index=True, comment='区域ID')
    POLICYDECODE_ID = Column(VARCHAR2(48), nullable=True, comment='政策解读ID')
    IS_ENTERPRISE = Column(Boolean, nullable=True, comment='是否涉企(1:True, 0:False)')
    FUNC_LABEL_ID = Column(VARCHAR2(48), nullable=True, comment='功能领域标签')
    APPLICATION = Column(CLOB, nullable=True, comment='申请条件')
    MATERIAL = Column(CLOB, nullable=True, comment='申请材料')
    TARGET = Column(CLOB, nullable=True, comment='扶持对象')
    SUPPORT = Column(CLOB, nullable=True, comment='扶持力度')
    IS_HIDE = Column(Boolean, nullable=False, index=True, comment='是否隐藏(1:True, 0:False)', default=0)
    IS_TOP = Column(Boolean, nullable=False, index=True, comment='是否置顶(1:True, 0:False)', default=0)
    TOP_TIME = Column(TIMESTAMP(6), nullable=False, comment='置顶时间')
    CREATE_DATE = Column(TIMESTAMP(6), nullable=False, comment='创建时间')


# 法律法规表
class Law(Base):
    """
    法律法规表
    """
    __tablename__ = 'BIZ_GMESP_LAW'

    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    TITLE = Column(VARCHAR2(4000), nullable=False, unique=True, comment='标题')
    WEB_LINK = Column(VARCHAR2(255), nullable=False, comment='网页链接')
    WEBSITE = Column(VARCHAR2(255), nullable=False, comment='来源网站')
    PUBLISH_DATE = Column(TIMESTAMP(6), nullable=True, comment='发布时间')
    PUBLISH_AGENCY_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='发布机构ID')
    FILE_NO = Column(VARCHAR2(400), nullable=True, comment='文号')
    IS_HIDE = Column(Boolean, nullable=False, index=True, comment='是否隐藏(1:False, 0:True)', default=1)
    IS_TOP = Column(Boolean, nullable=False, index=True, comment='是否置顶(1:True, 0:False)', default=0)
    TOP_TIME = Column(TIMESTAMP(6), nullable=False, comment='置顶时间')
    CREATE_DATE = Column(TIMESTAMP(6), nullable=False, comment='创建时间')


# 政策解读表
class PolicyDecode(Base):
    """
    政策解读表
    """
    __tablename__ = 'BIZ_GMESP_POLICYDECODE'

    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    TITLE = Column(VARCHAR2(4000), nullable=False, unique=True, comment='标题')
    WEB_LINK = Column(VARCHAR2(255), nullable=False, comment='网页链接')
    WEBSITE = Column(VARCHAR2(255), nullable=False, comment='来源网站')
    PUBLISH_DATE = Column(TIMESTAMP(6), nullable=True, comment='发布时间')
    PUBLISH_AGENCY_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='发布机构ID')
    IS_HIDE = Column(Boolean, nullable=False, index=True, comment='是否隐藏(1:False, 0:True)', default=1)
    IS_TOP = Column(Boolean, nullable=False, index=True, comment='是否置顶(1:True, 0:False)', default=0)
    TOP_TIME = Column(TIMESTAMP(6), nullable=False, comment='置顶时间')
    CREATE_DATE = Column(TIMESTAMP(6), nullable=False, comment='创建时间')


class BaseLabel:
    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    RATE = Column(Float, nullable=False, comment='所占百分比')


# 产业领域百分比表--政策
class IndustryLabel(BaseLabel, Base):
    """
    产业类别标签表
    """
    __tablename__ = 'BIZ_GMESP_INDUSTRY_LABEL_PLCY'

    INDUSTRY_NAME_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='产业名称ID')
    POLICY_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='政策ID')


# 项目领域百分比表--政策
class ProjectLabel(BaseLabel, Base):
    """
    项目类别标签表
    """
    __tablename__ = 'BIZ_GMESP_PROJ_LABEL_PLCY'

    PROJECT_NAME_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='项目名称ID')
    POLICY_ID = Column(VARCHAR2(48), nullable=False, index=True, comment='政策ID')


class Industry(Base):
    """
    产业名称表
    """
    __tablename__ = 'BIZ_GMESP_INDUSTRY_NAME'

    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    NAME = Column(VARCHAR2(255), nullable=False, unique=True, comment='产业类别名称')


class Project(Base):
    """
    项目名称表
    """
    __tablename__ = 'BIZ_GMESP_PROJECT_NAME'

    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    NAME = Column(VARCHAR2(255), nullable=False, unique=True, comment='项目类别名称')


class Func(Base):
    """
    功能领域名称表
    """
    __tablename__ = 'BIZ_GMESP_FUNC_LABEL'
    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    NAME = Column(VARCHAR2(255), nullable=False, unique=True, comment='功能领域名称')


class PublishAgency(Base):
    """
    发布机构表
    """
    __tablename__ = 'BIZ_GMESP_PUBLISH_AGENCY'

    ID = Column(VARCHAR2(48), primary_key=True, comment='主键ID')
    AGENCY_NAME = Column(VARCHAR2(255), nullable=False, comment='机构名称')
    REGION_ID = Column(VARCHAR2(48), nullable=False, comment='区域ID')


class Region(Base):
    """
    区域表
    """
    __tablename__ = 'BIZ_GMESP_REGION'

    ID = Column(VARCHAR2(50), primary_key=True, comment='主键ID')
    REGION_NAME = Column(VARCHAR2(255), nullable=False, comment='区域名')


def drop_all():
    """delete all tables that inherit from Base.Do not recommend that use to delete tables"""
    Base.metadata.drop_all(bind=ENGINE)


def create_all():
    """create all tables which inherit from Base"""
    Base.metadata.create_all(bind=ENGINE)


# pylint:disable=C0103
Session = sessionmaker(bind=ENGINE)
session = Session()
