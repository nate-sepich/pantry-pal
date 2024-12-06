from gradio import Interface, TextArea, Dropdown, CheckboxGroup
from api_utils import llm_chat  # Import the function from your `api_utils`

def construct_prompt(recipe_type, pantry_items, macro_goals):
    """Construct a structured prompt for the LLM."""
    prompt = f"Create a {recipe_type} recipe using the following pantry items: {', '.join(pantry_items)}."
    if macro_goals:
        prompt += f" The recipe should meet these macro goals: {macro_goals}."
    return prompt

def communicate_with_llm(recipe_type, pantry_items, macro_goals):
    """Send constructed prompt to LLM and return the response."""
    prompt = construct_prompt(recipe_type, pantry_items, macro_goals)
    return llm_chat(prompt)

def get_pantry_items():
    """Fetch pantry items. Replace this with an actual fetch if needed."""
    return ["Chicken", "Rice", "Beans", "Tomatoes", "Cheese", "Spinach"]

iface = Interface(
    fn=communicate_with_llm,
    inputs=[
        Dropdown(label="Recipe Type", choices=["Breakfast", "Lunch", "Dinner", "Snack", "Dessert"]),
        CheckboxGroup(label="Pantry Items", choices=get_pantry_items()),
        TextArea(label="Macro Goals (optional)", placeholder="e.g., High protein, low carb")
    ],
    outputs="text",
    title="PantryPal Recipe Generator",
    description="Generate recipes tailored to your pantry and macro goals."
)

if __name__ == "__main__":
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, type=int, help="Port to run Gradio")
    args = parser.parse_args()

    # Launch Gradio Interface
    iface.launch(share=False, server_name="0.0.0.0", server_port=7860)
