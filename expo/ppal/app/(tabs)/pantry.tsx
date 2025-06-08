import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Modal, Dimensions } from 'react-native';
import { SafeAreaView, Image } from 'react-native';
import { TextInput as RNTextInput } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons'; // Icons for delete and add actions
import apiClient from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';
import { useRouter, Redirect } from 'expo-router';
import { InventoryItem } from '../../src/types/InventoryItem';

export default function PantryScreen() {
  const { userToken, userId, loading, signOut } = useAuth();
  const router = useRouter();
  const [pantryItems, setPantryItems] = useState<InventoryItem[]>([]);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [itemName, setItemName] = useState('');
  const [itemQuantity, setItemQuantity] = useState('');
  const [selectedItemDetails, setSelectedItemDetails] = useState<InventoryItem | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
  const { width } = Dimensions.get('window');
  // Images are auto-generated upon item creation via the API

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
      const res = await apiClient.get<InventoryItem[]>('/pantry/items');
      console.log('Fetched pantry items:', res.data);
      // Filter active items and map image_url to imageUrl
      const activeItems = res.data
        .filter((item: InventoryItem) => item.active)
        .map((item: InventoryItem) => ({
          ...item,
          imageUrl: item.image_url || item.imageUrl || null,
        }));
      setPantryItems(activeItems);
    } catch (e: any) {
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
    } catch (e: any) {
      console.error('Error adding item:', e);
    }
  };

  const handleDeleteItem = async (id: string) => {
    try {
      console.log(`Sending request to soft delete item with ID: ${id}`);
      
      // Optimistically update the UI by removing the item from the state
      setPantryItems(prevItems => prevItems.filter(item => item.id !== id));

      await apiClient.delete(`/pantry/items/${id}`); // Soft delete the item
      console.log(`Item with ID: ${id} marked as inactive.`);
    } catch (e: any) {
      console.error(`Error soft deleting item with ID: ${id}`, e);
      // Optionally, refetch the pantry items to ensure consistency
      fetchPantry();
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedItems(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const showItemDetails = (item: InventoryItem) => {
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
    // Clear auth state and storage
    await signOut();
    router.replace('/login');
  };

  if (loading) {
    return <ActivityIndicator style={styles.centered} size="large" />;
  }

  if (!userToken) {
    return <Redirect href="/login" />;
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.title}>My Pantry</Text>
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Text style={styles.logoutButtonText}>Logout</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={pantryItems}
        keyExtractor={item => item.id}
        numColumns={2}
        columnWrapperStyle={styles.columnWrapper}
        contentContainerStyle={pantryItems.length < 2 ? styles.listCenter : styles.list}
        ListEmptyComponent={() => (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>Your pantry is empty.</Text>
            <Text style={styles.emptySubtext}>Tap + to add your first item.</Text>
          </View>
        )}
        renderItem={({ item }) => (
          <View style={[styles.card, { width: (width - 48) / 2 }]}> 
            {item.imageUrl ? (
              <Image source={{ uri: item.imageUrl }} style={styles.cardImage} resizeMode="cover" />
            ) : (
              <View style={styles.cardPlaceholder}>
                <MaterialIcons name="image-not-supported" size={48} color="#ccc" />
              </View>
            )}
            <View style={styles.cardBody}>
              <Text numberOfLines={1} style={styles.cardTitle}>{item.product_name}</Text>
              <Text style={styles.cardQuantity}>Qty: {item.quantity}</Text>
              <View style={styles.cardActions}>
                <TouchableOpacity onPress={() => showItemDetails(item)}>
                  <MaterialIcons name="info-outline" size={20} color="#0a7ea4" />
                </TouchableOpacity>
                <TouchableOpacity onPress={() => handleDeleteItem(item.id)}>
                  <MaterialIcons name="delete" size={20} color="#ff4d4d" />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        )}
      />

      {/* Floating Add Button */}
      <TouchableOpacity style={styles.fab} onPress={() => setAddModalVisible(true)}>
        <MaterialIcons name="add" size={28} color="#fff" />
      </TouchableOpacity>

      {/* Add Item Modal */}
      <Modal visible={addModalVisible} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.addSheet}>
            <Text style={styles.addTitle}>Add Item</Text>
            <RNTextInput
              style={styles.addInput}
              placeholder="Item name"
              value={itemName}
              onChangeText={setItemName}
            />
            <RNTextInput
              style={styles.addInput}
              placeholder="Quantity"
              keyboardType="numeric"
              value={itemQuantity}
              onChangeText={setItemQuantity}
            />
            <TouchableOpacity style={styles.addButton} onPress={() => { handleAddItem(); setAddModalVisible(false); }}>
              <Text style={styles.addButtonText}>Save</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.addCancel} onPress={() => setAddModalVisible(false)}>
              <Text style={styles.addCancelText}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

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
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f5f5' },
  container: { flexGrow: 1, padding: 16 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 28, fontWeight: '700', textAlign: 'center' },
  logoutButton: { backgroundColor: '#ff4d4d', padding: 8, borderRadius: 8 },
  logoutButtonText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  emptyText: { fontSize: 16, color: '#888', textAlign: 'center', marginVertical: 16 },
  list: { paddingHorizontal: 16, paddingBottom: 120 },
  listCenter: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 16 },
  card: { backgroundColor: '#fff', borderRadius: 12, margin: 8, overflow: 'hidden', shadowColor: '#000', shadowOpacity: 0.1, shadowOffset: { width:0, height:2 }, shadowRadius:4, elevation:3 },
  cardImage: { width: '100%', height: 150, backgroundColor: '#eee' },
  cardPlaceholder: { width: '100%', height: 150, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f0f0' },
  cardBody: { padding: 12 },
  cardTitle: { fontSize: 18, fontWeight: '600', marginBottom: 4 },
  cardQuantity: { fontSize: 14, color: '#666', marginBottom: 8 },
  cardActions: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 16 },
  columnWrapper: { justifyContent: 'space-between' },

  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 50 },
  emptySubtext: { fontSize: 14, color: '#888', marginTop: 4 },

  /* Add item bottom sheet style */
  modalOverlay: { flex:1, justifyContent:'flex-end', backgroundColor:'rgba(0,0,0,0.4)' },
  addSheet: { backgroundColor:'#fff', padding:16, borderTopLeftRadius:12, borderTopRightRadius:12 },
  addTitle: { fontSize:20, fontWeight:'bold', marginBottom:12 },
  addInput: { borderWidth:1, borderColor:'#ddd', borderRadius:8, padding:12, marginBottom:12 },
  addButton: { backgroundColor:'#0a7ea4', padding:14, borderRadius:8, alignItems:'center', marginBottom:8 },
  addButtonText: { color:'#fff', fontSize:16, fontWeight:'600' },
  addCancel: { alignItems:'center', padding:12 },
  addCancelText: { fontSize:16, color:'#0a7ea4' },
  fab: {
    position: 'absolute',
    bottom: 32,
    right: 32,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#0a7ea4',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOpacity: 0.3,
    shadowOffset: { width: 0, height: 4 },
    shadowRadius: 4,
    elevation: 4,
  },

  button: { backgroundColor: '#0a7ea4', padding: 12, borderRadius: 8, alignItems: 'center', marginVertical: 8 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  recipeContainer: { marginTop: 16, padding: 16, backgroundColor: '#fff', borderRadius: 8, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4 },
  recipeText: { fontSize: 16, lineHeight: 24 },
  modalContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0, 0, 0, 0.5)' },
  modalContent: { width: '80%', backgroundColor: '#fff', padding: 20, borderRadius: 12, alignItems: 'center' },
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
  modalButtons: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', marginTop: 16 },
  quantityBadge: { backgroundColor: '#0a7ea4', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, marginLeft: 12 },
  badgeText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  itemImage: { width: 40, height: 40, borderRadius: 20, marginHorizontal: 8 },
  imageButton: { padding: 4, marginHorizontal: 4 },
});
