from __future__ import annotations

import json
import os
from typing import Any, Dict

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import pipeline
import visualizations

app = FastAPI(title="YouTube Watch History API", version="1.0.0")

frontend_origin = os.getenv("FRONTEND_ORIGIN")
allow_origins = [frontend_origin] if frontend_origin else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Upload must be a .json file")

    try:
        raw = await file.read()
        history = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc}") from exc

    if not isinstance(history, list):
        raise HTTPException(
            status_code=400, detail="watch-history JSON must be a list of entries"
        )

    try:
        # Run the pipeline
        df = pipeline.run_pipeline(history)

        # Calculate visualization data
        dashboard = visualizations.create_dashboard_data(df)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "rows": int(len(df)),
        "dashboard": dashboard,
    }
