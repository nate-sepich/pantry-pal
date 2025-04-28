import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, Button, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, ScrollView, Modal } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import apiClient, { logout } from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';
import { useRouter } from 'expo-router'; // Import the router for navigation
import { MaterialIcons } from '@expo/vector-icons'; // Import MaterialIcons for trash can icon

export default function PantryScreen() {
  const { userToken, userId, signIn, loading } = useAuth();
  const router = useRouter(); // Initialize the router for navigation
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [pantryItems, setPantryItems] = useState<any[]>([]);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [recipeType, setRecipeType] = useState('Breakfast');
  const [recipe, setRecipe] = useState<string>('');
  const [itemName, setItemName] = useState('');
  const [itemQuantity, setItemQuantity] = useState('');
  const [selectedItemDetails, setSelectedItemDetails] = useState<any | null>(null);
  const [modalVisible, setModalVisible] = useState(false);

  useEffect(() => {
    if (userToken) {
      console.log('User token found:', userToken);
      console.log('User ID:', userId); // Debugging log for userId
      fetchPantry();
    } else {
      console.warn('No user token found. Please log in.');
    }
  }, [userToken]);

  const fetchPantry = async () => {
    try {
      const res = await apiClient.get('/pantry/items');
      console.log('Fetched pantry items:', res.data); // Debugging log to print all items
      const activeItems = res.data.filter((item: any) => {
        console.log('Item attributes:', item); // Debugging log for each item
        return item.active; // Filter active items
      });
      setPantryItems(activeItems);
    } catch (e) {
      console.error('Error fetching pantry items:', e);
    }
  };

  const handleAddItem = async () => {
    if (!itemName || !itemQuantity) {
      console.error('Error: Item name or quantity is missing.');
      return;
    }

    try {
      console.log('Sending API request to add item:', { product_name: itemName, quantity: Number(itemQuantity) });
      const response = await apiClient.post('/pantry/items', {
        product_name: itemName,
        quantity: Number(itemQuantity),
      });
      console.log('Item added successfully:', response.data);
      setItemName('');
      setItemQuantity('');
      fetchPantry(); // Refresh the pantry list
    } catch (e) {
      console.error('Error adding item:', e.response?.data || e.message);
    }
  };

  const handleDeleteItem = async (id: string) => {
    try {
      console.log(`Sending request to soft delete item with ID: ${id}`);
      
      // Optimistically update the UI by removing the item from the state
      setPantryItems(prevItems => prevItems.filter(item => item.id !== id));

      await apiClient.delete(`/pantry/items/${id}`); // Soft delete the item
      console.log(`Item with ID: ${id} marked as inactive.`);
    } catch (e) {
      console.error(`Error soft deleting item with ID: ${id}`, e.response?.data || e.message);
      // Optionally, refetch the pantry items to ensure consistency
      fetchPantry();
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedItems(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleGenerate = async () => {
    const names = pantryItems
      .filter(x => selectedItems.includes(x.id))
      .map(x => x.product_name);
    const prompt = `Create a ${recipeType} recipe using the following pantry items: ${names.join(', ')}.`;
    try {
      const res = await apiClient.post('/openai/llm_chat', { prompt });
      setRecipe(res.data.response || res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const showItemDetails = (item: any) => {
    const macros = item.macros || {
      calories: 0,
      protein: 0,
      carbohydrates: 0,
      fat: 0,
      sodium: 0,
      iron: 0,
    };
    setSelectedItemDetails({ ...item, macros });
    setModalVisible(true);
  };

  const handleLogout = async () => {
    console.log('Logging out...');
    await logout(); // Clear tokens
    signIn('', ''); // Reset authentication state
    router.replace('/'); // Redirect to the login screen
    console.log('User logged out successfully.');
  };

  if (loading) {
    return <ActivityIndicator style={styles.centered} size="large" />;
  }

  if (!userToken) {
    console.log('Redirecting to login screen...');
    return (
      <View style={styles.container}>
        <Text style={styles.title}>Sign In</Text>
        <TextInput
          placeholder="Username"
          value={username}
          onChangeText={setUsername}
          style={styles.input}
        />
        <TextInput
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          style={styles.input}
        />
        <TouchableOpacity style={styles.button} onPress={() => signIn(username, password)}>
          <Text style={styles.buttonText}>Sign In</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>My Pantry</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
      {pantryItems.length === 0 ? (
        <Text style={styles.emptyText}>Your pantry is empty. Add some items!</Text>
      ) : (
        <FlatList
          data={pantryItems}
          keyExtractor={item => item.id}
          renderItem={({ item }) => (
            <View style={styles.item}>
              <TouchableOpacity
                onPress={() => toggleSelect(item.id)}
                style={[
                  styles.itemDetails,
                  selectedItems.includes(item.id) && styles.selectedItem,
                ]}
              >
                <Text style={styles.itemText}>{item.product_name} ({item.quantity})</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => showItemDetails(item)}
                style={styles.infoButton}
              >
                <Text style={styles.infoButtonText}>i</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => handleDeleteItem(item.id)}
                style={styles.deleteButton}
              >
                <MaterialIcons name="delete" size={24} color="#ff4d4d" />
              </TouchableOpacity>
            </View>
          )}
        />
      )}

      <View style={styles.addContainer}>
        <TextInput
          placeholder="Item name"
          value={itemName}
          onChangeText={setItemName}
          style={styles.input}
        />
        <TextInput
          placeholder="Quantity"
          value={itemQuantity}
          onChangeText={setItemQuantity}
          keyboardType="numeric"
          style={styles.input}
        />
        <TouchableOpacity style={styles.button} onPress={() => {
          console.log('Add Item button pressed');
          handleAddItem();
        }}>
          <Text style={styles.buttonText}>Add Item</Text>
        </TouchableOpacity>
      </View>

      <Picker
        selectedValue={recipeType}
        onValueChange={setRecipeType}
        style={styles.picker}
      >
        <Picker.Item label="Breakfast" value="Breakfast" />
        <Picker.Item label="Lunch" value="Lunch" />
        <Picker.Item label="Dinner" value="Dinner" />
        <Picker.Item label="Snack" value="Snack" />
        <Picker.Item label="Dessert" value="Dessert" />
      </Picker>

      <TouchableOpacity style={styles.button} onPress={handleGenerate}>
        <Text style={styles.buttonText}>Generate Recipe</Text>
      </TouchableOpacity>

      {recipe ? (
        <View style={styles.recipeContainer}>
          <Text style={styles.recipeText}>{recipe}</Text>
        </View>
      ) : null}

      {/* Modal for item details */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            {selectedItemDetails ? (
              <>
                <Text style={styles.modalTitle}>{selectedItemDetails.product_name}</Text>
                <Text>Quantity: {selectedItemDetails.quantity}</Text>
                <Text>Calories: {selectedItemDetails.macros.calories}</Text>
                <Text>Protein: {selectedItemDetails.macros.protein}g</Text>
                <Text>Carbs: {selectedItemDetails.macros.carbohydrates}g</Text>
                <Text>Fat: {selectedItemDetails.macros.fat}g</Text>
                <Text>Sodium: {selectedItemDetails.macros.sodium}mg</Text>
                <Text>Iron: {selectedItemDetails.macros.iron}mg</Text>
              </>
            ) : (
              <Text>Loading...</Text>
            )}
            <TouchableOpacity
              style={styles.button}
              onPress={() => setModalVisible(false)}
            >
              <Text style={styles.buttonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 16, backgroundColor: '#f5f5f5' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 28, fontWeight: 'bold', textAlign: 'center' },
  logoutButton: { backgroundColor: '#ff4d4d', padding: 8, borderRadius: 8 },
  logoutButtonText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  emptyText: { fontSize: 16, color: '#888', textAlign: 'center', marginVertical: 16 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12, marginBottom: 12, backgroundColor: '#fff' },
  item: { flexDirection: 'row', alignItems: 'center', padding: 16, marginVertical: 8, backgroundColor: '#fff', borderRadius: 8, borderWidth: 1, borderColor: '#ddd' },
  itemDetails: { flex: 1, paddingVertical: 8, paddingHorizontal: 12 },
  selectedItem: { backgroundColor: '#d0f0c0', borderColor: '#a0d090' },
  itemText: { fontSize: 16 },
  addContainer: { marginTop: 16 },
  picker: { marginVertical: 16, backgroundColor: '#fff', borderRadius: 8 },
  button: { backgroundColor: '#0a7ea4', padding: 12, borderRadius: 8, alignItems: 'center', marginVertical: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  recipeContainer: { marginTop: 16, padding: 16, backgroundColor: '#fff', borderRadius: 8, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4 },
  recipeText: { fontSize: 16, lineHeight: 24 },
  modalContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0, 0, 0, 0.5)' },
  modalContent: { width: '80%', backgroundColor: '#fff', padding: 20, borderRadius: 8, alignItems: 'center' },
  modalTitle: { fontSize: 20, fontWeight: 'bold', marginBottom: 10 },
  selectButton: { padding: 8, borderRadius: 8, borderWidth: 1, borderColor: '#ddd', backgroundColor: '#f0f0f0', marginLeft: 8 },
  selectedButton: { backgroundColor: '#d0f0c0', borderColor: '#a0d090' },
  selectButtonText: { fontSize: 14, color: '#333' },
  infoButton: { backgroundColor: '#0a7ea4', padding: 8, borderRadius: 16, justifyContent: 'center', alignItems: 'center', marginLeft: 8 },
  infoButtonText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  deleteButton: {
    marginLeft: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
