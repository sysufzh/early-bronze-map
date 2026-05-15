const API_BASE = '/api';
const PERIOD_COLORS = [
  '#e60049', '#0bb4ff', '#50e991', '#e6d800', '#9b19f5',
  '#ffa300', '#dc0ab4', '#b3d4ff', '#00bfa0', '#b30000',
  '#2cba00', '#636efa', '#ff6699', '#00cc96', '#ab63fa',
];
const PERIOD_COLOR_MAP = {};

function getPeriodColor(periodLabel) {
  if (!periodLabel) return '#999';
  if (!PERIOD_COLOR_MAP[periodLabel]) {
    const idx = Object.keys(PERIOD_COLOR_MAP).length % PERIOD_COLORS.length;
    PERIOD_COLOR_MAP[periodLabel] = PERIOD_COLORS[idx];
  }
  return PERIOD_COLOR_MAP[periodLabel];
}

const app = Vue.createApp({
  data() {
    return {
      sites: [],
      selectedId: null,
      selectedSite: null,
      totalCount: 0,

      filterSearch: '',
      filterRegion: '',
      filterPeriod: '',
      filterSiteType: '',
      filterPeriodStartMin: null,
      filterPeriodStartMax: null,
      filterOptions: { regions: [], period_labels: [], cultures: [], site_types: [] },

      debounceTimer: null,

      // Auth
      token: null,
      user: null,
      showLoginModal: false,
      showRegisterModal: false,
      authForm: { username: '', password: '', captcha_answer: null },
      captchaToken: '',
      captchaQuestion: '',

      // Site form
      showForm: false,
      editingId: null,
      form: {},
    };
  },

  computed: {
    isLoggedIn() { return !!this.token && !!this.user; },
    isAdmin() { return this.user && this.user.is_admin; },
    legendPeriods() {
      return Object.entries(PERIOD_COLOR_MAP).map(([label, color]) => ({ label, color }));
    },
  },

  methods: {
    // ── Auth ────────────────────────────────────
    authHeaders() {
      return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    },

    async refreshCaptcha() {
      try {
        const res = await fetch(`${API_BASE}/auth/captcha`);
        const data = await res.json();
        this.captchaToken = data.token;
        this.captchaQuestion = data.question;
      } catch (e) { console.error('Captcha fetch error:', e); }
    },

    async doLogin() {
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: this.authForm.username,
            password: this.authForm.password,
            captcha_token: this.captchaToken,
            captcha_answer: this.authForm.captcha_answer,
          }),
        });
        if (res.ok) {
          const data = await res.json();
          this.token = data.access_token;
          this.user = data.user;
          localStorage.setItem('bronze_token', this.token);
          localStorage.setItem('bronze_user', JSON.stringify(this.user));
          this.showLoginModal = false;
          this.authForm = { username: '', password: '', captcha_answer: null };
          this.fetchSites();
        } else {
          const err = await res.json();
          alert(JSON.stringify(err.detail || err));
        }
      } catch (e) { alert('登录失败: ' + e.message); }
    },

    async doRegister() {
      try {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: this.authForm.username,
            password: this.authForm.password,
            captcha_token: this.captchaToken,
            captcha_answer: this.authForm.captcha_answer,
          }),
        });
        if (res.ok) {
          alert('注册成功，请登录');
          this.showRegisterModal = false;
          this.showLoginModal = true;
          this.authForm = { username: '', password: '', captcha_answer: null };
          this.refreshCaptcha();
        } else {
          const err = await res.json();
          alert(JSON.stringify(err.detail || err));
        }
      } catch (e) { alert('注册失败: ' + e.message); }
    },

    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('bronze_token');
      localStorage.removeItem('bronze_user');
    },

    // ── Data ────────────────────────────────────
    async fetchSites() {
      const params = new URLSearchParams({ limit: '5000', offset: '0' });
      if (this.filterSearch) params.set('name', this.filterSearch);
      if (this.filterRegion) params.set('region', this.filterRegion);
      if (this.filterPeriod) params.set('period_label', this.filterPeriod);
      if (this.filterSiteType) params.set('site_type', this.filterSiteType);
      if (this.filterPeriodStartMin != null) params.set('period_start_min', this.filterPeriodStartMin);
      if (this.filterPeriodStartMax != null) params.set('period_start_max', this.filterPeriodStartMax);
      try {
        const res = await fetch(`${API_BASE}/prehistoric-sites/?${params}`);
        this.sites = await res.json();
        this.totalCount = this.sites.length;
        this.updateMarkers();
      } catch (e) { console.error('Fetch sites error:', e); }
    },

    debouncedFetch() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => this.fetchSites(), 300);
    },

    async fetchFilterOptions() {
      try {
        const res = await fetch(`${API_BASE}/prehistoric-sites/filters`);
        this.filterOptions = await res.json();
      } catch (e) { console.error('Fetch filters error:', e); }
    },

    // ── Map ────────────────────────────────────
    updateMarkers() {
      if (!window._siteLayer) return;
      window._siteLayer.clearLayers();
      const periodColorMap = {};

      for (const s of this.sites) {
        if (s.longitude == null || s.latitude == null) continue;
        const color = getPeriodColor(s.period_label);
        const marker = L.circleMarker([s.latitude, s.longitude], {
          radius: 8,
          fillColor: color,
          color: '#fff',
          weight: 2,
          fillOpacity: 0.85,
        });
        marker.bindPopup(
          `<b>${s.name}</b><br/>${s.region || '-'} · ${s.site_name || '-'}<br/>${s.period_label || '-'}`
        );
        marker.on('click', () => { this.selectSite(s); });
        marker.addTo(window._siteLayer);
      }
    },

    selectSite(s) {
      if (!this.isLoggedIn) {
        this.refreshCaptcha();
        this.showLoginModal = true;
        return;
      }
      this.selectedId = s.id;
      this.selectedSite = s;
    },

    // ── CRUD (Admin) ─────────────────────────────
    openNewSiteForm() {
      this.editingId = null;
      this.form = {
        name: '', catalog_number: '', region: '', site_name: '',
        longitude: null, latitude: null, period_label: '', period_start: null, period_end: null,
        culture: '', site_type: '', area_desc: '', description: '',
        excavation_history: '', key_findings: '', preservation_status: '',
        source_reference: '', notes: '',
      };
      this.showForm = true;
    },

    editSite(s) {
      this.editingId = s.id;
      this.form = { ...s };
      this.showForm = true;
      this.selectedSite = null;
    },

    async saveSite() {
      if (!this.form.name) { alert('请填写遗址名称'); return; }
      if (this.form.period_start === '') this.form.period_start = null;
      if (this.form.period_end === '') this.form.period_end = null;
      if (this.form.longitude === '') this.form.longitude = null;
      if (this.form.latitude === '') this.form.latitude = null;

      try {
        let url = `${API_BASE}/prehistoric-sites/`;
        let method = 'POST';
        if (this.editingId) { url += this.editingId; method = 'PUT'; }
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
          body: JSON.stringify(this.form),
        });
        if (res.ok) {
          this.showForm = false;
          this.editingId = null;
          await this.fetchSites();
          await this.fetchFilterOptions();
        } else {
          const errText = await res.text();
          let errDetail;
          try { errDetail = JSON.parse(errText); } catch { errDetail = errText; }
          alert('保存失败: ' + (typeof errDetail === 'object' ? JSON.stringify(errDetail) : errDetail));
        }
      } catch (e) { alert('保存失败: ' + e.message); }
    },

    async deleteSite(id) {
      if (!confirm('确定删除该遗址？此操作不可恢复。')) return;
      try {
        const res = await fetch(`${API_BASE}/prehistoric-sites/${id}`, { method: 'DELETE', headers: this.authHeaders() });
        if (res.ok) {
          this.selectedSite = null;
          this.selectedId = null;
          await this.fetchSites();
          await this.fetchFilterOptions();
        } else {
          const errText = await res.text();
          let errDetail;
          try { errDetail = JSON.parse(errText); } catch { errDetail = errText; }
          alert('删除失败: ' + (typeof errDetail === 'object' ? JSON.stringify(errDetail) : errDetail));
        }
      } catch (e) { alert('删除失败: ' + e.message); }
    },
  },

  mounted() {
    // Restore auth
    this.token = localStorage.getItem('bronze_token');
    const userStr = localStorage.getItem('bronze_user');
    if (userStr) { try { this.user = JSON.parse(userStr); } catch {} }

    // Init map
    const m = L.map('map', { center: [35, 105], zoom: 5, zoomControl: true });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(m);
    window._map = m;
    window._siteLayer = L.layerGroup().addTo(m);

    this.fetchSites();
    this.fetchFilterOptions();
  },
});

app.mount('#app');
