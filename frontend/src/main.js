/* GCJ-02 <-> WGS84 conversion (for 天地图 GCJ-02 tiles) */
const PI = Math.PI;
const X_PI = (PI * 3000.0) / 180.0;
const A = 6378245.0;
const EE = 0.00669342162296594323;

function outOfChina(lng, lat) {
  return lng < 72.004 || lng > 137.8347 || lat < 0.8293 || lat > 55.8271;
}

function transformLat(x, y) {
  let ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * Math.sqrt(Math.abs(x));
  ret += ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) / 3.0;
  ret += ((20.0 * Math.sin(y * PI) + 40.0 * Math.sin((y / 3.0) * PI)) * 2.0) / 3.0;
  ret += ((160.0 * Math.sin((y / 12.0) * PI) + 320.0 * Math.sin((y * PI) / 30.0)) * 2.0) / 3.0;
  return ret;
}

function transformLng(x, y) {
  let ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * Math.sqrt(Math.abs(x));
  ret += ((20.0 * Math.sin(6.0 * x * PI) + 20.0 * Math.sin(2.0 * x * PI)) * 2.0) / 3.0;
  ret += ((20.0 * Math.sin(x * PI) + 40.0 * Math.sin((x / 3.0) * PI)) * 2.0) / 3.0;
  ret += ((150.0 * Math.sin((x / 12.0) * PI) + 300.0 * Math.sin((x / 30.0) * PI)) * 2.0) / 3.0;
  return ret;
}

function wgs84ToGcj02(lng, lat) {
  if (outOfChina(lng, lat)) return [lng, lat];
  let dLat = transformLat(lng - 105.0, lat - 35.0);
  let dLng = transformLng(lng - 105.0, lat - 35.0);
  const radLat = (lat / 180.0) * PI;
  let magic = Math.sin(radLat);
  magic = 1 - EE * magic * magic;
  const sqrtMagic = Math.sqrt(magic);
  dLat = (dLat * 180.0) / (((A * (1 - EE)) / (magic * sqrtMagic)) * PI);
  dLng = (dLng * 180.0) / ((A / sqrtMagic) * Math.cos(radLat) * PI);
  return [lng + dLng, lat + dLat];
}

function gcj02ToWgs84(lng, lat) {
  if (outOfChina(lng, lat)) return [lng, lat];
  const [wgsLng, wgsLat] = wgs84ToGcj02(lng, lat);
  return [lng * 2 - wgsLng, lat * 2 - wgsLat];
}

const API_BASE = 'http://localhost:8000/api';

const materialColors = {
  '红铜': '#e74c3c', '黄铜': '#f1c40f', '锡青铜': '#2ecc71',
  '铅青铜': '#9b59b6', '砷铜': '#e67e22', '砷青铜': '#e67e22',
  '青铜': '#27ae60', '铅锡青铜': '#8e44ad', '白铜': '#bdc3c7',
  '冰铜': '#7f8c8d', '矿石': '#1abc9c', '矿石（孔雀石）': '#1abc9c',
  '炼渣': '#95a5a6',
};
const defaultColor = '#3498db';

let map, markerLayer;

const app = Vue.createApp({
  data() {
    return {
      artifacts: [],
      selectedId: null,
      selectedArtifact: null,
      showForm: false,
      editingId: null,
      page: 0,
      pageSize: 5000,
      filters: {
        search: '',
        materials: [],
        artifact_types: [],
        cultures: [],
        regions: [],
        period_start_min: null,
        period_start_max: null,
      },
      form: {
        name: '', catalog_number: '', quantity: '', region: '',
        site_name: '', longitude: null, latitude: null,
        period_label: '', period_start: null, period_end: null,
        culture: '', material: '', production_method: '',
        artifact_type: '', context_desc: '', location_desc: '',
        source_reference: '', image_url: '', notes: '',
      },
      materialOptions: ['红铜','黄铜','锡青铜','铅青铜','砷铜','砷青铜','青铜','铅锡青铜','白铜','冰铜','矿石（孔雀石）','炼渣'],
      typeOptions: ['工具','兵器','装饰品','礼器','炼渣','矿石','权杖头','镜','坩埚','铜渣','铜块','其他'],
      regionOptions: ['河西走廊','河湟地区','哈密盆地','黄河中下游地区','燕山地区','河套地区','长江流域','新疆中西部'],
      materialColors,
    };
  },

  computed: {
    totalCount() { return this.artifacts.length; },
    legendItems() {
      const seen = new Set();
      this.artifacts.forEach(a => { if (a.material) seen.add(a.material); });
      return [...seen].map(m => ({ label: m, color: materialColors[m] || defaultColor }));
    },
  },

  methods: {
    async fetchArtifacts() {
      const params = new URLSearchParams();
      params.append('limit', this.pageSize);
      params.append('offset', this.page * this.pageSize);
      if (this.filters.search) params.append('search', this.filters.search);
      if (this.filters.materials.length) params.append('materials', this.filters.materials.join(','));
      if (this.filters.artifact_types.length) params.append('artifact_types', this.filters.artifact_types.join(','));
      if (this.filters.cultures.length) params.append('cultures', this.filters.cultures.join(','));
      if (this.filters.regions.length) params.append('regions', this.filters.regions.join(','));
      if (this.filters.period_start_min != null) params.append('period_start_min', this.filters.period_start_min);
      if (this.filters.period_start_max != null) params.append('period_start_max', this.filters.period_start_max);

      const url = `${API_BASE}/artifacts/?${params.toString()}`;
      try {
        const res = await fetch(url);
        this.artifacts = await res.json();
        this.updateMarkers();
      } catch (e) {
        console.error('Fetch failed:', e);
      }
    },

    onFilter() { this.page = 0; this.fetchArtifacts(); },
    prevPage() { if (this.page > 0) { this.page--; this.fetchArtifacts(); } },
    nextPage() { this.page++; this.fetchArtifacts(); },

    selectArtifact(a) {
      this.selectedId = a.id;
      this.selectedArtifact = a;
      if (map && a.longitude != null) {
        const [gcjLng, gcjLat] = wgs84ToGcj02(a.longitude, a.latitude);
        map.flyTo([gcjLat, gcjLng], 8, { duration: 0.5 });
      }
    },

    editArtifact(a) {
      this.editingId = a.id;
      this.form = {
        name: a.name || '', catalog_number: a.catalog_number || '',
        quantity: a.quantity || '', region: a.region || '',
        site_name: a.site_name || '', longitude: a.longitude, latitude: a.latitude,
        period_label: a.period_label || '', period_start: a.period_start, period_end: a.period_end,
        culture: a.culture || '', material: a.material || '',
        production_method: a.production_method || '', artifact_type: a.artifact_type || '',
        context_desc: a.context_desc || '', location_desc: a.location_desc || '',
        source_reference: a.source_reference || '', image_url: a.image_url || '', notes: a.notes || '',
      };
      this.showForm = true;
      this.selectedArtifact = null;
    },

    resetForm() {
      this.form = {
        name: '', catalog_number: '', quantity: '', region: '',
        site_name: '', longitude: null, latitude: null,
        period_label: '', period_start: null, period_end: null,
        culture: '', material: '', production_method: '',
        artifact_type: '', context_desc: '', location_desc: '',
        source_reference: '', image_url: '', notes: '',
      };
    },

    async saveArtifact() {
      if (!this.form.name) { alert('请填写器物名称'); return; }
      const payload = { ...this.form };
      if (payload.period_start === '') payload.period_start = null;
      if (payload.period_end === '') payload.period_end = null;
      if (payload.longitude === '') payload.longitude = null;
      if (payload.latitude === '') payload.latitude = null;

      try {
        let url = `${API_BASE}/artifacts/`;
        let method = 'POST';
        if (this.editingId) { url += this.editingId; method = 'PUT'; }
        const res = await fetch(url, {
          method, headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          this.showForm = false; this.editingId = null; this.resetForm();
          await this.fetchArtifacts();
        } else {
          const err = await res.json();
          alert('保存失败: ' + JSON.stringify(err.detail || err));
        }
      } catch (e) { console.error('Save failed:', e); alert('保存失败，检查后端'); }
    },

    async deleteArtifact(a) {
      if (!confirm(`确认删除 "${a.name}"？`)) return;
      const res = await fetch(`${API_BASE}/artifacts/${a.id}`, { method: 'DELETE' });
      if (res.ok) { this.selectedArtifact = null; this.selectedId = null; await this.fetchArtifacts(); }
    },

    /* --- Map --- */
    initMap() {
      map = L.map('map', { center: [38.0, 104.0], zoom: 5, maxZoom: 18 });

      // 天地图地形晕渲底图 (通过后端代理)
      L.tileLayer(API_BASE + '/tiles/ter/{z}/{x}/{y}', {
        maxZoom: 18, attribution: '天地图',
      }).addTo(map);

      // 天地图地形注记叠加层
      L.tileLayer(API_BASE + '/tiles/cta/{z}/{x}/{y}', {
        maxZoom: 18,
      }).addTo(map);

      markerLayer = L.layerGroup().addTo(map);

      map.on('click', (e) => {
        if (this.showForm) {
          const [wgsLng, wgsLat] = gcj02ToWgs84(e.latlng.lng, e.latlng.lat);
          this.form.longitude = Math.round(wgsLng * 10000) / 10000;
          this.form.latitude = Math.round(wgsLat * 10000) / 10000;
        }
      });
    },

    updateMarkers() {
      markerLayer.clearLayers();
      this.artifacts.forEach((a) => {
        if (a.longitude == null || a.latitude == null) return;
        const color = materialColors[a.material] || defaultColor;
        const [gcjLng, gcjLat] = wgs84ToGcj02(a.longitude, a.latitude);
        const m = L.circleMarker([gcjLat, gcjLng], {
          radius: 6, fillColor: color, color: '#333', weight: 1, fillOpacity: 0.8,
        }).addTo(markerLayer);
        m.bindPopup(`<b>${a.name}</b><br/>遗址: ${a.site_name || '-'}<br/>文化: ${a.culture || '-'}<br/>材质: ${a.material || '-'}`);
        m.on('click', () => { this.selectedId = a.id; this.selectedArtifact = a; });
      });
    },
  },

  mounted() {
    this.initMap();
    this.fetchArtifacts();
  },
});

app.mount('#app');
