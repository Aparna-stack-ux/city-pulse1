# CityPulse

CityPulse is a Smart City Digital Twin Django project (demo).

## Setup (Windows)

1. Create and activate virtualenv

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Configure environment variables

```powershell
Copy-Item .env.example .env
```

Set `DJANGO_SECRET_KEY` in `.env` to a newly generated secret. In Supabase, open **Project Settings > Database > Connection string**, choose the URI format, and use that value for `DATABASE_URL`. URL-encode any special characters in the database password. Keep `.env` private; it is ignored by Git.

Without `DATABASE_URL`, the project uses the local `db.sqlite3` database. When `DATABASE_URL` is set, Django uses Supabase PostgreSQL and requires SSL by default.

4. Apply migrations

```powershell
python manage.py migrate
```

5. Create a superuser (follow prompts)

```powershell
python manage.py createsuperuser
```

6. (Optional) Load demo data

```powershell
python manage.py loaddemo
```

7. Run development server

```powershell
python manage.py runserver
```

## Notes
- Configure `OPENWEATHER_API_KEY` via environment variables or a `.env` file.
- Use `.env.example` as a template and never commit `.env` or database credentials.
- Run `python manage.py migrate` after setting `DATABASE_URL` to create the project tables in Supabase.
- Static files are expected under `citypulse/static/` and media under `media/`.
