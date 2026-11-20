document.addEventListener('DOMContentLoaded', () => {
  for (const name of ['format', 'quality', 'height', 'playlist']) {
    const input = document.querySelector(`[name="${name}"]`);
    try {
      const saved = localStorage.getItem(`download-${name}`);
      if (saved !== null) {
        if (input.type === 'checkbox') input.checked = saved === 'true';
        else if ([...input.options].some(option => option.value === saved)) input.value = saved;
      }
    } catch (_) { /* Preferences are optional when browser storage is disabled. */ }
    input.addEventListener('change', () => {
      try { localStorage.setItem(`download-${name}`, input.type === 'checkbox' ? input.checked : input.value); } catch (_) {}
    });
  }
});
