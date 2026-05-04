"""Proxy Tianditu tiles to avoid browser Referer restrictions."""
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router = APIRouter(prefix="/api/tiles", tags=["tiles"])

SUBDOMAINS = ['0', '1', '2', '3', '4', '5', '6', '7']
TDT_KEY = 'e379fb49ee78c37fe845e2ebf1c0b304'

# 天地图 WMTS 图层: vec(矢量) cva(矢量注记) ter(地形晕渲) cta(地形注记) img(影像) cia(影像注记)
LAYERS = {
    'vec': 'vec', 'cva': 'cva',
    'ter': 'ter', 'cta': 'cta',
    'img': 'img', 'cia': 'cia',
}


@router.get("/{layer}/{z}/{x}/{y}")
def tile_proxy(layer: str, z: int, x: int, y: int):
    """Proxy 天地图 WMTS tile request."""
    if layer not in LAYERS:
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}")
    lyr = LAYERS[layer]
    for s in SUBDOMAINS:
        url = (
            f"https://t{s}.tianditu.gov.cn/{lyr}_w/wmts"
            f"?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0"
            f"&LAYER={lyr}&STYLE=default&TILEMATRIXSET=w"
            f"&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}"
            f"&tk={TDT_KEY}"
        )
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as resp:
                return Response(content=resp.read(), media_type="image/png")
        except Exception:
            continue
    raise HTTPException(status_code=502, detail="All Tianditu subdomains failed")
