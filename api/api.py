import logging
import json
import boto3
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum  # AWS Lambda adapter for FastAPI
from pantry.pantry_service import pantry_router, get_roi_metrics
from macros.macro_service import macro_router
from auth.auth_service import auth_router
from ai.ai_service import ai_router
from ai.openai_service import openai_router
from pydantic import BaseModel, ValidationError

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
app.include_router(openai_router, tags=["OpenAI"])

# Add new routes
app.add_api_route("/roi/metrics", get_roi_metrics, methods=["GET"], tags=["ROI"])

@app.get("/")
def root():
    return {"message": "Welcome to Pantry Pal API"}

# Define the schema for pantry items
class PantryItem(BaseModel):
    name: str
    quantity: int
    unit: str

@app.post("/pantry/items")
async def add_pantry_item(request: Request):
    try:
        # Parse and validate the request payload
        payload = await request.json()
        item = PantryItem(**payload)
        logging.info(f"Adding pantry item: {item}")
        # Add logic to save the item to the database (e.g., DynamoDB)
        return {"message": "Pantry item added successfully", "item": item.dict()}
    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail="Invalid request payload")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Lambda handler
def lambda_handler(event, context):
    asgi_handler = Mangum(app)
    return asgi_handler(event, context)

if __name__ == "__main__":
    logging.info("Starting API server")
    import uvicorn
    uvicorn.run(app, port=8000)