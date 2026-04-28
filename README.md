# 中国出土早期铜器数据库与 WebGIS 地图

交互式 WebGIS 地图展示中国早期铜器（红铜、黄铜、青铜、砷铜等）的出土地点、年代、材质、器型等信息。

## 技术栈

- **数据库**: PostgreSQL 17 + PostGIS
- **后端**: FastAPI + SQLAlchemy + GeoAlchemy2
- **前端**: Leaflet.js + Vue 3（CDN 引入，无构建工具）
- **地图底图**: 天地图（地形晕渲 + 注记）
- **坐标系**: WGS84（存储）↔ GCJ-02（地图显示）

## 快速启动

### 1. 数据库

```bash
brew install postgresql@17 postgis
createdb early_bronze
psql early_bronze -c "CREATE EXTENSION postgis;"
```

### 2. 后端

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 导入数据
python seed_data/import_copper.py
python seed_data/geocode_sites.py

# 启动 API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 前端

```bash
cd frontend
python3 -m http.server 5173
```

打开 http://localhost:5173

## API 端点

| 端点 | 说明 |
|---|---|
| `GET /api/artifacts/` | 铜器列表（支持筛选、搜索、分页） |
| `GET /api/artifacts/{id}` | 单件铜器详情 |
| `POST /api/artifacts/` | 新增铜器 |
| `PUT /api/artifacts/{id}` | 编辑铜器 |
| `DELETE /api/artifacts/{id}` | 删除铜器 |
| `GET /api/map/geojson` | 地图 GeoJSON |
| `GET /api/map/stats` | 统计数据 |
| `GET /api/tiles/{layer}/{z}/{x}/{y}` | 天地图瓦片代理 |

## 数据来源

copper.xlsx 包含 798 条早期铜器记录，涵盖：
- 黄河中下游地区（二里头、东下冯、朱开沟等）
- 河西走廊（火烧沟、西城驿、干骨崖等）
- 河湟地区（尕马台、宗日、皇娘娘台等）
- 哈密盆地（天山北路墓地等）
- 燕山地区（大甸子、夏家店等）
