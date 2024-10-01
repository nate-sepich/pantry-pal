document.addEventListener('DOMContentLoaded', () => {
  const BASE_URL = 'http://localhost:8000/pantry';
  const pantryForm = document.getElementById('pantry-form');
  const pantryTableBody = document.querySelector('#pantry-table tbody');

  // Fetch and display items
  async function fetchItems() {
      try {
          const response = await fetch(`${BASE_URL}/items`);
          const items = await response.json();
          pantryTableBody.innerHTML = '';
          items.forEach(item => {
              const row = document.createElement('tr');
              row.innerHTML = `
                  <td>${item.product_name}</td>
                  <td>${item.quantity}</td>
                  <td>${JSON.stringify(item.macros)}</td>
                  <td>
                      <button onclick="editItem('${item.id}')">Edit</button>
                      <button onclick="deleteItem('${item.id}')">Delete</button>
                  </td>
              `;
              pantryTableBody.appendChild(row);
          });
      } catch (error) {
          console.error('Error fetching items:', error);
      }
  }

// Add new item
pantryForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        const itemName = document.getElementById('item-name').value;
        const itemQuantity = document.getElementById('item-quantity').value;

        const newItem = {
                product_name: itemName,
                quantity: parseInt(itemQuantity, 10)
        };
            
        try {
                const response = await fetch(`${BASE_URL}/items`, {
                        method: 'POST',
                        headers: {
                                'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(newItem)
                });
                const createdItem = await response.json();
                fetchItems(); // Refresh the list
        } catch (error) {
                console.error('Error adding item:', error);
        }
});

  // Edit item
  window.editItem = async (itemId) => {
      const itemName = prompt('Enter new item name:');
      const itemQuantity = prompt('Enter new item quantity:');
      if (itemName && itemQuantity) {
          const updatedItem = {
              product_name: itemName,
              quantity: parseInt(itemQuantity, 10)
          };

          try {
              const response = await fetch(`${BASE_URL}/items/${itemId}`, {
                  method: 'PUT',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  body: JSON.stringify(updatedItem)
              });
              const updated = await response.json();
              fetchItems(); // Refresh the list
          } catch (error) {
              console.error(`Error updating item with ID ${itemId}:`, error);
          }
      }
  };

  // Delete item
  window.deleteItem = async (itemId) => {
      try {
          const response = await fetch(`${BASE_URL}/items/${itemId}`, {
              method: 'DELETE'
          });
          const result = await response.json();
          fetchItems(); // Refresh the list
      } catch (error) {
          console.error(`Error deleting item with ID ${itemId}:`, error);
      }
  };

  // Initial fetch of items
  fetchItems();
});