from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import agreements, auth, buyers, counties, disposition, imports, leads, parcels

app = FastAPI(title="ChatCRM API")
BUILD_ID = "lead-postgres-diagnostics-1"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://127.0.0.1:4175",
        "http://127.0.0.1:4176",
        "http://127.0.0.1:4177",
        "http://127.0.0.1:4178",
        "http://localhost:5173",
        "http://localhost:4175",
        "http://localhost:4176",
        "http://localhost:4177",
        "http://localhost:4178",
        "https://chatcrm-olive.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(leads.router)
app.include_router(buyers.router)
app.include_router(counties.router)
app.include_router(disposition.router)
app.include_router(imports.router)
app.include_router(agreements.router)
app.include_router(parcels.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "build": BUILD_ID}


@app.get("/health/db")
def database_health_check():
    return {
        "build": BUILD_ID,
        "database": "postgres" if leads.USE_POSTGRES else "sqlite",
        "database_url_configured": bool(leads.RAW_DATABASE_URL),
        "database_url_scheme": leads.database_url_scheme(),
    }


@app.get("/health/leads")
def leads_health_check():
    try:
        saved_leads = leads.list_saved_leads()
    except Exception as exc:
        return {
            "build": BUILD_ID,
            "status": "error",
            "error_type": type(exc).__name__,
            "message": str(exc)[:500],
        }

    return {"build": BUILD_ID, "status": "ok", "count": len(saved_leads)}
