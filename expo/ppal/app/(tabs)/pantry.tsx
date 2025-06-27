import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Modal, Dimensions, SafeAreaView, Image, Pressable, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Card, Button, TextInput as PaperTextInput, FAB, ProgressBar, IconButton, Chip } from 'react-native-paper';
import { Picker } from '@react-native-picker/picker';
import { MaterialIcons } from '@expo/vector-icons'; // Icons for delete and add actions
import { Ionicons } from '@expo/vector-icons';
import apiClient from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';
import { useRouter, Redirect } from 'expo-router';
import { InventoryItem } from '../../src/types/InventoryItem';
import { RecipeRequest, RecipeResponse } from '../../src/types/RecipeRequest';
import { FoodCategory, FoodSuggestion } from '../../src/types/Food';

export default function PantryScreen() {
  const { userToken, userId, loading, signOut } = useAuth();
  const router = useRouter();
  const [pantryItems, setPantryItems] = useState<InventoryItem[]>([]);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [servings, setServings] = useState(1);
  const [showServingsPicker, setShowServingsPicker] = useState(false);
  const [flavorAdjustments, setFlavorAdjustments] = useState<string[]>([]);
  const [removeItems, setRemoveItems] = useState<string[]>([]);
  const [overrideInput, setOverrideInput] = useState('');
  const [overrides, setOverrides] = useState<string[]>([]);
  const [itemName, setItemName] = useState('');
  const [itemQuantity, setItemQuantity] = useState('');
  const [itemUnit, setItemUnit] = useState('g');
  const [categoryFilter, setCategoryFilter] = useState<FoodCategory | 'all'>('all');
  const [suggestions, setSuggestions] = useState<FoodSuggestion[]>([]);
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);
  const [detailItem, setDetailItem] = useState<InventoryItem | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
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

  useEffect(() => {
    fetchSuggestions(itemName);
  }, [itemName, categoryFilter]);

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

  const fetchSuggestions = async (text: string) => {
    if (text.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const params: any = { query: text };
      if (categoryFilter !== 'all') params.category = categoryFilter;
      const res = await apiClient.get<FoodSuggestion[]>('/macros/autocomplete', { params });
      setSuggestions(res.data);
    } catch (e) {
      console.warn('Autocomplete failed', e);
    }
  };

  const handleAddItem = async () => {
    if (!itemName || !itemQuantity) {
      console.error('Error: Item name or quantity is missing.');
      return;
    }

    try {
      const macroRes = await apiClient.post('/macros/item', {
        item_name: itemName,
        quantity: Number(itemQuantity),
        unit: itemUnit,
      });
      const response = await apiClient.post('/pantry/items', {
        product_name: itemName,
        quantity: Number(itemQuantity),
        macros: macroRes.data,
      });
      console.log('Item added successfully:', response.data);
      setItemName('');
      setItemQuantity('');
      setSuggestions([]);
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

  const handleGenerate = async () => {
    const payload: RecipeRequest = {
      itemIds: selectedItems,
      modifiers: {
        servings: servings !== 1 ? servings : undefined,
        flavorAdjustments: flavorAdjustments.length ? flavorAdjustments : undefined,
        removeItems: removeItems.length ? removeItems : undefined,
        overrides: overrides.length ? overrides : undefined,
      },
    };
    try {
      const res = await apiClient.post<RecipeResponse>('/openai/recipes/generate', payload);
      const recipeParam = encodeURIComponent(JSON.stringify(res.data.recipe));
      router.push({ pathname: '/chat', params: { recipe: recipeParam } });
    } catch (e) {
      console.error('Recipe generation failed', e);
    }
  };

  const toggleSelect = (id: string) => {
    setSelectedItems(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };
    
  const toggleExpandItem = (id: string) => {
    setExpandedItemId(prev => (prev === id ? null : id));
  };

  const openDetail = (item: InventoryItem) => {
    setDetailItem(item);
    setDetailVisible(true);
  };

  const toggleFlavor = (label: string) => {
    setFlavorAdjustments(prev =>
      prev.includes(label) ? prev.filter(x => x !== label) : [...prev, label]
    );
  };

  const toggleRemove = (name: string) => {
    setRemoveItems(prev =>
      prev.includes(name) ? prev.filter(x => x !== name) : [...prev, name]
    );
  };

  const addOverride = () => {
    if (overrideInput.trim()) {
      setOverrides(prev => [...prev, overrideInput.trim()]);
      setOverrideInput('');
    }
  };

  const renderMacroBars = (macros: any) => {
    if (!macros) return null;
    const data = [
      { label: 'Protein', value: Number(macros.protein || 0) },
      { label: 'Carbs', value: Number(macros.carbohydrates || 0) },
      { label: 'Fat', value: Number(macros.fat || 0) },
      { label: 'Sugar', value: Number(macros.sugar || 0) },
    ];
    const maxVal = Math.max(...data.map(d => d.value), 1);
    return data.map(d => (
      <View key={d.label} style={styles.macroRow}>
        <Text style={styles.macroText}>{`${d.label}: ${d.value}g`}</Text>
        <ProgressBar progress={d.value / maxVal} color="#0a7ea4" style={styles.macroBar} />
      </View>
    ));
  };

  const handleLogout = async () => {
    // Clear auth state and storage
    await signOut();
    router.replace('/login');
  };

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!userToken) {
    return <Redirect href="/login" />;
  }

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
      <Modal
        visible={detailVisible}
        transparent
        animationType="slide"
        onRequestClose={() => setDetailVisible(false)}
      >
        <Pressable style={styles.detailOverlay} onPress={() => setDetailVisible(false)}>
          <View style={styles.modalContent}>
            {detailItem && (
              <ScrollView>
                {detailItem.imageUrl && (
                  <Image source={{ uri: detailItem.imageUrl }} style={styles.modalImage} />
                )}
                <Text style={styles.modalTitle}>{detailItem.product_name}</Text>
                {detailItem.macros && (
                  <View style={{ marginBottom: 16 }}>
                    <Text style={styles.sectionHeader}>Macros</Text>
                    {renderMacroBars(detailItem.macros)}
                  </View>
                )}
                <TouchableOpacity style={[styles.closeButton, { alignSelf: 'flex-end' }]} onPress={() => setDetailVisible(false)}>
                  <MaterialIcons name="close" size={24} color="#fff" />
                </TouchableOpacity>
              </ScrollView>
            )}
          </View>
        </Pressable>
      </Modal>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Ionicons name="cart-outline" size={32} color="white" />
          <Text style={styles.headerTitle}>My Pantry</Text>
          <Ionicons
            name="chatbubble-outline"
            size={24}
            color="white"
            onPress={() => router.push('/chats')}
          />
        </View>
      </View>
      <View style={styles.content}>
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
           <Card
             style={[
               styles.card,
               { width: (width - 48) / 2 },
               selectedItems.includes(item.id) && styles.selectedCard,
            ]}
            onPress={() => openDetail(item)}
            onLongPress={() => toggleSelect(item.id)}
          >
           <View style={{ position: 'relative' }}>
             {item.imageUrl ? (
               <Card.Cover source={{ uri: item.imageUrl }} style={styles.cardImage} />
             ) : (
               <View style={styles.cardPlaceholder}>
                 <MaterialIcons name="image-not-supported" size={48} color="#ccc" />
               </View>
             )}
             {/* delete overlay icon */}
             <TouchableOpacity style={styles.deleteOverlay} onPress={() => handleDeleteItem(item.id)}>
               <Ionicons name="trash-outline" size={20} color="#ff4d4d" />
             </TouchableOpacity>
           </View>
             <Card.Content style={styles.cardBody}>
               <Text numberOfLines={1} style={styles.cardTitle}>{item.product_name}</Text>
               <Text style={styles.cardQuantity}>Qty: {item.quantity}</Text>
               {expandedItemId === item.id && (
                 <View style={styles.macrosContainer}>
                   {renderMacroBars(item.macros)}
                 </View>
               )}
             </Card.Content>
             <Card.Actions style={styles.cardActions}>
               <Button textColor="#0a7ea4" onPress={() => toggleExpandItem(item.id)}>
                 {expandedItemId === item.id ? 'Hide' : 'Info'}
               </Button>
             </Card.Actions>
           </Card>
         )}
       />

       {selectedItems.length > 0 && (
         <View style={styles.modifierSection}>
           <View style={styles.chipRow}>
             <Chip
               style={styles.chip}
               selected={servings > 1}
               onPress={() => setShowServingsPicker(true)}
             >
               {servings > 1 ? `${servings} Servings` : 'Scale Servings'}
             </Chip>
             <Chip
               style={styles.chip}
               selected={flavorAdjustments.includes('Less Salty')}
               onPress={() => toggleFlavor('Less Salty')}
             >
               Less Salty
             </Chip>
             <Chip
               style={styles.chip}
               selected={flavorAdjustments.includes('No Carbs')}
               onPress={() => toggleFlavor('No Carbs')}
             >
               No Carbs
             </Chip>
             {pantryItems.find(p => selectedItems.includes(p.id) && p.quantity === 0) && (
               <Chip
                 style={styles.chip}
                 selected={removeItems.includes(
                   pantryItems.find(p => selectedItems.includes(p.id) && p.quantity === 0)!.product_name
                 )}
                 onPress={() =>
                   toggleRemove(
                     pantryItems.find(p => selectedItems.includes(p.id) && p.quantity === 0)!.product_name
                   )
                 }
               >
                 {`Remove ${
                   pantryItems.find(p => selectedItems.includes(p.id) && p.quantity === 0)!.product_name
                 }`}
               </Chip>
             )}
           </View>
           <View style={styles.overrideRow}>
             {overrides.map(note => (
               <Chip key={note} style={styles.chip} onClose={() => setOverrides(overrides.filter(n => n !== note))}>
                 {note}
               </Chip>
             ))}
             <PaperTextInput
               style={styles.overrideInput}
               mode="outlined"
               placeholder="Add note"
               value={overrideInput}
               onChangeText={setOverrideInput}
               onSubmitEditing={addOverride}
             />
           </View>
           <Button mode="contained" onPress={handleGenerate} style={styles.generateButton}>
             Generate Recipe
           </Button>
         </View>
       )}

       {/* Floating Add Button */}
       <FAB
         icon="plus"
         style={styles.fab}
         onPress={() => setAddModalVisible(true)}
       />

       {/* Add Item Modal */}
       <Modal visible={addModalVisible} animationType="slide" transparent>
         <KeyboardAvoidingView
           style={styles.modalOverlay}
           behavior={Platform.OS === 'ios' ? 'padding' : undefined}
         >
           <View style={styles.addSheet}>
             <Text style={styles.addTitle}>Add Item</Text>
            <Picker
              selectedValue={categoryFilter}
              style={styles.picker}
              onValueChange={(v) => setCategoryFilter(v as FoodCategory | 'all')}
            >
              <Picker.Item label="All Categories" value="all" />
              {Object.values(FoodCategory).map(cat => (
                <Picker.Item key={cat} label={cat} value={cat} />
              ))}
            </Picker>
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Item name"
              value={itemName}
              onChangeText={setItemName}
            />
            {suggestions.length > 0 && (
              <View style={styles.suggestionBox}>
                {suggestions.map(s => (
                  <TouchableOpacity key={s.fdc_id || s.name} onPress={() => { setItemName(s.name); setSuggestions([]); }}>
                    <Text style={styles.suggestionText}>{s.name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Quantity"
              keyboardType="numeric"
              value={itemQuantity}
              onChangeText={setItemQuantity}
            />
            <Picker
              selectedValue={itemUnit}
              style={styles.picker}
              onValueChange={(v) => setItemUnit(v)}
            >
              {['g', 'kg', 'oz', 'lb', 'ml', 'l', 'fl_oz'].map(u => (
                <Picker.Item key={u} label={u} value={u} />
              ))}
            </Picker>
            <Button
              mode="contained"
              style={styles.addButton}
              buttonColor="#0a7ea4"
              onPress={() => {
                 handleAddItem();
                 setAddModalVisible(false);
               }}
             >
               Save
             </Button>
             <Button mode="text" textColor="#0a7ea4" onPress={() => setAddModalVisible(false)}>
               Cancel
             </Button>
           </View>
         </KeyboardAvoidingView>
       </Modal>

       <Modal visible={showServingsPicker} transparent animationType="fade">
         <View style={styles.modalOverlay}>
           <View style={styles.addSheet}>
             <Text style={styles.addTitle}>Servings</Text>
             <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
               <IconButton icon="minus" onPress={() => setServings(Math.max(1, servings - 1))} />
               <Text>{servings}</Text>
               <IconButton icon="plus" onPress={() => setServings(Math.min(8, servings + 1))} />
             </View>
             <Button onPress={() => setShowServingsPicker(false)}>Done</Button>
           </View>
         </View>
       </Modal>

     </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f5f5' },
  header: { backgroundColor: '#0d9488', padding: 16 },
  headerContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  content: { flex: 1, padding: 16 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '700', textAlign: 'center' },
  logoutButton: { backgroundColor: '#0a7ea4', padding: 8, borderRadius: 8 },
  logoutButtonText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  emptyText: { fontSize: 16, color: '#888', textAlign: 'center', marginVertical: 16 },
  list: { paddingHorizontal: 16, paddingBottom: 120 },
  listCenter: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 16 },
  card: { backgroundColor: '#fff', borderRadius: 16, margin: 8, overflow: 'hidden', shadowColor: '#000', shadowOpacity: 0.1, shadowOffset: { width:0, height:2 }, shadowRadius:4, elevation:3 },
  cardImage: { width: '100%', height: 150, backgroundColor: '#eee' },
  cardPlaceholder: { width: '100%', height: 150, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f0f0' },
  cardBody: { padding: 12 },
  cardTitle: { fontSize: 20, fontWeight: '600', marginBottom: 4 },
  cardQuantity: { fontSize: 14, color: '#666', marginBottom: 8 },
  cardActions: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 16 },
  columnWrapper: { justifyContent: 'space-between' },

  selectedCard: { borderColor: '#0a7ea4', borderWidth: 2 },

  modifierSection: { padding: 16 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', marginBottom: 8 },
  chip: { marginRight: 8, marginBottom: 8 },
  overrideRow: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center' },
  overrideInput: { flex: 1, marginVertical: 4 },
  generateButton: { marginTop: 8 },

  emptyContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', marginTop: 50 },
  emptySubtext: { fontSize: 14, color: '#888', marginTop: 4 },

  /* Add item bottom sheet style */
  modalOverlay: { flex:1, justifyContent:'flex-end', backgroundColor:'rgba(0,0,0,0.4)' },
  detailOverlay: { flex:1, justifyContent:'center', alignItems:'center', backgroundColor:'rgba(0,0,0,0.5)' },
  addSheet: { backgroundColor:'#fff', padding:16, borderTopLeftRadius:12, borderTopRightRadius:12 },
  addTitle: { fontSize:20, fontWeight:'bold', marginBottom:12 },
  addInput: { borderWidth:1, borderColor:'#ddd', borderRadius:8, padding:12, marginBottom:12 },
  picker: { marginBottom: 12 },
  suggestionBox: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#ddd', borderRadius: 8, maxHeight: 120, marginBottom: 12 },
  suggestionText: { padding: 8 },
  addButton: { marginBottom:8 },
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

  recipeContainer: { marginTop: 16, padding: 16, backgroundColor: '#fff', borderRadius: 8, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 4 },
  macrosContainer: { marginTop: 8 },
  macroRow: { marginBottom: 6 },
  macroText: { fontSize: 12, marginBottom: 2 },
  macroBar: { height: 8, borderRadius: 4 },
  modalContent: {
    width: '90%',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
  },
  modalImage: { width: '100%', height: 200, borderRadius: 8, marginBottom: 16 },
  modalTitle: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
  sectionHeader: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
  closeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#0d9488',
    borderRadius: 16,
    padding: 8,
  },
  deleteOverlay: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(255,255,255,0.8)',
    borderRadius: 12,
    padding: 4,
    zIndex: 1,
  },
});
