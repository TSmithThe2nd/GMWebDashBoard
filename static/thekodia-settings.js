/**
 * Thekodia Settings Modal
 * Loaded on every DM page. Injects the gear button into the nav and the settings
 * modal into the body. Handles all settings reads/writes and campaign management.
 */
const ThekodiaSettings = (() => {
  const BASE = 'http://localhost:5000';
  const LS_KEY = 'thekodia_settings';

  const DEFAULT_SETTINGS = {
    worldName: 'Thekodia',
    clockRatio: 5,
    calendar: {
      preset: 'thekodia',
      eraName: 'CE',
      months: ['Wahuary','Dosuary','Tresuary','Nneuary','Wuuary','Situary',
               'Sietuary','Octuary','Tisauary','Shiuary','Hdashuary','Docuary'],
      daysPerMonth: 28,
      weekDays: ['Wahday','Dosday','Tresday','Nneday','Wuday','Sitday','Sietday'],
    },
    moons: [
      { name: 'Nox',    cycle: 14, color: '#a0c8e8' },
      { name: 'Tharis', cycle: 24, color: '#c8a96e' },
      { name: 'Cerath', cycle: 36, color: '#9b72cf' },
    ],
    playerDisplay: {
      showHpBars: true,
      showConditions: true,
      maskEnemies: false,
    },
  };

  const CALENDAR_PRESETS = {
    thekodia: {
      label: 'Thekodia (Custom)',
      eraName: 'CE',
      months: ['Wahuary','Dosuary','Tresuary','Nneuary','Wuuary','Situary',
               'Sietuary','Octuary','Tisauary','Shiuary','Hdashuary','Docuary'],
      daysPerMonth: 28,
      weekDays: ['Wahday','Dosday','Tresday','Nneday','Wuday','Sitday','Sietday'],
    },
    faerun: {
      label: 'Faerûn (Forgotten Realms)',
      eraName: 'DR',
      months: ['Hammer','Alturiak','Ches','Tarsakh','Mirtul','Kythorn',
               'Flamerule','Eleasis','Eleint','Marpenoth','Uktar','Nightal'],
      daysPerMonth: 30,
      weekDays: ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th'],
    },
    greyhawk: {
      label: 'Oerth (Greyhawk)',
      eraName: 'CY',
      months: ['Fireseek','Readying','Coldeven','Planting','Flocktime','Wealsun',
               'Reaping','Goodmonth','Harvester','Patchwall',"Ready'reat",'Sunsebb'],
      daysPerMonth: 28,
      weekDays: ['Starday','Sunday','Moonday','Godsday','Waterday','Earthday','Freeday'],
    },
    eberron: {
      label: 'Eberron',
      eraName: 'YK',
      months: ['Zarantyr','Olarune','Therendor','Eyre','Dravago','Nymm',
               'Lharvion','Barrakas','Rhaan','Sypheros','Aryth','Vult'],
      daysPerMonth: 28,
      weekDays: ['Sul','Mol','Zol','Wir','Zor','Far','Sar'],
    },
    custom: {
      label: 'Custom',
      eraName: null, months: null, daysPerMonth: null, weekDays: null,
    },
  };

  let settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));

  // ── Utilities ─────────────────────────────────────────────

  function mergeDeep(target, source) {
    for (const key of Object.keys(source || {})) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        if (!target[key] || typeof target[key] !== 'object') target[key] = {};
        mergeDeep(target[key], source[key]);
      } else {
        target[key] = source[key];
      }
    }
    return target;
  }

  function loadFromStorage() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) settings = mergeDeep(JSON.parse(JSON.stringify(DEFAULT_SETTINGS)), JSON.parse(raw));
    } catch {}
  }

  function applyWorldName() {
    const el = document.getElementById('appTitle');
    if (el) el.textContent = `⚔ ${settings.worldName || 'Thekodia'} DM`;
  }

  // ── Init ──────────────────────────────────────────────────

  function init() {
    loadFromStorage();
    applyWorldName();
    injectModal();
    injectGearButton();
    ensureBackupInput();
  }

  function injectGearButton() {
    const nav = document.querySelector('.nav-tabs');
    if (!nav) return;
    const btn = document.createElement('button');
    btn.className = 'nav-tab';
    btn.title = 'Settings';
    btn.textContent = '⚙ Settings';
    btn.onclick = () => open('campaign');
    const quitBtn = Array.from(nav.querySelectorAll('button')).find(b => b.textContent.includes('Quit'));
    if (quitBtn) nav.insertBefore(btn, quitBtn);
    else nav.appendChild(btn);
  }

  function ensureBackupInput() {
    if (document.getElementById('backupFileInput')) return;
    const input = document.createElement('input');
    input.type = 'file';
    input.id = 'backupFileInput';
    input.accept = '.json';
    input.style.display = 'none';
    input.onchange = (e) => {
      if (e.target.files[0] && typeof ThekodiaStorage !== 'undefined') {
        ThekodiaStorage.importBackup(e.target.files[0]);
      }
      e.target.value = '';
    };
    document.body.appendChild(input);
  }

  function injectModal() {
    const presetOptions = Object.entries(CALENDAR_PRESETS)
      .map(([k, p]) => `<option value="${k}">${p.label}</option>`)
      .join('');

    const html = `
<div class="modal-overlay" id="settingsOverlay" style="display:none;align-items:center;justify-content:center"
     onclick="if(event.target===this)ThekodiaSettings.close()">
  <div class="modal" style="max-width:720px;width:96%;max-height:90vh;display:flex;flex-direction:column">

    <div class="modal-head">
      <span style="font-family:'Cinzel',serif;letter-spacing:.08em">⚙ Settings</span>
      <button class="btn small" style="padding:2px 8px;font-size:16px;line-height:1" onclick="ThekodiaSettings.close()">✕</button>
    </div>

    <div style="display:flex;gap:0;padding:0 16px;border-bottom:1px solid var(--border);background:var(--bg2);flex-shrink:0">
      <button class="settings-tab active" id="stab-btn-campaign" onclick="ThekodiaSettings.showTab('campaign')">Campaign</button>
      <button class="settings-tab" id="stab-btn-world"    onclick="ThekodiaSettings.showTab('world')">World</button>
      <button class="settings-tab" id="stab-btn-clock"    onclick="ThekodiaSettings.showTab('clock')">Calendar</button>
      <button class="settings-tab" id="stab-btn-moons"    onclick="ThekodiaSettings.showTab('moons')">Moons</button>
      <button class="settings-tab" id="stab-btn-display"  onclick="ThekodiaSettings.showTab('display')">Player Display</button>
    </div>

    <div class="modal-body" style="flex:1;overflow-y:auto;padding:20px">

      <!-- ── Campaign Tab ─────────────────────────────────── -->
      <div id="stab-campaign">
        <div style="margin-bottom:16px">
          <div class="settings-label">Active Campaign</div>
          <div id="settingsActiveCampaign" style="font-family:'Cinzel',serif;font-size:17px;color:var(--accent)">—</div>
        </div>
        <div class="settings-label" style="margin-bottom:8px">All Campaigns</div>
        <div id="settingsCampaignList" style="display:flex;flex-direction:column;gap:6px;margin-bottom:16px">
          <div style="color:var(--text3);font-size:13px">Loading…</div>
        </div>
        <div style="display:flex;gap:8px;align-items:center">
          <input class="field" id="settingsNewCampaignName" placeholder="New campaign name…"
            style="flex:1;height:32px"
            onkeydown="if(event.key==='Enter')ThekodiaSettings.createCampaign()">
          <button class="btn primary small" onclick="ThekodiaSettings.createCampaign()">+ Create</button>
        </div>
        <div id="settingsCampaignMsg" style="font-size:12px;color:var(--red);margin-top:6px;min-height:16px"></div>
      </div>

      <!-- ── World Tab ────────────────────────────────────── -->
      <div id="stab-world" style="display:none">
        <div>
          <label class="settings-label" for="settingsWorldName">World / Setting Name</label>
          <p style="font-size:12px;color:var(--text3);margin-bottom:10px">Shown in the header on every DM page.</p>
          <input class="field" id="settingsWorldName" style="width:100%;max-width:360px" placeholder="Thekodia">
        </div>
      </div>

      <!-- ── Calendar Tab ─────────────────────────────────── -->
      <div id="stab-clock" style="display:none">

        <div style="margin-bottom:22px">
          <label class="settings-label">Real-Time Ratio</label>
          <p style="font-size:12px;color:var(--text3);margin-bottom:10px">In-world minutes per real minute when auto-tick is on.</p>
          <div style="display:flex;align-items:center;gap:12px">
            <input type="range" id="settingsRatioRange" min="1" max="60" step="1"
              style="flex:1;accent-color:var(--accent)"
              oninput="document.getElementById('settingsRatioVal').textContent=this.value">
            <span style="font-family:'Cinzel',serif;color:var(--accent);min-width:26px;text-align:center;font-size:18px" id="settingsRatioVal">5</span>
            <span style="font-size:12px;color:var(--text3)">min / real min</span>
          </div>
        </div>

        <div style="margin-bottom:18px;display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end">
          <div>
            <label class="settings-label" for="settingsCalPreset">Calendar Preset</label>
            <select class="field" id="settingsCalPreset" style="width:260px"
              onchange="ThekodiaSettings.applyCalPreset()">${presetOptions}</select>
          </div>
          <div>
            <label class="settings-label" for="settingsEraName">Era Name</label>
            <input class="field" id="settingsEraName" style="width:80px" placeholder="CE"
              oninput="document.getElementById('settingsCalPreset').value='custom'">
          </div>
        </div>

        <div style="margin-bottom:18px;display:flex;gap:16px;align-items:flex-end;flex-wrap:wrap">
          <div>
            <label class="settings-label" for="settingsMonthCount">Months Per Year</label>
            <input type="number" class="field" id="settingsMonthCount" min="1" max="24" style="width:72px;height:30px;text-align:center"
              oninput="ThekodiaSettings.updateMonthCount();document.getElementById('settingsCalPreset').value='custom'">
          </div>
          <div>
            <label class="settings-label" for="settingsDaysPerMonth">Days Per Month</label>
            <input type="number" class="field" id="settingsDaysPerMonth" min="1" max="999" style="width:72px;height:30px;text-align:center"
              oninput="document.getElementById('settingsCalPreset').value='custom'">
          </div>
        </div>

        <div style="margin-bottom:24px">
          <label class="settings-label">Month Names</label>
          <div id="settingsMonthGrid" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px"></div>
        </div>

        <div style="margin-bottom:16px">
          <label class="settings-label" for="settingsWeekCount">Days Per Week</label>
          <input type="number" class="field" id="settingsWeekCount" min="1" max="20" style="width:72px;height:30px;text-align:center"
            oninput="ThekodiaSettings.updateWeekCount();document.getElementById('settingsCalPreset').value='custom'">
        </div>

        <div>
          <label class="settings-label">Weekday Names</label>
          <div id="settingsWeekGrid" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px"></div>
        </div>

      </div>

      <!-- ── Moons Tab ─────────────────────────────────────── -->
      <div id="stab-moons" style="display:none">
        <p style="font-size:12px;color:var(--text2);margin-bottom:16px">
          Configure the moons visible in your world. Changes take effect after saving and reloading the Clock page.
        </p>
        <div id="settingsMoonList" style="display:flex;flex-direction:column;gap:10px;margin-bottom:16px"></div>
        <button class="btn small" onclick="ThekodiaSettings.addMoon()" style="border-color:var(--accent-dim);color:var(--accent)">+ Add Moon</button>
      </div>

      <!-- ── Player Display Tab ───────────────────────────── -->
      <div id="stab-display" style="display:none">
        <p style="font-size:12px;color:var(--text2);margin-bottom:16px">
          Controls what players see on the
          <a href="/thekodia-player-display.html" target="_blank" style="color:var(--accent)">Player Display</a> screen.
        </p>
        <div class="settings-toggle-row">
          <div>
            <div style="font-size:14px;font-weight:600;color:var(--text)">Show HP Bars</div>
            <div style="font-size:12px;color:var(--text3)">Display the HP bar for the current player character</div>
          </div>
          <label class="toggle-switch"><input type="checkbox" id="dispShowHp"><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-toggle-row">
          <div>
            <div style="font-size:14px;font-weight:600;color:var(--text)">Show Conditions</div>
            <div style="font-size:12px;color:var(--text3)">Display status condition pills on the current combatant</div>
          </div>
          <label class="toggle-switch"><input type="checkbox" id="dispShowConditions"><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-toggle-row">
          <div>
            <div style="font-size:14px;font-weight:600;color:var(--text)">Mask Enemy Names</div>
            <div style="font-size:12px;color:var(--text3)">Show "???" instead of monster names on the player display</div>
          </div>
          <label class="toggle-switch"><input type="checkbox" id="dispMaskEnemies"><span class="toggle-slider"></span></label>
        </div>
      </div>

    </div><!-- /modal-body -->

    <div class="modal-foot" style="justify-content:space-between">
      <button class="btn" onclick="ThekodiaSettings.close()">Cancel</button>
      <button class="btn primary" onclick="ThekodiaSettings.save()">Save Changes</button>
    </div>
  </div>
</div>`;

    const wrapper = document.createElement('div');
    wrapper.innerHTML = html;
    document.body.appendChild(wrapper.firstElementChild);
  }

  // ── Tab Switching ─────────────────────────────────────────

  function showTab(name) {
    ['campaign','world','clock','moons','display'].forEach(t => {
      const content = document.getElementById(`stab-${t}`);
      const btn = document.getElementById(`stab-btn-${t}`);
      if (content) content.style.display = t === name ? '' : 'none';
      if (btn) btn.classList.toggle('active', t === name);
    });
    if (name === 'campaign') loadCampaigns();
  }

  // ── Open / Close ──────────────────────────────────────────

  function open(tab) {
    const overlay = document.getElementById('settingsOverlay');
    if (!overlay) return;
    overlay.style.display = 'flex';

    // World
    const wn = document.getElementById('settingsWorldName');
    if (wn) wn.value = settings.worldName || 'Thekodia';

    // Clock ratio
    const ratio = document.getElementById('settingsRatioRange');
    const ratioVal = document.getElementById('settingsRatioVal');
    const v = settings.clockRatio || 5;
    if (ratio) ratio.value = v;
    if (ratioVal) ratioVal.textContent = v;

    // Calendar
    const cal = settings.calendar || {};
    const calPreset = document.getElementById('settingsCalPreset');
    if (calPreset) calPreset.value = cal.preset || 'thekodia';

    const eraIn = document.getElementById('settingsEraName');
    if (eraIn) eraIn.value = cal.eraName || 'CE';

    const months = cal.months || DEFAULT_SETTINGS.calendar.months;
    const monthCount = document.getElementById('settingsMonthCount');
    if (monthCount) monthCount.value = months.length;
    buildMonthInputs(months);

    const dpM = document.getElementById('settingsDaysPerMonth');
    if (dpM) dpM.value = cal.daysPerMonth || 28;

    const weekDays = cal.weekDays || DEFAULT_SETTINGS.calendar.weekDays;
    const weekCount = document.getElementById('settingsWeekCount');
    if (weekCount) weekCount.value = weekDays.length;
    buildWeekdayInputs(weekDays);

    // Moons
    renderMoonList(settings.moons || DEFAULT_SETTINGS.moons);

    // Player display
    const pd = settings.playerDisplay || {};
    const showHp = document.getElementById('dispShowHp');
    const showCond = document.getElementById('dispShowConditions');
    const maskEnem = document.getElementById('dispMaskEnemies');
    if (showHp)   showHp.checked   = pd.showHpBars    !== false;
    if (showCond) showCond.checked = pd.showConditions !== false;
    if (maskEnem) maskEnem.checked = !!pd.maskEnemies;

    showTab(tab || 'campaign');
  }

  function close() {
    const overlay = document.getElementById('settingsOverlay');
    if (overlay) overlay.style.display = 'none';
  }

  // ── Calendar / Month Helpers ──────────────────────────────

  function buildMonthInputs(months) {
    const grid = document.getElementById('settingsMonthGrid');
    if (!grid) return;
    grid.innerHTML = months.map((m, i) => `
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-size:11px;color:var(--text3);min-width:22px;text-align:right;font-family:'Cinzel',serif">${i + 1}.</span>
        <input class="field" style="flex:1;height:28px;font-size:12px"
          id="settingsMonth${i}" value="${m.replace(/"/g, '&quot;')}" placeholder="Month ${i + 1}"
          oninput="document.getElementById('settingsCalPreset').value='custom'">
      </div>`).join('');
  }

  function updateMonthCount() {
    const n = parseInt(document.getElementById('settingsMonthCount')?.value) || 12;
    const clamped = Math.max(1, Math.min(24, n));
    const current = Array.from({ length: 12 }, (_, i) =>
      document.getElementById(`settingsMonth${i}`)?.value || DEFAULT_SETTINGS.calendar.months[i] || `Month ${i + 1}`
    );
    const months = Array.from({ length: clamped }, (_, i) =>
      current[i] !== undefined ? current[i] : `Month ${i + 1}`
    );
    buildMonthInputs(months);
  }

  function buildWeekdayInputs(weekDays) {
    const grid = document.getElementById('settingsWeekGrid');
    if (!grid) return;
    grid.innerHTML = weekDays.map((d, i) => `
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-size:11px;color:var(--text3);min-width:22px;text-align:right;font-family:'Cinzel',serif">${i + 1}.</span>
        <input class="field" style="flex:1;height:28px;font-size:12px"
          id="settingsWeekDay${i}" value="${d.replace(/"/g, '&quot;')}" placeholder="Day ${i + 1}"
          oninput="document.getElementById('settingsCalPreset').value='custom'">
      </div>`).join('');
  }

  function updateWeekCount() {
    const n = parseInt(document.getElementById('settingsWeekCount')?.value) || 7;
    const clamped = Math.max(1, Math.min(20, n));
    const currentCount = parseInt(document.getElementById('settingsWeekCount')?.value) || 7;
    const current = Array.from({ length: 20 }, (_, i) =>
      document.getElementById(`settingsWeekDay${i}`)?.value || ''
    ).filter((_, i) => i < currentCount);
    const defaults = DEFAULT_SETTINGS.calendar.weekDays;
    const days = Array.from({ length: clamped }, (_, i) =>
      (current[i] !== undefined && current[i] !== '') ? current[i] : (defaults[i] || `Day ${i + 1}`)
    );
    buildWeekdayInputs(days);
  }

  function applyCalPreset() {
    const key = document.getElementById('settingsCalPreset')?.value;
    if (!key || key === 'custom') return;
    const preset = CALENDAR_PRESETS[key];
    if (!preset) return;

    if (preset.eraName != null) {
      const eraIn = document.getElementById('settingsEraName');
      if (eraIn) eraIn.value = preset.eraName;
    }
    if (Array.isArray(preset.months)) {
      const monthCount = document.getElementById('settingsMonthCount');
      if (monthCount) monthCount.value = preset.months.length;
      buildMonthInputs(preset.months);
    }
    if (preset.daysPerMonth != null) {
      const dpM = document.getElementById('settingsDaysPerMonth');
      if (dpM) dpM.value = preset.daysPerMonth;
    }
    if (Array.isArray(preset.weekDays)) {
      const weekCount = document.getElementById('settingsWeekCount');
      if (weekCount) weekCount.value = preset.weekDays.length;
      buildWeekdayInputs(preset.weekDays);
    }
  }

  // ── Moon Editor ───────────────────────────────────────────

  let _editMoons = [];

  function renderMoonList(moons) {
    _editMoons = moons.map(m => ({ ...m }));
    _refreshMoonList();
  }

  function _refreshMoonList() {
    const list = document.getElementById('settingsMoonList');
    if (!list) return;
    if (!_editMoons.length) {
      list.innerHTML = '<div style="color:var(--text3);font-size:13px;padding:8px 0">No moons configured — click + Add Moon to add one.</div>';
      return;
    }
    list.innerHTML = _editMoons.map((m, i) => `
      <div style="display:flex;align-items:center;gap:10px;padding:10px 12px;background:var(--bg3);border:1px solid var(--border);border-radius:var(--radius)">
        <div style="display:flex;flex-direction:column;gap:4px;flex:1">
          <div style="display:flex;gap:8px;align-items:center">
            <label class="settings-label" style="margin:0;min-width:36px">Name</label>
            <input class="field" style="flex:1;height:28px;font-size:12px" id="moonName${i}"
              value="${m.name.replace(/"/g,'&quot;')}" placeholder="Moon name">
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            <label class="settings-label" style="margin:0;min-width:36px">Cycle</label>
            <input type="number" class="field" style="width:72px;height:28px;text-align:center;font-size:12px"
              id="moonCycle${i}" value="${m.cycle}" min="1" max="9999" placeholder="Days">
            <span style="font-size:12px;color:var(--text3)">days</span>
          </div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:center;gap:4px">
          <label class="settings-label" style="margin:0">Color</label>
          <input type="color" id="moonColor${i}" value="${m.color}"
            style="width:40px;height:32px;border:1px solid var(--border);border-radius:4px;padding:2px;background:var(--bg2);cursor:pointer">
        </div>
        <button class="btn small" style="color:var(--red);border-color:var(--red-dim);align-self:flex-start"
          onclick="ThekodiaSettings.removeMoon(${i})">✕</button>
      </div>`).join('');
  }

  function addMoon() {
    _editMoons.push({ name: `Moon ${_editMoons.length + 1}`, cycle: 28, color: '#a0a0c8' });
    _refreshMoonList();
  }

  function removeMoon(idx) {
    _collectMoonEdits();
    _editMoons.splice(idx, 1);
    _refreshMoonList();
  }

  function _collectMoonEdits() {
    _editMoons = _editMoons.map((m, i) => ({
      name:  document.getElementById(`moonName${i}`)?.value.trim()  || m.name,
      cycle: parseInt(document.getElementById(`moonCycle${i}`)?.value) || m.cycle,
      color: document.getElementById(`moonColor${i}`)?.value        || m.color,
    }));
  }

  // ── Save ──────────────────────────────────────────────────

  async function save() {
    // World
    settings.worldName = (document.getElementById('settingsWorldName')?.value || 'Thekodia').trim() || 'Thekodia';

    // Clock ratio
    settings.clockRatio = parseInt(document.getElementById('settingsRatioRange')?.value) || 5;

    // Calendar
    const presetKey   = document.getElementById('settingsCalPreset')?.value || 'thekodia';
    const eraName     = (document.getElementById('settingsEraName')?.value || 'CE').trim() || 'CE';
    const daysPerMonth = parseInt(document.getElementById('settingsDaysPerMonth')?.value) || 28;
    const monthCount  = parseInt(document.getElementById('settingsMonthCount')?.value) || 12;
    const months = Array.from({ length: monthCount }, (_, i) => {
      const v = document.getElementById(`settingsMonth${i}`)?.value.trim();
      return v || `Month ${i + 1}`;
    });
    const weekCount = parseInt(document.getElementById('settingsWeekCount')?.value) || 7;
    const weekDays = Array.from({ length: weekCount }, (_, i) => {
      const v = document.getElementById(`settingsWeekDay${i}`)?.value.trim();
      return v || DEFAULT_SETTINGS.calendar.weekDays[i] || `Day ${i + 1}`;
    });

    settings.calendar = { preset: presetKey, eraName, months, daysPerMonth, weekDays };

    // Moons
    _collectMoonEdits();
    settings.moons = _editMoons.length
      ? _editMoons.filter(m => m.name)
      : DEFAULT_SETTINGS.moons;

    // Player display
    settings.playerDisplay = {
      showHpBars:     !!(document.getElementById('dispShowHp')?.checked),
      showConditions: !!(document.getElementById('dispShowConditions')?.checked),
      maskEnemies:    !!(document.getElementById('dispMaskEnemies')?.checked),
    };

    const json = JSON.stringify(settings);
    localStorage.setItem(LS_KEY, json);
    try {
      await fetch(`${BASE}/data/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: json,
      });
    } catch {}

    applyWorldName();
    close();
  }

  // ── Campaign Management ────────────────────────────────────

  async function loadCampaigns() {
    const listEl = document.getElementById('settingsCampaignList');
    const activeEl = document.getElementById('settingsActiveCampaign');
    if (!listEl) return;
    listEl.innerHTML = '<div style="color:var(--text3);font-size:13px">Loading…</div>';
    try {
      const r = await fetch(`${BASE}/campaigns`);
      if (!r.ok) throw new Error();
      const { campaigns, active } = await r.json();
      if (activeEl) activeEl.textContent = active;
      if (!campaigns.length) {
        listEl.innerHTML = '<div style="color:var(--text3);font-size:13px">No campaigns found.</div>';
        return;
      }
      listEl.innerHTML = campaigns.map(name => {
        const isActive = name === active;
        const safeName = name.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
        return `<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;
          background:var(--bg3);border:1px solid ${isActive ? 'var(--accent-dim)' : 'var(--border)'};
          border-radius:var(--radius)">
          <span style="flex:1;font-weight:600;${isActive ? 'color:var(--accent)' : ''}">${name}${isActive ? ' ✓' : ''}</span>
          ${!isActive ? `<button class="btn small primary" style="font-size:11px;padding:2px 8px"
            onclick="ThekodiaSettings.switchCampaign('${safeName}')">Switch</button>` : ''}
          ${!isActive ? `<button class="btn small" style="font-size:11px;padding:2px 8px;color:var(--red);border-color:var(--red-dim)"
            onclick="ThekodiaSettings.deleteCampaign('${safeName}')">Delete</button>` : ''}
        </div>`;
      }).join('');
    } catch {
      if (listEl) listEl.innerHTML = '<div style="color:var(--text3);font-size:13px">Could not reach server — launch app.py first.</div>';
    }
  }

  async function createCampaign() {
    const input = document.getElementById('settingsNewCampaignName');
    const msgEl = document.getElementById('settingsCampaignMsg');
    const name = input?.value.trim();
    if (!name) return;
    if (msgEl) msgEl.textContent = '';
    try {
      const r = await fetch(`${BASE}/campaigns`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await r.json();
      if (data.error) { if (msgEl) msgEl.textContent = data.error; return; }
      if (input) input.value = '';
      loadCampaigns();
    } catch {
      if (msgEl) msgEl.textContent = 'Error creating campaign.';
    }
  }

  async function switchCampaign(name) {
    if (!confirm(`Switch to "${name}"?\n\nThe page will reload to load that campaign's data.`)) return;
    try {
      const r = await fetch(`${BASE}/campaigns/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await r.json();
      if (data.error) { alert(data.error); return; }
      location.reload();
    } catch {
      alert('Error switching campaign — is the server running?');
    }
  }

  async function deleteCampaign(name) {
    if (!confirm(`Delete campaign "${name}"?\n\nAll data in that campaign will be permanently deleted.`)) return;
    try {
      const r = await fetch(`${BASE}/campaigns/${encodeURIComponent(name)}`, { method: 'DELETE' });
      const data = await r.json();
      if (data.error) { alert(data.error); return; }
      loadCampaigns();
    } catch {
      alert('Error deleting campaign.');
    }
  }

  return {
    init, open, close, save,
    showTab, applyCalPreset,
    updateMonthCount, updateWeekCount,
    addMoon, removeMoon,
    get: () => settings,
    createCampaign, switchCampaign, deleteCampaign, loadCampaigns,
  };
})();

document.addEventListener('DOMContentLoaded', () => ThekodiaSettings.init());
