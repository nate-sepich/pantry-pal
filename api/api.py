import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pantry.pantry_service import pantry_router, get_roi_metrics
from macros.macro_service import macro_router
from auth.auth_service import auth_router
from ai.ai_service import ai_router

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

# Allow all origins, methods, and headers for simplicity
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your specific needs
    allow_credentials=True,
    allow_methods=["*"],  # Adjust this to your specific needs
    allow_headers=["*"],  # Adjust this to your specific needs
)

# Add your routers to the main app
app.include_router(pantry_router, tags=["Pantry"])
app.include_router(macro_router, tags=["Macros"])
app.include_router(auth_router, tags=["Auth"])
app.include_router(ai_router, tags=["AI"])

# Add new routes
app.add_api_route("/roi/metrics", get_roi_metrics, methods=["GET"], tags=["ROI"])

if __name__ == "__main__":
    logging.info("Starting API server")
    import uvicorn
    uvicorn.run(app, port=8000)