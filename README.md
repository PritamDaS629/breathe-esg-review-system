# Breathe ESG Ingestion Prototype

A Django REST + React prototype for ingesting SAP fuel/procurement exports, utility electricity CSVs, and corporate travel exports, normalizing rows into reviewable emission activities, and approving records for audit lock.

## Demo credentials

- Tenant: `Acme Manufacturing`
- Analyst user: `analyst@acme.example`
- Password: `breathe-demo`

## Local run

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_BASE=http://localhost:8000/api` for local development if needed.

## Deployment

The repo includes `render.yaml` for a single Render web service. The Django app serves the React production build via WhiteNoise, runs migrations, and seeds demo data during the build command.

## Sample uploads

Sample source files live in `sample_data/`:

- `sap_material_movements.csv`
- `utility_green_button_style.csv`
- `concur_travel_segments.csv`

Upload them from the Sources page or seed them with `python manage.py seed_demo`.
