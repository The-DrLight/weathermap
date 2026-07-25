# Lagos Smart Weather Prediction System

University project for EEG 323 (Instrumentation and Measurement II). Fetches live Lagos
atmospheric data, predicts rain in the next 24 hours with a Random Forest classifier,
and validates the prediction against Open-Meteo's forecast and NASA POWER data.

**Lagos coordinates:** 6.5244° N, 3.3792° E

## Stack

- **Backend:** Python, FastAPI
- **Frontend:** React (Vite)
- **ML:** scikit-learn (Random Forest Classifier)
- **Data:** Open-Meteo API (live + historical), NASA POWER API (validation)
- **Deployment:** Render (backend), Vercel (frontend)

## Project structure

```
weathermap/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # config/settings
│   │   ├── ml/           # feature engineering + predictor
│   │   ├── schemas/      # pydantic models
│   │   └── services/     # Open-Meteo / NASA POWER clients
│   ├── data/              # downloaded historical data (gitignored)
│   ├── models/            # trained model artifacts (gitignored)
│   ├── tests/
│   ├── train_model.py     # training script (Step 3)
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── components/    # dashboard UI
│       ├── hooks/         # data-fetching hooks
│       └── services/      # API client
├── render.yaml
└── vercel.json
```

## Build order

1. ✅ Project scaffold
2. ✅ Data fetcher module (Open-Meteo + NASA POWER)
3. ✅ Model training script (4 years of Lagos historical data, Random Forest)
4. ✅ FastAPI backend endpoints: `/weather/live`, `/predict`, `/validate`
5. ✅ React frontend dashboard
6. ✅ Deployment config (render.yaml, vercel.json)

## Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Dashboard available at `http://localhost:5173`.

### Training the model

`/predict` and `/validate` return `503` until a model exists at
`backend/models/rain_model.joblib`. Run `python backend/train_model.py` once
Step 3 (training script) is implemented.

## Deployment

- **Backend (Render):** connects `render.yaml` at the repo root; `rootDir: backend`, so
  Render builds and runs from `backend/` directly. Pinned to `PYTHON_VERSION=3.11` (Render's
  default Python has been less reliable for scikit-learn/numpy wheel availability than 3.11).
- **Frontend (Vercel):** connects `vercel.json` at the repo root. Because `vercel.json` uses
  plain relative paths (`npm run build`, `dist`), **you must set the Vercel project's Root
  Directory to `frontend`** in the Vercel dashboard (Project Settings → General → Root
  Directory) — otherwise Vercel will try to build from the repo root instead of `frontend/`.

### ⚠️ Before deploying the frontend

`frontend/.env.production` ships with a placeholder:

```
VITE_API_URL=https://your-render-url.onrender.com
```

**You must replace this with your actual Render backend URL** once the backend is deployed
(Render assigns the URL after first deploy — it looks like
`https://lagos-weather-backend-xxxx.onrender.com`). Vite bakes `.env.production` into the
build at build time, so this has to be correct *before* running `npm run build` / triggering
a Vercel deploy — updating it after deploy requires a rebuild.

Also set `FRONTEND_ORIGIN` in the Render dashboard to your deployed Vercel URL, so the
backend's CORS policy allows the frontend to call it.

### Cold start on Render

`backend/models/rain_model.joblib` is gitignored (it's a 120MB+ binary artifact), so it
won't exist on a fresh Render deploy. `app/main.py` checks for it on startup and, if
missing, trains the model live by calling `train_model.py`'s `main()` — you'll see
`"Model not found — training now. This will take ~2 minutes."` in the Render logs on
first boot. Subsequent restarts skip training since the model file persists on Render's
disk for the life of the instance (it is retrained again after any redeploy, since Render
containers are ephemeral).
