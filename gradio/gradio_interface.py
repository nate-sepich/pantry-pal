from gradio import Interface, TextArea, Dropdown, CheckboxGroup
import requests
import os
import logging
import socket

from api_utils import llm_chat, fetch_pantry_items

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_URL = os.getenv("API_BASE", "http://api:8000")

def communicate_with_llm(recipe_type, pantry_items, macro_goals):
    """Construct a prompt based on user inputs and send it to the LLM."""
    prompt = f"Create a {recipe_type} recipe using the following pantry items: {', '.join(pantry_items)}."
    if macro_goals:
        prompt += f" The recipe should meet these macro goals: {macro_goals}."
    return llm_chat(prompt)

def launch_interface(username, access_token, port):
    if not access_token:
        logging.error("Authentication failed. Unable to launch interface.")
        return

    iface = Interface(
        fn=communicate_with_llm,
        inputs=[
            Dropdown(label="Recipe Type", choices=["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]),
            CheckboxGroup(label="Pantry Items", choices=fetch_pantry_items(username, access_token)),
            TextArea(label="Macro Goals (optional)", placeholder="e.g., High protein, low carb")
        ],
        outputs="text",
        title="Recipe Generator",
        description="Select a recipe type, choose your available pantry items, and specify any macro goals."
    )
    iface.launch(share=False, server_port=port)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

if __name__ == "__main__":
    import argparse
    import random

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, type=str, help="Username for authentication")
    parser.add_argument("--access_token", required=True, type=str, help="Access token for authentication")
    args = parser.parse_args()

    # Choose a random port between 7860 and 7890 that is not in use
    port = random.randint(7860, 7890)
    while is_port_in_use(port):
        port = random.randint(7860, 7890)

    # Launch Gradio Interface
    launch_interface(args.username, args.access_token, port)

