const themeToggle = document.querySelector('[data-theme-toggle]');

if (themeToggle) {
    const updateThemeToggle = (theme) => {
        const isDark = theme === 'dark';
        const label = isDark ? themeToggle.dataset.themeLabelLight : themeToggle.dataset.themeLabelDark;
        themeToggle.setAttribute('aria-label', label);
        themeToggle.setAttribute('title', label);
        themeToggle.setAttribute('aria-pressed', String(isDark));
    };

    updateThemeToggle(document.documentElement.dataset.theme);

    themeToggle.addEventListener('click', () => {
        const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = nextTheme;
        updateThemeToggle(nextTheme);

        try {
            localStorage.setItem('citypulse-theme', nextTheme);
        } catch (error) {
            // The current page theme still works if storage is unavailable.
        }
    });
}
