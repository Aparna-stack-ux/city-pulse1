(function () {
    const languagePattern = /^\/(?:en|hi|ml|ta|te|kn|bn|mr|gu|pa|or|as|ur)(?=\/|$)/;
    const formStateKey = 'citypulse-i18n-form-state';

    const withoutLanguagePrefix = (path) => path.replace(languagePattern, '') || '/';

    const saveFormState = () => {
        const fields = Array.from(document.querySelectorAll('input[name], textarea[name], select[name]'))
            .filter((field) => !['password', 'file', 'hidden', 'submit', 'reset', 'button'].includes(field.type))
            .filter((field) => !['language', 'csrfmiddlewaretoken'].includes(field.name))
            .map((field) => {
                const sameName = Array.from(document.getElementsByName(field.name));
                return {
                    name: field.name,
                    index: sameName.indexOf(field),
                    type: field.type,
                    value: field.multiple
                        ? Array.from(field.selectedOptions, (option) => option.value)
                        : field.value,
                    checked: field.type === 'checkbox' || field.type === 'radio' ? field.checked : undefined,
                };
            });

        try {
            sessionStorage.setItem(formStateKey, JSON.stringify({
                path: withoutLanguagePrefix(window.location.pathname),
                fields,
            }));
        } catch (error) {
            // Language switching still works if session storage is unavailable.
        }
    };

    const restoreFormState = () => {
        let savedState;
        try {
            savedState = JSON.parse(sessionStorage.getItem(formStateKey) || 'null');
            sessionStorage.removeItem(formStateKey);
        } catch (error) {
            return;
        }

        if (!savedState || savedState.path !== withoutLanguagePrefix(window.location.pathname)) return;

        savedState.fields.forEach((savedField) => {
            const field = document.getElementsByName(savedField.name)[savedField.index];
            if (!field) return;
            if (savedField.type === 'checkbox' || savedField.type === 'radio') {
                field.checked = savedField.checked;
            } else if (field.multiple && Array.isArray(savedField.value)) {
                Array.from(field.options).forEach((option) => {
                    option.selected = savedField.value.includes(option.value);
                });
            } else {
                field.value = savedField.value;
            }
        });
    };

    window.citypulseSetLanguage = (select) => {
        if (!select || !select.form) return;
        saveFormState();
        const nextField = select.form.elements.next;
        const currentPath = window.location.pathname;
        const isLocalePrefixed = languagePattern.test(currentPath);
        const path = withoutLanguagePrefix(currentPath);
        const targetPath = isLocalePrefixed
            ? `/${select.value}${path === '/' ? '/' : path}`
            : currentPath;
        nextField.value = `${targetPath}${window.location.search}`;
        select.form.requestSubmit();
    };

    document.addEventListener('DOMContentLoaded', restoreFormState);
})();