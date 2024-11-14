import streamlit as st
import requests

API_URL = "http://localhost:8000/pantry/items"

def fetch_pantry_items():
    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error fetching pantry items: {e}")
        return []

def add_pantry_item(name, quantity):
    item = {"product_name": name, "quantity": quantity}
    try:
        response = requests.post(API_URL, json=item)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"Error adding pantry item: {e}")
        return None

def delete_pantry_item(item_id):
    try:
        response = requests.delete(f"{API_URL}/{item_id}")
        response.raise_for_status()
        return response.status_code
    except requests.RequestException as e:
        st.error(f"Error deleting pantry item: {e}")
        return None

st.title("Pantry Inventory")

with st.form("add_item_form"):
    name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=1)
    submitted = st.form_submit_button("Add Item")
    if submitted:
        if add_pantry_item(name, quantity):
            st.success("Item added successfully")
            st.experimental_rerun()  # Auto-refresh the page

st.header("Pantry Items")

if st.button("Refresh Pantry"):
    items = fetch_pantry_items()
else:
    items = fetch_pantry_items()

if items:
    st.write("### Pantry Items")
    for item in items:
        col1, col2, col3, col4, col5, col6 = st.columns([3, 1, 1, 1, 1, 1])
        col1.write(f"Name: {item['product_name']}")
        col2.write(f"Quantity: {item['quantity']}")
        col4.write(f"Protein: {item['macros']['protein']}")
        col5.write(f"Carbs: {item['macros']['carbohydrates']}g")
        if col6.button(f"Delete", key=item['id']):
            if st.confirm(f"Are you sure you want to delete {item['product_name']}?"):
                if delete_pantry_item(item['id']) == 204:
                    st.success("Item deleted successfully")
                    st.experimental_rerun()  # Auto-refresh the page
else:
    st.write("No items in pantry")

