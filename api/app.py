import logging
import json
import os
import asyncio
import boto3
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum  # AWS Lambda adapter for FastAPI
from pantry.pantry_service import pantry_router, get_roi_metrics
from ai.openai_service import enrich_image_job  # helper for image hydration
from macros.macro_service import macro_router, enrich_item, enrich_recipe
from auth.auth_service import auth_router
from ai.ai_service import ai_router
from ai.openai_service import openai_router
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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

# SQS setup for background hydration jobs
MACRO_QUEUE_URL = os.getenv("MACRO_QUEUE_URL")
sqs = boto3.client("sqs")
handler_api = Mangum(app)

# Lambda handler
def lambda_handler(event, context):
    """
    Handle both SQS and API Gateway events.
    """
    # Handle SQS events
    if event.get("Records") and event["Records"][0].get("eventSource") == "aws:sqs":
        for rec in event["Records"]:
            msg = json.loads(rec["body"])
            logging.info(f"Received hydration message: {msg}")
            job = msg.get("jobType", "ITEM")
            payload = msg.get("payload", {})
            if job == "ITEM":
                logging.info(f"Hydrating macros ITEM job: {payload}")
                enrich_item(payload)
            elif job == "RECIPE":
                logging.info(f"Hydrating macros RECIPE job: {payload}")
                enrich_recipe(payload)
            elif job == "IMAGE":
                logging.info(f"Hydrating image IMAGE job: {payload}")
                enrich_image_job(payload)
            else:
                logging.warning(f"Unknown hydration job type: {job} with payload {payload}")
        return {"status": "hydration jobs processed"}

    # Handle API Gateway events
    return handler_api(event, context)

if __name__ == "__main__":
    logging.info("Starting API server")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)