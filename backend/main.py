import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.leads import router as leads_router
from routes.contracts import router as contracts_router
from routes.invoices import router as invoices_router
from routes.chat import router as chat_router
from routes.webhooks import router as webhooks_router
from routes.signing import router as signing_router
from routes.company import router as company_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("QTC API running")
    yield


app = FastAPI(title="Quote-to-Cash API", version="1.0", lifespan=lifespan)

# Allow the configured frontend + common local dev ports.
# In production set ALLOWED_ORIGINS=https://yourapp.com (comma-separated for multiple).
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
)
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]
# Always include common Vite dev ports so local development never breaks
for _dev in ("http://localhost:5173", "http://localhost:8080", "http://localhost:8082"):
    if _dev not in _allowed_origins:
        _allowed_origins.append(_dev)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leads_router, prefix="/api")
app.include_router(contracts_router, prefix="/api")
app.include_router(invoices_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
app.include_router(signing_router, prefix="/api")  # public — no auth
app.include_router(company_router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "quote-to-cash"}
