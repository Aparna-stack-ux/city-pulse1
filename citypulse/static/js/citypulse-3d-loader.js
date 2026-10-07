const loadCityPulseScene = () => import('./citypulse-3d.js?v=4').catch(() => {});

window.addEventListener('load', () => {
    if (typeof window.requestIdleCallback === 'function') {
        window.requestIdleCallback(loadCityPulseScene, { timeout: 1200 });
    } else {
        window.setTimeout(loadCityPulseScene, 250);
    }
}, { once: true });