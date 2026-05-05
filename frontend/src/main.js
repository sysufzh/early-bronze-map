const API_BASE = '/api';

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
      lightboxImg: null,
      showForm: false,
      editingId: null,
      editImages: [],
      uploadFile: null,
      pdfFile: null,
      newImageCaption: '',
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
      // Auth state
      user: null,
      token: null,
      showLoginModal: false,
      showRegisterModal: false,
      authForm: {
        username: '',
        password: '',
      },
      // Review panel
      showReviewPanel: false,
      pendingEdits: [],
      reviewNotes: {},
      reviewFilter: 'pending',
      fieldApprovals: {},  // { editId: { field: true/false } }
      // My submissions
      showMyEdits: false,
      myEdits: [],
      myFilter: '',
    };
  },

  computed: {
    totalCount() { return this.artifacts.length; },
    isLoggedIn() { return this.user !== null && this.token !== null; },
    isAdmin() { return this.user !== null && this.user.is_admin === true; },
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
      if (!this.isLoggedIn) {
        this.showLoginModal = true;
        return;
      }
      this.selectedId = a.id;
      this.selectedArtifact = a;
      if (map && a.longitude != null) {
        map.flyTo([a.latitude, a.longitude], 8, { duration: 0.5 });
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
        source_reference: a.source_reference || '', source_pdf: a.source_pdf || '',
        image_url: a.image_url || '', notes: a.notes || '',
      };
      this.editImages = (a.images || []).slice();
      this.uploadFile = null;
      this.pdfFile = null;
      this.newImageCaption = '';
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
        source_reference: '', source_pdf: '', image_url: '', notes: '',
      };
      this.editImages = [];
      this.uploadFile = null;
      this.pdfFile = null;
      this.newImageCaption = '';
    },

    async saveArtifact() {
      if (!this.form.name) { alert('请填写器物名称'); return; }
      const payload = { ...this.form };
      if (payload.period_start === '') payload.period_start = null;
      if (payload.period_end === '') payload.period_end = null;
      if (payload.longitude === '') payload.longitude = null;
      if (payload.latitude === '') payload.latitude = null;

      // Non-admin users submit for approval
      if (!this.isAdmin) {
        delete payload.source_pdf;  // PDF upload requires admin, don't include in pending edit
        const actionType = this.editingId ? 'update' : 'create';
        try {
          const res = await fetch(`${API_BASE}/pending-edits/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
            body: JSON.stringify({
              artifact_id: this.editingId || null,
              action_type: actionType,
              payload: payload,
            }),
          });
          if (res.ok) {
            this.showForm = false; this.editingId = null; this.resetForm();
            alert('已提交审核，等待管理员通过');
          } else {
            const err = await res.json();
            alert('提交失败: ' + JSON.stringify(err.detail || err));
          }
        } catch (e) { console.error('Submit failed:', e); alert('提交失败，检查后端'); }
        return;
      }

      // Admin direct save
      try {
        let url = `${API_BASE}/artifacts/`;
        let method = 'POST';
        if (this.editingId) { url += this.editingId; method = 'PUT'; }
        const res = await fetch(url, {
          method, headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
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
      const res = await fetch(`${API_BASE}/artifacts/${a.id}`, { method: 'DELETE', headers: this.authHeaders() });
      if (res.ok) { this.selectedArtifact = null; this.selectedId = null; await this.fetchArtifacts(); }
    },

    /* --- Images --- */
    imageUrl(filename) {
      return `/static/images/artifacts/${filename}`;
    },
    pdfUrl(filename) {
      return `/static/pdfs/${filename}`;
    },

    viewImage(img) {
      this.lightboxImg = img;
    },

    onFileSelected(e) {
      this.uploadFile = e.target.files[0] || null;
    },

    async uploadSelectedFile() {
      if (!this.uploadFile || !this.editingId) return;
      const formData = new FormData();
      formData.append('file', this.uploadFile);
      if (this.newImageCaption) formData.append('caption', this.newImageCaption);
      formData.append('sort_order', this.editImages.length);
      try {
        const res = await fetch(`${API_BASE}/artifacts/${this.editingId}/images/upload`, {
          method: 'POST', body: formData, headers: this.authHeaders(),
        });
        if (res.ok) {
          const img = await res.json();
          this.editImages.push(img);
          this.uploadFile = null;
          this.newImageCaption = '';
          // Reset file input
          if (this.$refs.fileInput) this.$refs.fileInput.value = '';
        } else {
          const err = await res.json();
          alert('上传失败: ' + JSON.stringify(err.detail || err));
        }
      } catch (e) { console.error('Upload failed:', e); alert('上传失败'); }
    },

    async removeImage(imgId) {
      if (!confirm('确认删除此图片？')) return;
      const res = await fetch(`${API_BASE}/artifacts/${this.editingId}/images/${imgId}`, { method: 'DELETE', headers: this.authHeaders() });
      if (res.ok) {
        this.editImages = this.editImages.filter(i => i.id !== imgId);
      }
    },

    /* --- PDF upload --- */
    onPdfSelected(e) {
      this.pdfFile = e.target.files[0] || null;
    },

    async uploadPdf() {
      if (!this.pdfFile || !this.editingId) return;
      const formData = new FormData();
      formData.append('file', this.pdfFile);
      const res = await fetch(`${API_BASE}/artifacts/${this.editingId}/pdf`, {
        method: 'POST', body: formData, headers: this.authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        this.form.source_pdf = data.filename;
        this.pdfFile = null;
        if (this.$refs.pdfInput) this.$refs.pdfInput.value = '';
      } else {
        const err = await res.json();
        alert('PDF上传失败: ' + JSON.stringify(err.detail || err));
      }
    },

    async deletePdf() {
      if (!confirm('确认删除此PDF？')) return;
      const res = await fetch(`${API_BASE}/artifacts/${this.editingId}/pdf`, {
        method: 'DELETE', headers: this.authHeaders(),
      });
      if (res.ok) {
        this.form.source_pdf = '';
      }
    },

    /* --- Auth --- */
    loadTokenFromStorage() {
      const savedToken = localStorage.getItem('bronze_token');
      const savedUser = localStorage.getItem('bronze_user');
      if (savedToken && savedUser) {
        try {
          this.token = savedToken;
          this.user = JSON.parse(savedUser);
          this.checkAuth();
        } catch (e) {
          this.clearAuth();
        }
      }
    },

    async checkAuth() {
      if (!this.token) return;
      try {
        const res = await fetch(`${API_BASE}/auth/me`, {
          headers: { 'Authorization': `Bearer ${this.token}` },
        });
        if (res.ok) {
          this.user = await res.json();
          localStorage.setItem('bronze_user', JSON.stringify(this.user));
        } else {
          this.clearAuth();
        }
      } catch {
        // Network error - keep current state
      }
    },

    clearAuth() {
      this.token = null;
      this.user = null;
      localStorage.removeItem('bronze_token');
      localStorage.removeItem('bronze_user');
    },

    async doLogin() {
      if (!this.authForm.username || !this.authForm.password) {
        alert('请填写用户名和密码');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.authForm),
        });
        if (res.ok) {
          const data = await res.json();
          this.token = data.access_token;
          this.user = data.user;
          localStorage.setItem('bronze_token', this.token);
          localStorage.setItem('bronze_user', JSON.stringify(this.user));
          this.showLoginModal = false;
          this.authForm = { username: '', password: '' };
        } else {
          const err = await res.json();
          alert('登录失败: ' + (err.detail || '用户名或密码错误'));
        }
      } catch (e) {
        console.error('Login failed:', e);
        alert('登录失败，请检查网络');
      }
    },

    async doRegister() {
      if (!this.authForm.username || !this.authForm.password) {
        alert('请填写用户名和密码');
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.authForm),
        });
        if (res.ok) {
          alert('注册成功，请登录');
          this.showRegisterModal = false;
          this.authForm = { username: '', password: '' };
        } else {
          const err = await res.json();
          alert('注册失败: ' + (err.detail || '未知错误'));
        }
      } catch (e) {
        console.error('Register failed:', e);
        alert('注册失败，请检查网络');
      }
    },

    doLogout() {
      this.clearAuth();
      this.showForm = false;
      this.selectedArtifact = null;
    },

    authHeaders() {
      return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
    },

    /* --- Map --- */
    initMap() {
      map = L.map('map', { center: [38.0, 104.0], zoom: 5, maxZoom: 18 });

      // MapTiler Outdoor 地形晕渲底图（路网标注极简）
      L.tileLayer('https://api.maptiler.com/maps/outdoor-v2/{z}/{x}/{y}.png?key=fkAIsCTcnsFbs00BrHlT', {
        maxZoom: 18,
        attribution: '&copy; <a href="https://www.maptiler.com/copyright/">MapTiler</a> | <a href="https://openstreetmap.org/copyright">OSM</a>',
      }).addTo(map);

      markerLayer = L.layerGroup().addTo(map);

      map.on('click', (e) => {
        if (this.showForm) {
          this.form.longitude = Math.round(e.latlng.lng * 10000) / 10000;
          this.form.latitude = Math.round(e.latlng.lat * 10000) / 10000;
        }
      });
    },

    updateMarkers() {
      markerLayer.clearLayers();

      // Group artifacts by coordinate for popup listing & jitter
      const coordMap = new Map(); // key: "lon,lat" -> artifacts[]
      this.artifacts.forEach((a) => {
        if (a.longitude == null || a.latitude == null) return;
        const key = `${a.longitude.toFixed(4)},${a.latitude.toFixed(4)}`;
        if (!coordMap.has(key)) coordMap.set(key, []);
        coordMap.get(key).push(a);
      });

      // Track how many markers we've placed at each WGS84 coordinate for jitter
      const coordCount = new Map();

      this.artifacts.forEach((a) => {
        if (a.longitude == null || a.latitude == null) return;
        const color = materialColors[a.material] || defaultColor;
        // Add small random jitter for markers at the same location
        const key = `${a.longitude.toFixed(4)},${a.latitude.toFixed(4)}`;
        const count = coordCount.get(key) || 0;
        coordCount.set(key, count + 1);
        const jitterLng = count > 0 ? (Math.random() - 0.5) * 0.002 : 0;
        const jitterLat = count > 0 ? (Math.random() - 0.5) * 0.002 : 0;

        const m = L.circleMarker([a.latitude + jitterLat, a.longitude + jitterLng], {
          radius: 6, fillColor: color, color: '#333', weight: 1, fillOpacity: 0.8,
        }).addTo(markerLayer);

        // Popup lists all artifacts at this coordinate
        const sameSite = coordMap.get(key) || [a];
        const listItems = sameSite.slice(0, 20).map(x => `&bull; ${x.name} <small>[${x.material||'?'}]</small>`).join('<br/>');
        const more = sameSite.length > 20 ? `<br/><small>...还有 ${sameSite.length - 20} 件</small>` : '';
        m.bindPopup(`<b>${a.site_name || '-'}</b>（共${sameSite.length}件）<br/>${listItems}${more}`);

        m.on('click', () => { this.selectArtifact(a); });
      });
    },

    /* --- Review Panel (admin) --- */
    async fetchPendingEdits() {
      try {
        const params = new URLSearchParams();
        if (this.reviewFilter) params.append('status', this.reviewFilter);
        const res = await fetch(`${API_BASE}/pending-edits/?${params.toString()}`, {
          headers: this.authHeaders(),
        });
        if (res.ok) {
          this.pendingEdits = await res.json();
          // Init field approvals for all pending update edits
          this.pendingEdits.forEach(pe => {
            if (pe.status === 'pending' && pe.action_type === 'update') {
              this.initFieldApprovals(pe);
            }
          });
        }
      } catch (e) { console.error('Fetch pending edits failed:', e); }
    },

    initFieldApprovals(pe) {
      if (!this.fieldApprovals[pe.id]) {
        this.fieldApprovals[pe.id] = {};
      }
      const diffs = this.getDiffFields(pe);
      diffs.forEach(d => {
        // Default: all fields accepted
        if (!(d.field in this.fieldApprovals[pe.id])) {
          this.fieldApprovals[pe.id][d.field] = true;
        }
      });
    },

    isFieldApproved(editId, field) {
      return this.fieldApprovals[editId]?.[field] !== false;
    },

    toggleFieldApproval(editId, field) {
      if (!this.fieldApprovals[editId]) {
        this.fieldApprovals[editId] = {};
      }
      this.fieldApprovals[editId][field] = !this.isFieldApproved(editId, field);
    },

    async approveEdit(editId) {
      const pe = this.pendingEdits.find(e => e.id === editId);
      if (!pe) return;

      let approvedFields;
      if (pe.action_type === 'update') {
        // Collect fields that are approved (toggle = true)
        const diffs = this.getDiffFields(pe);
        approvedFields = diffs.filter(d => this.isFieldApproved(editId, d.field)).map(d => d.field);
        // Also include non-diff fields that exist in payload
        for (const key of Object.keys(pe.payload)) {
          if (!approvedFields.includes(key) && key !== 'longitude' && key !== 'latitude' && key !== 'source_pdf') {
            // If field wasn't in diff (unchanged), auto-accept it
            if (!diffs.some(d => d.field === key)) {
              approvedFields.push(key);
            }
          }
        }
      } else {
        // For "create", accept all fields
        approvedFields = Object.keys(pe.payload).filter(k => k !== 'source_pdf');
      }

      try {
        const res = await fetch(`${API_BASE}/pending-edits/${editId}/approve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
          body: JSON.stringify({ approved_fields: approvedFields }),
        });
        if (res.ok) {
          delete this.fieldApprovals[editId];
          await this.fetchPendingEdits();
          await this.fetchArtifacts();
        } else {
          const err = await res.json();
          alert('审核失败: ' + JSON.stringify(err.detail || err));
        }
      } catch (e) { console.error('Approve failed:', e); }
    },

    async rejectEdit(editId) {
      const notes = this.reviewNotes[editId] || '';
      try {
        const res = await fetch(`${API_BASE}/pending-edits/${editId}/reject`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
          body: JSON.stringify({ notes: notes }),
        });
        if (res.ok) {
          this.reviewNotes[editId] = '';
          await this.fetchPendingEdits();
        } else {
          const err = await res.json();
          alert('驳回失败: ' + JSON.stringify(err.detail || err));
        }
      } catch (e) { console.error('Reject failed:', e); }
    },

    statusLabel(status) {
      const map = { pending: '待审核', approved: '已通过', rejected: '已驳回' };
      return map[status] || status;
    },

    /* --- My Submissions (registered user) --- */
    async fetchMyEdits() {
      try {
        const params = new URLSearchParams();
        if (this.myFilter) params.append('status', this.myFilter);
        const url = `${API_BASE}/pending-edits/mine?${params.toString()}`;
        const res = await fetch(url, { headers: this.authHeaders() });
        if (res.ok) {
          this.myEdits = await res.json();
        }
      } catch (e) { console.error('Fetch my edits failed:', e); }
    },

    formatTime(ts) {
      if (!ts) return '-';
      return new Date(ts).toLocaleString('zh-CN');
    },

    getDiffFields(pe) {
      const oldData = pe.artifact_data || {};
      const newData = pe.payload || {};
      const fieldLabels = {
        name: '器物名称', catalog_number: '器物号', quantity: '数量',
        region: '区域', site_name: '遗址名称',
        period_label: '时代标签', period_start: '起始年代', period_end: '结束年代',
        culture: '考古学文化', material: '材质',
        production_method: '制作方式', artifact_type: '器型',
        context_desc: '出土情境', location_desc: '出土地点',
        source_reference: '资料出处', notes: '备注',
        longitude: '经度', latitude: '纬度',
      };
      const diffs = [];
      for (const [field, label] of Object.entries(fieldLabels)) {
        const oldVal = oldData[field] != null ? String(oldData[field]) : '';
        const newVal = newData[field] != null ? String(newData[field]) : '';
        if (oldVal !== newVal) {
          diffs.push({ field, label, old: oldVal, new: newVal });
        }
      }
      return diffs;
    },
  },

  mounted() {
    this.loadTokenFromStorage();
    this.initMap();
    this.fetchArtifacts();
  },
});

app.mount('#app');
