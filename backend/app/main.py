from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import agreements, auth, imports, leads

app = FastAPI(title="ChatCRM API")

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
app.include_router(imports.router)
app.include_router(agreements.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
