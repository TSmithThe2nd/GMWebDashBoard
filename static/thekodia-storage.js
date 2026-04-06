/**
 * Thekodia Storage Library
 * Replaces localStorage with Flask file-backed API.
 * Falls back to localStorage if server not available.
 */

const ThekodiaStorage = (() => {
  const BASE = 'http://localhost:5000';
  let _serverAvailable = null;

  // Map localStorage keys to server store names
  const KEY_MAP = {
    'thekodia_encounters':    'encounters',
    'thekodia_library':       'library',
    'thekodia_players':       'players',
    'thekodia_clock':         'clock',
    'thekodia_clock_history': 'clock_history',
    'thekodia_display_state': 'display_state',
    'thekodia_weather':       'weather',
    'thekodia_event':         'event',
    'thekodia_ref_notes':     'ref_notes',
    'thekodia_dice_presets':  'dice_presets',
    'thekodia_dice_history':  'dice_history',
    'thekodia_live_add':      'live_add',
  };

  async function checkServer() {
    if (_serverAvailable !== null) return _serverAvailable;
    try {
      const r = await fetch(`${BASE}/health`, { signal: AbortSignal.timeout(500) });
      _serverAvailable = r.ok;
    } catch {
      _serverAvailable = false;
    }
    return _serverAvailable;
  }

  async function getItem(key) {
    const store = KEY_MAP[key];
    if (store && await checkServer()) {
      try {
        const r = await fetch(`${BASE}/data/${store}`);
        const data = await r.json();
        return data === null ? null : JSON.stringify(data);
      } catch {}
    }
    return localStorage.getItem(key);
  }

  async function setItem(key, value) {
    // Always write to localStorage for instant cross-tab sync
    localStorage.setItem(key, value);
    const store = KEY_MAP[key];
    if (store && await checkServer()) {
      try {
        await fetch(`${BASE}/data/${store}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: value
        });
      } catch {}
    }
  }

  async function removeItem(key) {
    localStorage.removeItem(key);
    const store = KEY_MAP[key];
    if (store && await checkServer()) {
      try {
        await fetch(`${BASE}/data/${store}`, { method: 'DELETE' });
      } catch {}
    }
  }

  // Sync from server to localStorage on page load
  async function syncFromServer() {
    if (!await checkServer()) return;
    for (const [lsKey, store] of Object.entries(KEY_MAP)) {
      try {
        const r = await fetch(`${BASE}/data/${store}`);
        const data = await r.json();
        if (data !== null) {
          localStorage.setItem(lsKey, JSON.stringify(data));
        }
      } catch {}
    }
  }

  // Upload a PDF for parsing
  async function parsePDF(file) {
    if (!await checkServer()) {
      return { error: 'Server not running. Start app.py to use PDF parsing.' };
    }
    const formData = new FormData();
    formData.append('file', file);
    try {
      const r = await fetch(`${BASE}/parse-pdf`, { method: 'POST', body: formData });
      return await r.json();
    } catch (e) {
      return { error: e.message };
    }
  }

  function exportBackup() {
    const BACKUP_KEYS = [
      'thekodia_clock',
      'thekodia_clock_history',
      'thekodia_encounters',
      'thekodia_library',
      'thekodia_players',
      'thekodia_weather',
      'thekodia_ref_notes',
      'thekodia_dice_presets',
      'thekodia_display_state',
      'thekodia_live_add',
      'thekodia_event'
    ];

    const backup = {
      version: 1,
      timestamp: new Date().toISOString(),
      data: {}
    };

    BACKUP_KEYS.forEach(key => {
      const val = localStorage.getItem(key);
      if (val !== null) {
        try {
          backup.data[key] = JSON.parse(val);
        } catch {
          backup.data[key] = val;
        }
      }
    });

    const json = JSON.stringify(backup, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);

    const a = document.createElement('a');
    a.href = url;
    a.download = `thekodia-backup-${new Date().toISOString().slice(0,10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function importBackup(file) {
    if (!file) return;

    const reader = new FileReader();

    reader.onload = function(e) {
      try {
        const backup = JSON.parse(e.target.result);

        if (!backup.version || !backup.data) {
          alert('Invalid backup file.');
          return;
        }

        Object.entries(backup.data).forEach(([key, value]) => {
          localStorage.setItem(key, JSON.stringify(value));
        });

        alert(`Backup restored from ${backup.timestamp.slice(0,10)}. Reloading...`);
        location.reload();

      } catch {
        alert('Could not read backup file. Make sure it is a valid Thekodia backup.');
      }
    };

    reader.readAsText(file);
  }

  return { getItem, setItem, removeItem, syncFromServer, parsePDF, checkServer , exportBackup , importBackup };
})();
