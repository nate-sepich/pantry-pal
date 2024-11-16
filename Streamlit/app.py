# app.py

import streamlit as st
from api_utils import fetch_pantry_items, add_pantry_item, delete_pantry_item, authenticate_user

st.title("Pantry Pal")

# Placeholder function to simulate user authentication
def get_user():
    if "user" not in st.session_state:
        st.session_state["user"] = None
    return st.session_state["user"]

def login(username, password):
    user = authenticate_user(username, password)
    if user:
        st.session_state["user"] = user
        st.success("Logged in successfully")
        st.rerun()
    else:
        st.error("Invalid username or password")

def logout():
    st.session_state["user"] = None
    st.rerun()

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
    st.sidebar.button("Logout", on_click=logout)
    
    st.header(f"{user['username']}'s Pantry Items")

    # Sidebar for adding new items
    with st.sidebar:
        st.header("Add New Item")
        with st.form("add_item_form"):
            name = st.text_input("Item Name")
            quantity = st.number_input("Quantity", min_value=1)
            submitted = st.form_submit_button("Add Item")
            if submitted:
                if add_pantry_item(user["id"], name, quantity):
                    st.success("Item added successfully")
                    st.rerun() # Refresh the page to show new item

    # Callback functions for deletion
    def confirm_delete(item_id):
        st.session_state[f"delete_confirm_{item_id}"] = True

    def delete_item(item_id):
        if delete_pantry_item(user["id"], item_id):
            st.success("Item deleted successfully")
            # Remove the confirmation state
            del st.session_state[f"delete_confirm_{item_id}"]
        else:
            st.error("Failed to delete the item.")

    def cancel_delete(item_id):
        st.session_state[f"delete_confirm_{item_id}"] = False

    def render_pantry_items():
        """Display pantry items and handle deletion with confirmation."""
        items = fetch_pantry_items(user["id"])
        if items:
            for item in items:
                item_id = item['id']
                with st.expander(f"{item['product_name']} - Quantity: {item['quantity']}"):
                    if st.session_state.get(f"expanded_{item_id}", False):
                        macros = item.get('macros', {})
                        calories = macros.get('calories', 'N/A')
                        carbs = macros.get('carbohydrates', 'N/A')
                        protein = macros.get('protein', 'N/A')
                        st.write(f"**Calories**: {calories}kcal")
                        st.write(f"**Carbs**: {carbs}g")
                        st.write(f"**Protein**: {protein}g")
                    else:
                        st.session_state[f"expanded_{item_id}"] = True

                    if not st.session_state.get(f"delete_confirm_{item_id}", False):
                        # Show the Delete button
                        st.button(
                            "Delete",
                            key=f"delete_{item_id}",
                            on_click=confirm_delete,
                            args=(item_id,)
                        )
                    else:
                        # Show confirmation message and Yes/No buttons
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
            st.write("No items in pantry.")

    render_pantry_items()
