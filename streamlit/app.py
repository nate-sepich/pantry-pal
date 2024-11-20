# app.py

import streamlit as st
import logging
from datetime import datetime
import pytz  # Import pytz for timezone conversion
from api_utils import fetch_pantry_items, add_pantry_item, delete_pantry_item, authenticate_user, get_ai_meal_recommendation, get_meal_suggestions
import json  # Import json for import/export functionality

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

st.title("Pantry Pal")

# Placeholder function to simulate user authentication
if "user" not in st.session_state:
    st.session_state["user"] = None
if "token" not in st.session_state:
    st.session_state["token"] = None

def get_user():
    return st.session_state["user"]

def login(username, password):
    logging.info(f"Attempting to log in user: {username}")
    user = authenticate_user(username, password)
    if user and "access_token" in user:
        logging.info(f"User {username} logged in successfully")
        st.session_state["user"] = user
        st.session_state["token"] = user["access_token"]
        logging.info(f"Stored token: {st.session_state['token']}")
        st.success("Logged in successfully")
        st.rerun()
    else:
        logging.warning(f"Failed login attempt for user: {username}")
        st.error("Invalid username or password")

def logout():
    if st.session_state["user"]:
        logging.info(f"User {st.session_state['user']['username']} logged out")
    st.session_state["user"] = None
    st.session_state["token"] = None
    st.rerun()

def export_pantry(items):
    """Export pantry items to a JSON file."""
    file_content = json.dumps(items, indent=4)
    st.download_button(
        label="⬇️ Export Pantry",
        data=file_content,
        file_name="pantry_export.json",
        mime="application/json"
    )

def import_pantry(file):
    """Import pantry items from a JSON file."""
    try:
        items = json.load(file)
        for item in items:
            if not any(existing_item['product_name'] == item['product_name'] for existing_item in fetch_pantry_items(user["id"], st.session_state["token"])):
                add_pantry_item(user["id"], item["product_name"], item["quantity"], st.session_state["token"])
        st.success("Pantry items imported successfully")
    except Exception as e:
        logging.error(f"Error importing pantry items: {e}")
        st.error(f"Error importing pantry items: {e}")

user = get_user()

if user is None:
    st.header("Login")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            login(username, password)
else:
    # Sidebar for adding new items and import/export features
    with st.sidebar:
        # Welcome Header with Emoji
        st.markdown(f"# 👋 Welcome, {user.get('username', 'User')}!")

        # Display the date and time in US Central Time
        central = pytz.timezone('US/Central')
        current_datetime = datetime.now(central)
        st.markdown(f"#### **{current_datetime.strftime('%A, %B %d, %Y')}**")  # Bold date
        st.markdown(f"## **{current_datetime.strftime('%I:%M %p')}**")       # Bold time
        
        st.markdown("---")  # Separator line
        
        # Add New Item Section with Emoji
        st.markdown("#### ➕ Add New Item")
        with st.form("add_item_form"):
            name = st.text_input("Item Name")
            quantity = st.number_input("Quantity", min_value=1)
            submitted = st.form_submit_button("Add Item")
            if submitted:
                logging.info(f"Submitting new item: {name}, quantity: {quantity}")
                if add_pantry_item(user["id"], name, quantity, st.session_state["token"]):
                    st.success("Item added successfully")
                    st.rerun()  # Refresh the page to show new item
                else:
                    logging.error("Failed to add item")
        
        st.markdown("---")  # Separator line
        
        # Import and Export Section with Emoji
        st.markdown("#### 📁 Import/Export Pantry")
        # Export Pantry Button
        export_pantry(fetch_pantry_items(user["id"], st.session_state["token"]))
        # Import Pantry File Uploader
        import_file = st.file_uploader("Upload Pantry JSON", type=["json"])
        if import_file is not None:
            import_pantry(import_file)
        
        st.markdown("---")  # Separator line
        
        # Logout Button with Emoji
        if st.button("🚪 Logout"):
            logout()


    # Callback functions for deletion
    def confirm_delete(item_id):
        logging.info(f"User {user['username']} requested to delete item ID: {item_id}")
        st.session_state[f"delete_confirm_{item_id}"] = True

    def delete_item(item_id):
        if delete_pantry_item(user["id"], item_id, st.session_state["token"]):
            logging.info(f"Item ID: {item_id} deleted successfully by user {user['username']}")
            st.success("Item deleted successfully")
            # Remove the confirmation state
            del st.session_state[f"delete_confirm_{item_id}"]
        else:
            logging.error(f"Failed to delete item ID: {item_id} for user {user['username']}")
            st.error("Failed to delete the item.")

    def cancel_delete(item_id):
        logging.info(f"User {user['username']} canceled deletion of item ID: {item_id}")
        st.session_state[f"delete_confirm_{item_id}"] = False

    def render_pantry_items():
        """Display pantry items and handle deletion with confirmation."""
        token = st.session_state.get("token")
        logging.info(f"Using token: {token}")
        items = fetch_pantry_items(user["id"], token)
        if items:
            logging.info(f"Fetched {len(items)} items for user {user['username']}")
            for item in items:
                item_id = item['id']
                with st.expander(f"{item['product_name']} - Quantity: {item['quantity']}"):
                    if st.session_state.get(f"expanded_{item_id}", False):
                        macros = item.get('macros', {})
                        if macros:
                            calories = macros.get('calories', 'N/A')
                            carbs = macros.get('carbohydrates', 'N/A')
                            protein = macros.get('protein', 'N/A')
                        else:
                            calories = 'N/A'
                            carbs = 'N/A'
                            protein = 'N/A'
                        st.write(f"**Calories**: {calories}kcal")
                        st.write(f"**Carbs**: {carbs}g")
                        st.write(f"**Protein**: {protein}g")
                    else:
                        st.session_state[f"expanded_{item_id}"] = True

                    if not st.session_state.get(f"delete_confirm_{item_id}", False):
                        st.button(
                            "Delete",
                            key=f"delete_{item_id}",
                            on_click=confirm_delete,
                            args=(item_id,)
                        )
                    else:
                        st.warning(f"Are you sure you want to delete **{item['product_name']}**?")
                        col1, col2 = st.columns(2)
                        col1.button(
                            "Yes",
                            key=f"confirm_yes_{item_id}",
                            on_click=delete_item,
                            args=(item_id,)
                        )
                        col2.button(
                            "No",
                            key=f"confirm_no_{item_id}",
                            on_click=cancel_delete,
                            args=(item_id,)
                        )
        else:
            logging.info(f"No items found in pantry for user {user['username']}")
            st.write("No items in pantry.")

    render_pantry_items()

    # AI Recommendations
    def render_ai_recommendations():
        """Display AI-powered recommendations."""
        st.header("AI Meal Recommendation")
        if st.button("Generate AI Recommendation"):
            logging.info(f"User {user['username']} requested AI meal recommendation")
            recommendations = get_ai_meal_recommendation(user["id"], st.session_state["token"])
            st.write(f"{recommendations}")

    def render_meal_suggestions():
        """Display AI-powered meal suggestions based on daily macro goals."""
        st.header("AI Meal Suggestions")
        with st.form("macro_goals_form"):
            calories = st.number_input("Daily Calories", min_value=0)
            protein = st.number_input("Daily Protein (g)", min_value=0)
            carbohydrates = st.number_input("Daily Carbohydrates (g)", min_value=0)
            fat = st.number_input("Daily Fat (g)", min_value=0)
            submitted = st.form_submit_button("Get Meal Suggestions")
            if submitted:
                daily_macro_goals = {
                    "calories": calories,
                    "protein": protein,
                    "carbohydrates": carbohydrates,
                    "fat": fat
                }
                logging.info(f"User {user['username']} requested meal suggestions with goals: {daily_macro_goals}")
                meal_suggestions = get_meal_suggestions(user["id"], daily_macro_goals, st.session_state["token"])
                st.write(f"{meal_suggestions}")

    render_ai_recommendations()
    render_meal_suggestions()
    
    # ROI Dashboard
    # def render_roi_dashboard():
    #     """Display ROI metrics for the user."""
    #     logging.info(f"User {user['username']} requested ROI metrics")
    #     roi_metrics = calculate_roi_metrics(user["id"], st.session_state["token"])
    #     st.header("ROI Dashboard")
    #     st.write(f"**Health ROI**: {roi_metrics['health_roi']}")
    #     st.write(f"**Financial ROI**: {roi_metrics['financial_roi']}")
    #     st.write(f"**Environmental ROI**: {roi_metrics['environmental_roi']}")

    # render_roi_dashboard()
