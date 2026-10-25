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

## Deploy to Render

1. Push the project to a GitHub repository that your Render account can access.
2. In Render, select **New + > Blueprint** and connect that repository. Render will use `render.yaml` to build and start the web service.
3. When prompted for `DATABASE_URL`, provide a PostgreSQL connection URI for a persistent database, such as the Supabase URI described above. Do not use SQLite for a deployed service because Render's local filesystem is ephemeral.
4. Deploy. The blueprint generates `DJANGO_SECRET_KEY`, disables debug mode, collects static files, and applies database migrations when the service starts. Render's `RENDER_EXTERNAL_HOSTNAME` is used for allowed hosts and CSRF checks.
5. Add `OPENWEATHER_API_KEY` and `OPENAI_API_KEY` in the Render service's environment settings if those integrations are needed.

The first push to GitHub must succeed before Render can access the project. If GitHub rejects the push, resolve repository access or authenticate Git with an account that has write access, then push the `main` branch.
