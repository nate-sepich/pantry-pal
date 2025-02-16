import signal
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
import os
import requests
import socket
from gradio import Interface, TextArea, Dropdown, CheckboxGroup, Markdown
from api_utils import fetch_pantry_items, llm_chat
import threading
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

API_URL = os.getenv("API_BASE", "http://api:8000")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthDetails(BaseModel):
    username: str
    access_token: str

async def communicate_with_llm(recipe_type: str, pantry_items: List[str], mods: str, all_pantry_items: List[str]):
    """Construct a prompt based on user inputs and stream the response from the LLM."""
    prompt = (
        "You are a culinary expert AI. Your task is to create a detailed and delicious recipe based on the user inputs below. "
        "Do not repeat the instructions or user inputs except as they naturally appear within the formatted recipe. "
        "The final answer should be a stand-alone recipe that another person can follow without additional explanation.\n"
        "\n"
        "Please format the response in Markdown as follows:\n"
        "## A short, descriptive title for the recipe.\n"
        "\n"
        "## Description\n"
        "A brief overview of what the dish is and why it’s appealing.\n"
        "\n"
        "## Ingredients\n"
        "A bulleted list of all the ingredients needed.\n"
        "- Clearly indicate which ingredients come from the selected pantry items.\n"
        "- If any required ingredients are not available in the provided pantry, note them after the list under a 'Missing Ingredients:' heading.\n"
        "\n"
        "## Instructions\n"
        "A clear, step-by-step guide on how to prepare and cook the dish.\n"
        "\n"
        "## Modifications\n"
        "If there are requested modifications, list and incorporate them here.\n"
        "\n"
        "### User Input\n"
        f"- Recipe Type: {recipe_type}\n"
        # f"- Available Pantry Items: {all_pantry_items}\n"
        f"- Selected Pantry Items: {', '.join(pantry_items)}\n"
    )
    if mods:
        prompt += f"- Requested Modifications: {mods}\n"
    prompt += "### Recipe\n"

    logging.info(f"Prompt: {prompt}")

    response_text = ""
    async for chunk in llm_chat(prompt):
        response_text += chunk
        yield response_text

def greet(name):
    return "Hello, " + name + "!"

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

@app.post("/launch_gradio")
async def launch_gradio(auth_details: AuthDetails):
    if not auth_details.access_token:
        raise HTTPException(status_code=401, detail="Authentication failed")

    import random
    port = random.randint(7860, 7890)
    while is_port_in_use(port):
        port = random.randint(7860, 7890)

    logging.info(f"Launching Gradio interface on port {port}")

    all_pantry_items = fetch_pantry_items(auth_details.username, auth_details.access_token)
    iface = Interface(
        fn=communicate_with_llm,
        inputs=[
            Dropdown(label="Recipe Type", choices=["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]),
            CheckboxGroup(label="Pantry Items", choices=all_pantry_items),
            TextArea(label="Modifications (optional)", placeholder="e.g., High protein, low carb"),
            CheckboxGroup(value=all_pantry_items,visible=False,choices=all_pantry_items)
        ],
        outputs=Markdown(label="Pal Response"),
        title="Recipe Generator",
        description="Select a recipe type, choose your required pantry items, and specify any macro goals."
    )

    async def launch_interface():
        iface.queue(max_size=20)  # Enable queuing with a maximum size
        iface.launch(share=False, server_name="0.0.0.0", server_port=port, inbrowser=False)

    loop = asyncio.get_event_loop()
    loop.create_task(launch_interface())

    logging.info(f"Gradio interface launched successfully on port {port}")
    return {"message": "Gradio interface launched successfully", "port": port, "status_code": 200}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
