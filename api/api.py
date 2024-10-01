from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pantry.pantry_service import pantry_router
from macros.macro_service import macro_router

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, port=8000)