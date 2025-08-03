import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Modal, Dimensions, SafeAreaView, Image, Pressable, ScrollView, KeyboardAvoidingView, Platform, Alert } from 'react-native';
import { Card, Button, TextInput as PaperTextInput, FAB, ProgressBar, IconButton, Chip, Searchbar } from 'react-native-paper';
import { Picker } from '@react-native-picker/picker';
import { MaterialIcons } from '@expo/vector-icons';
import { Ionicons } from '@expo/vector-icons';
// Remove camera imports for now and use manual entry only
// import { Camera } from 'expo-camera';
// import { BarCodeScanner } from 'expo-barcode-scanner';
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
  const [isAddingItem, setIsAddingItem] = useState(false);
  const [recentItems, setRecentItems] = useState<string[]>([]);
  const [popularItems, setPopularItems] = useState<string[]>([]);
  const [isLoadingPopular, setIsLoadingPopular] = useState(false);
  const [isLookingUp, setIsLookingUp] = useState(false);
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

  // Fetch popular items from backend
  useEffect(() => {
    if (userToken) {
      fetchPopularItems();
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

  const fetchPopularItems = async () => {
    try {
      setIsLoadingPopular(true);
      const res = await apiClient.get('/pantry/popular-items');
      setPopularItems(res.data.items || []);
    } catch (e) {
      console.warn('Failed to load popular items, using defaults');
      setPopularItems(['Milk', 'Bread', 'Eggs', 'Chicken Breast', 'Rice', 'Bananas']);
    } finally {
      setIsLoadingPopular(false);
    }
  };

  const handleAddItem = async () => {
    if (!itemName) {
      console.error('Error: Item name is missing.');
      return;
    }

    // Ensure we have a valid quantity - default to 1 if not set
    const quantity = itemQuantity && itemQuantity.trim() !== '' ? Number(itemQuantity) : 1;
    
    if (isNaN(quantity) || quantity <= 0) {
      console.error('Error: Invalid quantity.');
      Alert.alert('Error', 'Please enter a valid quantity.');
      return;
    }

    try {
      const macroRes = await apiClient.post('/macros/item', {
        item_name: itemName,
        quantity: quantity,
        unit: itemUnit,
      });
      const response = await apiClient.post('/pantry/items', {
        product_name: itemName,
        quantity: quantity,
        macros: macroRes.data,
      });
      console.log('Item added successfully:', response.data);
      setItemName('');
      setItemQuantity('');
      setSuggestions([]);
      fetchPantry(); // Refresh the pantry list
    } catch (e: any) {
      console.error('Error adding item:', e);
      Alert.alert('Error', 'Failed to add item. Please try again.');
    }
  };

  const handleQuickAdd = async (name: string) => {
    if (!name) {
      console.error('Error: Item name is missing for quick add.');
      return;
    }

    try {
      setIsAddingItem(true);
      console.log(`Quick adding item: ${name}`);
      
      // Get macro information for the item
      const macroRes = await apiClient.post('/macros/item', {
        item_name: name,
        quantity: 1,
        unit: 'g',
      });
      
      // Add the item to pantry
      const response = await apiClient.post('/pantry/items', {
        product_name: name,
        quantity: 1,
        macros: macroRes.data,
      });
      
      console.log('Quick add successful:', response.data);
      
      // Update recent items for better UX
      setRecentItems(prev => {
        const updated = [name, ...prev.filter(item => item !== name)];
        return updated.slice(0, 5); // Keep only top 5 recent items
      });
      
      // Refresh the pantry list
      fetchPantry();
      
      // Show success feedback
      Alert.alert('Success', `"${name}" added to your pantry!`);
      
    } catch (e: any) {
      console.error(`Error quick adding item ${name}:`, e);
      Alert.alert('Error', `Failed to add "${name}". Please try again.`);
    } finally {
      setIsAddingItem(false);
    }
  };

  const handleSuggestionSelect = (suggestion: FoodSuggestion) => {
    setItemName(suggestion.name);
    // Set default quantity to 1 if not already set
    if (!itemQuantity || itemQuantity.trim() === '') {
      setItemQuantity('1');
    }
    setSuggestions([]);
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

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    if (isLookingUp) return;
    
    setIsLookingUp(true);
    
    try {
      Alert.alert('Looking up product...', 'Please wait while we find product information.');
      
      const response = await apiClient.get(`/pantry/lookup/${data}`);
      if (response.data && response.data.product_name) {
        setItemName(response.data.product_name);
        setItemQuantity('1');
        setAddModalVisible(true);
        
        if (response.data.brand) {
          setRecentItems(prev => [response.data.product_name, ...prev.slice(0, 4)]);
        }
        
        Alert.alert('Product Found!', `Added "${response.data.product_name}" to the form.`);
      } else {
        Alert.alert('Product Not Found', 'This barcode was not found in our database. Please enter the item manually.');
        setAddModalVisible(true);
      }
    } catch (error: any) {
      console.error('UPC lookup failed:', error);
      if (error.response?.status === 404) {
        Alert.alert('Product Not Found', 'This barcode was not found in our database. Please enter the item manually.');
      } else {
        Alert.alert('Lookup Failed', 'Unable to find product information. Please enter manually.');
      }
      setAddModalVisible(true);
    } finally {
      setIsLookingUp(false);
    }
  };

  const openBarcodeScanner = async () => {
    // Since camera functionality is disabled, go straight to manual entry
    handleManualEntry();
  };

  const handleManualEntry = () => {
    Alert.prompt(
      'Enter Barcode',
      'Type the barcode number manually:',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Lookup', 
          onPress: (text) => {
            if (text && text.trim()) {
              handleBarCodeScanned({ type: 'manual', data: text.trim() });
            }
          }
        }
      ],
      'plain-text',
      '',
      'number-pad'
    );
  };

  const renderCameraModal = () => {
    // Camera functionality disabled for now
    return null;
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
               { width: (width - 32) / 2 - 8 }, // Improved spacing calculation
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
         onPress={() => {
           // Initialize with default values
           if (!itemQuantity || itemQuantity.trim() === '') {
             setItemQuantity('1');
           }
           setAddModalVisible(true);
         }}
       />

       {/* Add Item Modal */}
       <Modal visible={addModalVisible} animationType="slide" presentationStyle="fullScreen">
        <SafeAreaView style={styles.addModalContainer}>
          <View style={styles.addHeader}>
            <TouchableOpacity onPress={() => {
              setAddModalVisible(false);
              setItemName('');
              setItemQuantity('');
              setSuggestions([]);
              setCategoryFilter('all');
            }}>
              <Ionicons name="close" size={24} color="#0a7ea4" />
            </TouchableOpacity>
            <Text style={styles.addHeaderTitle}>Add Item</Text>
            <View style={styles.scanButtonGroup}>
              <TouchableOpacity 
                onPress={handleManualEntry}
                style={styles.scanButton}
              >
                <Ionicons name="keypad-outline" size={24} color="#0a7ea4" />
              </TouchableOpacity>
            </View>
          </View>

          <ScrollView style={styles.addContent} keyboardShouldPersistTaps="handled">
            {/* Popular Items Section */}
            <View style={styles.quickAddSection}>
              <Text style={styles.sectionTitle}>Popular Items</Text>
              {isLoadingPopular ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator size="small" color="#0a7ea4" />
                  <Text style={styles.loadingText}>Loading popular items...</Text>
                </View>
              ) : (
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={styles.quickAddRow}>
                    {popularItems.map(item => (
                      <TouchableOpacity 
                        key={item}
                        style={[
                          styles.quickAddChip,
                          itemName.toLowerCase() === item.toLowerCase() && styles.quickAddChipSelected
                        ]}
                        onPress={() => handleQuickAdd(item)}
                      >
                        <Text style={[
                          styles.quickAddText,
                          itemName.toLowerCase() === item.toLowerCase() && styles.quickAddTextSelected
                        ]}>
                          {item}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </ScrollView>
              )}
            </View>

            {/* Search Section */}
            <View style={styles.searchSection}>
              <Text style={styles.sectionTitle}>Search Items</Text>
              
              <View style={styles.categoryFilterRow}>
                <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                  <View style={styles.categoryChips}>
                    <Chip
                      selected={categoryFilter === 'all'}
                      onPress={() => setCategoryFilter('all')}
                      style={styles.categoryChip}
                    >
                      All
                    </Chip>
                    <Chip
                      selected={categoryFilter === FoodCategory.DAIRY}
                      onPress={() => setCategoryFilter(FoodCategory.DAIRY)}
                      style={styles.categoryChip}
                    >
                      Dairy
                    </Chip>
                    <Chip
                      selected={categoryFilter === FoodCategory.MEAT}
                      onPress={() => setCategoryFilter(FoodCategory.MEAT)}
                      style={styles.categoryChip}
                    >
                      Meat
                    </Chip>
                    <Chip
                      selected={categoryFilter === FoodCategory.VEGETABLES}
                      onPress={() => setCategoryFilter(FoodCategory.VEGETABLES)}
                      style={styles.categoryChip}
                    >
                      Vegetables
                    </Chip>
                    <Chip
                      selected={categoryFilter === FoodCategory.FRUITS}
                      onPress={() => setCategoryFilter(FoodCategory.FRUITS)}
                      style={styles.categoryChip}
                    >
                      Fruits
                    </Chip>
                    <Chip
                      selected={categoryFilter === FoodCategory.CARBS}
                      onPress={() => setCategoryFilter(FoodCategory.CARBS)}
                      style={styles.categoryChip}
                    >
                      Carbs
                    </Chip>
                  </View>
                </ScrollView>
              </View>

              <Searchbar
                placeholder="Search for an item..."
                value={itemName}
                onChangeText={setItemName}
                style={styles.searchBar}
                iconColor="#0a7ea4"
              />

              {/* Enhanced Suggestions */}
              {suggestions.length > 0 && (
                <View style={styles.modernSuggestionBox}>
                  {suggestions.slice(0, 5).map((suggestion) => (
                    <TouchableOpacity
                      key={suggestion.fdc_id || suggestion.name}
                      style={styles.suggestionItem}
                      onPress={() => handleSuggestionSelect(suggestion)}
                    >
                      <View style={styles.suggestionContent}>
                        <Text style={styles.suggestionName}>{suggestion.name}</Text>
                        <Text style={styles.suggestionCategory}>{suggestion.category}</Text>
                      </View>
                      <Ionicons name="add-circle-outline" size={20} color="#0a7ea4" />
                    </TouchableOpacity>
                  ))}
                </View>
              )}
            </View>

            {/* Add Button with quantity input */}
            <View style={styles.addButtonSection}>
              <View style={styles.quantityRow}>
                <PaperTextInput
                  mode="outlined"
                  label="Quantity"
                  value={itemQuantity}
                  onChangeText={setItemQuantity}
                  keyboardType="numeric"
                  placeholder="1"
                  style={styles.quantityInput}
                />
                <PaperTextInput
                  mode="outlined"
                  label="Unit"
                  value={itemUnit}
                  editable={false}
                  style={styles.unitInput}
                  right={
                    <PaperTextInput.Icon
                      icon="chevron-down"
                      onPress={() => {
                        // You could implement a unit picker modal here if needed
                        // For now, keeping it simple with default 'g'
                      }}
                    />
                  }
                />
              </View>
              
              <Button
                mode="contained"
                style={styles.modernAddButton}
                buttonColor="#0a7ea4"
                loading={isAddingItem}
                disabled={!itemName.trim() || isAddingItem}
                onPress={async () => {
                  setIsAddingItem(true);
                  try {
                    // Ensure quantity is set to 1 if not already set
                    if (!itemQuantity || itemQuantity.trim() === '') {
                      setItemQuantity('1');
                    }
                    await handleAddItem();
                    // Clear form and close modal on success
                    setItemName('');
                    setItemQuantity('');
                    setSuggestions([]);
                    setCategoryFilter('all');
                    setAddModalVisible(false);
                    
                    // Show success message
                    Alert.alert('Success', 'Item added to your pantry!');
                  } catch (error) {
                    console.error('Failed to add item:', error);
                    Alert.alert('Error', 'Failed to add item. Please try again.');
                  } finally {
                    setIsAddingItem(false);
                  }
                }}
              >
                {isAddingItem ? 'Adding Item...' : 'Add to Pantry'}
              </Button>
              
              <Text style={styles.helpText}>
                Enter quantity or leave empty for default of 1.
              </Text>
            </View>
          </ScrollView>
        </SafeAreaView>
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
  content: { flex: 1, padding: 8 }, // Reduced padding for better card spacing
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '700', textAlign: 'center' },
  logoutButton: { backgroundColor: '#0a7ea4', padding: 8, borderRadius: 8 },
  logoutButtonText: { color: '#fff', fontSize: 14, fontWeight: 'bold' },
  emptyText: { fontSize: 16, color: '#888', textAlign: 'center', marginVertical: 16 },
  list: { paddingHorizontal: 4, paddingBottom: 120 }, // Further reduced horizontal padding
  listCenter: { flexGrow: 1, justifyContent: 'center', paddingHorizontal: 4 },
  card: { 
    backgroundColor: '#fff', 
    borderRadius: 16, 
    margin: 4, // Keep margin at 4 for better fit
    overflow: 'hidden', 
    shadowColor: '#000', 
    shadowOpacity: 0.1, 
    shadowOffset: { width:0, height:2 }, 
    shadowRadius:4, 
    elevation:3 
  },
  cardImage: { width: '100%', height: 150, backgroundColor: '#eee' },
  cardPlaceholder: { width: '100%', height: 150, justifyContent: 'center', alignItems: 'center', backgroundColor: '#f0f0f0' },
  cardBody: { padding: 8 }, // Reduced padding for more compact cards
  cardTitle: { fontSize: 16, fontWeight: '600', marginBottom: 4 }, // Reduced font size for better fit
  cardQuantity: { fontSize: 14, color: '#666', marginBottom: 8 },
  cardActions: { flexDirection: 'row', justifyContent: 'space-between', paddingHorizontal: 8, paddingVertical: 4 }, // Reduced padding
  columnWrapper: { justifyContent: 'space-between', paddingHorizontal: 8 }, // Better distribution with space-between
  macroRow: { marginBottom: 4 },
  macroText: { fontSize: 12, color: '#666', marginBottom: 2 },
  macroBar: { height: 6, borderRadius: 3, backgroundColor: '#e0e0e0' },
  macrosContainer: { marginTop: 8 },

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
  addModalContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  addHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#e1e8ed',
  },
  addHeaderTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1d1d1f',
  },
  scanButtonGroup: {
    flexDirection: 'row',
    gap: 8,
  },
  scanButton: {
    padding: 8,
  },
  addContent: {
    flex: 1,
    padding: 16,
  },
  
  // Quick Add Section
  quickAddSection: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1d1d1f',
    marginBottom: 12,
  },
  quickAddRow: {
    flexDirection: 'row',
    gap: 8,
  },
  quickAddChip: {
    backgroundColor: 'white',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#e1e8ed',
    marginRight: 8,
  },
  quickAddText: {
    color: '#0a7ea4',
    fontWeight: '500',
  },
  
  // Search Section
  searchSection: {
    marginBottom: 24,
  },
  categoryFilterRow: {
    marginBottom: 16,
  },
  categoryChips: {
    flexDirection: 'row',
    gap: 8,
  },
  categoryChip: {
    marginRight: 8,
  },
  searchBar: {
    backgroundColor: 'white',
    elevation: 0,
    borderWidth: 1,
    borderColor: '#e1e8ed',
  },
  
  // Enhanced Suggestions
  modernSuggestionBox: {
    backgroundColor: 'white',
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: '#e1e8ed',
    overflow: 'hidden',
  },
  suggestionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f3f4',
  },
  suggestionContent: {
    flex: 1,
  },
  suggestionName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#1d1d1f',
  },
  suggestionCategory: {
    fontSize: 12,
    color: '#8e8e93',
    textTransform: 'capitalize',
    marginTop: 2,
  },
  
  // Quantity Section
  quantitySection: {
    marginBottom: 32,
  },
  quantityRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16, // Reduced spacing before add button
  },
  quantityInput: {
    flex: 2,
    backgroundColor: 'white',
  },
  unitInput: { // Added missing style
    flex: 1,
    backgroundColor: 'white',
  },
  unitPicker: {
    flex: 1,
    backgroundColor: 'white',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: '#e1e8ed',
  },
  unitPickerStyle: {
    height: 56,
  },
  
  // Add Button
  addButtonSection: {
    marginTop: 16, // Reduced from 'auto' to fixed spacing
    paddingTop: 16,
  },
  modernAddButton: {
    paddingVertical: 12, // Increased padding
    borderRadius: 12,
    marginBottom: 8, // Added margin before help text
  },
  
  // Barcode Scanner Styles
  scannerContainer: {
    flex: 1,
    backgroundColor: 'black',
  },
  scannerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: 'rgba(0,0,0,0.8)',
  },
  scannerTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  camera: {
    flex: 1,
  },
  scannerOverlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  scanFrame: {
    width: 250,
    height: 250,
    borderWidth: 2,
    borderColor: 'white',
    borderRadius: 12,
    backgroundColor: 'transparent',
  },
  scanInstructions: {
    color: 'white',
    fontSize: 16,
    marginTop: 24,
    textAlign: 'center',
  },
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
  permissionContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'black',
  },
  permissionText: {
    color: 'white',
    fontSize: 16,
    marginTop: 16,
    textAlign: 'center',
  },
  manualEntryButton: {
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 24,
  },
  manualEntryText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '500',
  },
  helpText: {
    fontSize: 12,
    color: '#8e8e93',
    textAlign: 'center',
    marginTop: 8,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  loadingText: {
    marginLeft: 8,
    color: '#0a7ea4',
    fontSize: 14,
  },
  quickAddChipSelected: {
    backgroundColor: '#0a7ea4',
    borderColor: '#0a7ea4',
  },
  quickAddTextSelected: {
    color: 'white',
  },
  fab: {
    position: 'absolute',
    bottom: 32,
    right: 32,
    backgroundColor: '#0a7ea4',
  },
});
