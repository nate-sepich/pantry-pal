import os
import json
import logging
import boto3
import requests
from openai import OpenAI
from storage.utils import pantry_table
from fastapi import HTTPException

# Configure logging
debug = os.getenv("DEBUG_IMAGE_HYDRATOR", "false").lower() == "true"
logging.basicConfig(level=logging.INFO if not debug else logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize AWS clients
s3 = boto3.client("s3")
dynamodb = pantry_table  # Uses existing table instance

# OpenAI setup
def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("OpenAI API key not configured")
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return OpenAI(api_key=api_key)

# Helper to ensure bucket exists

def _ensure_bucket(bucket_name: str):
    try:
        s3.head_bucket(Bucket=bucket_name)
    except s3.exceptions.NoSuchBucket:
        logging.info(f"Creating S3 bucket {bucket_name}")
        s3.create_bucket(Bucket=bucket_name)

# Handler invoked by SQS

def handler(event, context):
    """AWS Lambda handler for image generation hydration"""
    client = _get_openai_client()
    bucket_name = os.getenv("IMAGE_BUCKET_NAME")
    _ensure_bucket(bucket_name)

    for record in event.get('Records', []):
        try:
            body = json.loads(record['body'])
            user_id = body.get('user_id')
            item_id = body.get('item_id')
            item_name = body.get('item_name')
            logging.info(f"Processing image job for {user_id}/{item_id}")

            # Generate image via OpenAI
            prompt = f"High quality photo of {item_name} against a plain background."
            resp = client.images.generate(prompt=prompt, n=1, size="256x256")
            img_url = resp.data[0].url
            img_data = requests.get(img_url).content

            # Upload to S3
            key = f"{user_id}/{item_id}.png"
            s3.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=img_data,
                ContentType="image/png",
                ACL="public-read"
            )
            public_url = f"https://{bucket_name}.s3.amazonaws.com/{key}"

            # Update DynamoDB
            pk = f"USER#{user_id}"
            sk = f"PANTRY#{item_id}"
            dynamodb.update_item(
                Key={"PK": pk, "SK": sk},
                UpdateExpression="SET image_url = :url",
                ExpressionAttributeValues={":url": public_url}
            )
            logging.info(f"Image URL persisted for item {item_id}")
        except Exception as e:
            logging.error(f"Failed to process image job: {e}", exc_info=True)
    return {"status": "completed"}
