import ast
import json
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import polib
import requests
import django
from django.utils.translation.template import templatize

BASE_DIR = Path(__file__).resolve().parent
LANGUAGES = {
    'hi': 'hi',
    'ml': 'ml',
    'ta': 'ta',
    'te': 'te',
    'kn': 'kn',
    'bn': 'bn',
    'mr': 'mr',
    'gu': 'gu',
    'pa': 'pa',
    'or': 'or',
    'as': 'as',
    'ur': 'ur',
}
FUNCTIONS = {'_', 'gettext', 'gettext_lazy', 'ngettext', 'pgettext', 'npgettext'}
TEMPLATE_CALL = re.compile(r"\b(ngettext|npgettext|pgettext|gettext)\(\s*(?:u)?('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")", re.S)
STRING_TOKEN = re.compile(r"\s*(?:u)?('(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\")", re.S)
PLACEHOLDER = re.compile(r'%\([^)]+\)[a-zA-Z]|%[sdif]')


def python_messages(source_path):
    try:
        tree = ast.parse(source_path.read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return [], []
    singles = []
    plurals = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = node.func.id if isinstance(node.func, ast.Name) else None
        if name not in FUNCTIONS:
            continue
        values = [arg.value for arg in node.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
        if name in {'ngettext', 'npgettext'} and len(values) >= 2:
            plurals.append((values[0], values[1]))
        elif values:
            singles.append(values[0])
    return singles, plurals


def template_messages(source_path):
    try:
        extracted = templatize(source_path.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, ValueError):
        return [], []
    singles = []
    plurals = []
    for match in TEMPLATE_CALL.finditer(extracted):
        name = match.group(1)
        first = ast.literal_eval(match.group(2))
        if name in {'ngettext', 'npgettext'}:
            second = STRING_TOKEN.search(extracted, match.end())
            if second:
                plurals.append((first, ast.literal_eval(second.group(1))))
        else:
            singles.append(first)
    return singles, plurals


def collect_messages():
    singles = set()
    plurals = set()
    for path in BASE_DIR.rglob('*.py'):
        if any(part in {'venv', '.venv', 'migrations', 'tests'} for part in path.parts):
            continue
        found, plural_found = python_messages(path)
        singles.update(found)
        plurals.update(plural_found)
    for path in BASE_DIR.rglob('*.html'):
        if any(part in {'venv', '.venv'} for part in path.parts):
            continue
        found, plural_found = template_messages(path)
        singles.update(found)
        plurals.update(plural_found)
    for singular, plural in plurals:
        singles.discard(singular)
        singles.discard(plural)
    return sorted(singles), sorted(plurals)


def protect_placeholders(text):
    tokens = {}

    def replace(match):
        token = f'QZXVAR{len(tokens)}QXZ'
        tokens[token] = match.group(0)
        return token

    return PLACEHOLDER.sub(replace, text), tokens


def translate_batch(language, originals):
    prepared = []
    token_maps = []
    for original in originals:
        translated_input, tokens = protect_placeholders(original)
        prepared.append(translated_input)
        token_maps.append(tokens)
    query = '\n'.join(prepared)
    response = requests.get(
        'https://translate.googleapis.com/translate_a/single',
        params={'client': 'gtx', 'sl': 'en', 'tl': language, 'dt': 't', 'q': query},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    translated = ''.join(part[0] for part in payload[0] if part and part[0] is not None)
    values = translated.split('\n')
    if len(values) != len(originals):
        values = []
        for item, tokens in zip(prepared, token_maps):
            retry = requests.get(
                'https://translate.googleapis.com/translate_a/single',
                params={'client': 'gtx', 'sl': 'en', 'tl': language, 'dt': 't', 'q': item},
                timeout=20,
            )
            retry.raise_for_status()
            value = ''.join(part[0] for part in retry.json()[0] if part and part[0] is not None)
            for token, source in tokens.items():
                value = re.sub(re.escape(token), source, value, flags=re.IGNORECASE)
            values.append(value)
        return values
    for index, tokens in enumerate(token_maps):
        for token, source in tokens.items():
            values[index] = re.sub(re.escape(token), source, values[index], flags=re.IGNORECASE)
    return values


def translate_strings(language, strings):
    cache_directory = Path(tempfile.gettempdir()) / 'citypulse-i18n-cache'
    cache_directory.mkdir(parents=True, exist_ok=True)
    cache_path = cache_directory / f'{language}.json'
    try:
        result = json.loads(cache_path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        result = {}
    batches = []
    current = []
    current_length = 0
    for text in strings:
        if text in result:
            continue
        if not text:
            result[text] = text
            continue
        if '\n' in text:
            if current:
                batches.append(current)
                current = []
                current_length = 0
            batches.append([text])
            continue
        if current and current_length + len(text) > 1800:
            batches.append(current)
            current = []
            current_length = 0
        current.append(text)
        current_length += len(text) + 1
    if current:
        batches.append(current)

    def worker(batch):
        for attempt in range(7):
            try:
                return batch, translate_batch(language, batch)
            except (requests.RequestException, ValueError, IndexError, TypeError):
                if attempt == 6:
                    raise
                time.sleep(2 * (attempt + 1))

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(worker, batch) for batch in batches]
        for future in as_completed(futures):
            batch, translations = future.result()
            result.update(zip(batch, translations))
            cache_path.write_text(json.dumps(result, ensure_ascii=False), encoding='utf-8')
    return result


def create_catalog(locale, language, singles, plurals, translations):
    po = polib.POFile()
    po.metadata = {
        'Project-Id-Version': 'CityPulse',
        'Report-Msgid-Bugs-To': '',
        'POT-Creation-Date': '',
        'PO-Revision-Date': '',
        'Last-Translator': 'Machine translation; review required',
        'Language-Team': locale,
        'Language': locale,
        'MIME-Version': '1.0',
        'Content-Type': 'text/plain; charset=UTF-8',
        'Content-Transfer-Encoding': '8bit',
        'Plural-Forms': 'nplurals=2; plural=(n != 1);',
    }
    for text in singles:
        po.append(polib.POEntry(msgid=text, msgstr=translations.get(text, text)))
    for singular, plural in plurals:
        po.append(polib.POEntry(
            msgid=singular,
            msgid_plural=plural,
            msgstr_plural={
                0: translations.get(singular, singular),
                1: translations.get(plural, plural),
            },
        ))
    directory = BASE_DIR / 'locale' / locale / 'LC_MESSAGES'
    directory.mkdir(parents=True, exist_ok=True)
    po_path = directory / 'django.po'
    mo_path = directory / 'django.mo'
    po.save(str(po_path))
    po.save_as_mofile(str(mo_path))


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citypulse.settings')
    django.setup()
    singles, plurals = collect_messages()
    strings = sorted(set(singles) | {value for pair in plurals for value in pair})
    print(f'Extracted {len(singles)} singular strings and {len(plurals)} plural pairs.')
    for locale, target in LANGUAGES.items():
        translated = translate_strings(target, strings)
        create_catalog(locale, target, singles, plurals, translated)
        print(f'Compiled {locale}: {len(translated)} strings.')


if __name__ == '__main__':
    main()
