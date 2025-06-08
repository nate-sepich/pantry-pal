import React, { useState, useEffect } from 'react';
import { View, Text, FlatList, TouchableOpacity, StyleSheet, ActivityIndicator, Modal, Dimensions } from 'react-native';
import { SafeAreaView, Image } from 'react-native';
import { Card, Button, TextInput as PaperTextInput, FAB, ProgressBar, IconButton, Chip } from 'react-native-paper';
import { MaterialIcons } from '@expo/vector-icons'; // Icons for delete and add actions
import apiClient from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';
import { useRouter, Redirect } from 'expo-router';
import { InventoryItem } from '../../src/types/InventoryItem';
import { Chat, ChatMessage } from '../../src/types/Chat';
import { upsertChat } from '../../src/utils/chatStore';


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
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);
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

  const buildSystemPrompt = (items: InventoryItem[]): string => {
    const lines = [
      'You are PantryPal, an AI culinary assistant.',
      'The user has selected:'
    ];
    for (const it of items) {
      let macro = '';
      if (it.macros) {
        const m = it.macros as any;
        const details = [] as string[];
        if (m.calories) details.push(`calories: ${m.calories}`);
        if (m.protein) details.push(`protein: ${m.protein}g`);
        if (m.carbohydrates) details.push(`carbs: ${m.carbohydrates}g`);
        if (m.fat) details.push(`fat: ${m.fat}g`);
        if (details.length) macro = ' (' + details.join(', ') + ')';
      }
      lines.push(`- ${it.product_name}${it.quantity ? ` x${it.quantity}` : ''}${macro}`);
    }
    if (servings > 1) lines.push(`Scale recipes to ${servings} servings.`);
    if (flavorAdjustments.length) lines.push('Flavor adjustments: ' + flavorAdjustments.join(', '));
    if (removeItems.length) lines.push('Do not use: ' + removeItems.join(', '));
    if (overrides.length) {
      lines.push('Additional notes:');
      for (const note of overrides) lines.push(`- ${note}`);
    }
    lines.push('Provide recipes and suggestions based on these ingredients.');
    lines.push(
      'Reply in Markdown with easy to read sections for Ingredients, Steps and Total Macros.'
    );
    lines.push('Use bullet lists where appropriate and keep the language concise.');
    return lines.join('\n');
  };

  const handleGenerate = async () => {
    const selected = pantryItems.filter(p => selectedItems.includes(p.id));
    const prompt = buildSystemPrompt(selected);
    const sysMsg: ChatMessage = { role: 'system', content: prompt };
    const newId = Math.random().toString(36).slice(2);
    const chat: Chat = { id: newId, title: 'New Chat', messages: [sysMsg], context: selected, updatedAt: new Date().toISOString() };
    await upsertChat(chat);
    await apiClient.put(`/chats/${newId}`, chat);
    router.push({ pathname: '/chat', params: { chatId: newId } });
  };

  const toggleSelect = (id: string) => {
    setSelectedItems(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };
    
  const toggleExpandItem = (id: string) => {
    setExpandedItemId(prev => (prev === id ? null : id));
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
          <Card
            style={[
              styles.card,
              { width: (width - 48) / 2 },
              selectedItems.includes(item.id) && styles.selectedCard,
            ]}
            onPress={() => toggleSelect(item.id)}
          >
            {item.imageUrl ? (
              <Card.Cover source={{ uri: item.imageUrl }} style={styles.cardImage} />
            ) : (
              <View style={styles.cardPlaceholder}>
                <MaterialIcons name="image-not-supported" size={48} color="#ccc" />
              </View>
            )}
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
              <IconButton
                icon="delete"
                iconColor="#ff4d4d"
                size={20}
                onPress={() => handleDeleteItem(item.id)}
             />
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
        <View style={styles.modalOverlay}>
          <View style={styles.addSheet}>
            <Text style={styles.addTitle}>Add Item</Text>
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Item name"
              value={itemName}
              onChangeText={setItemName}
            />
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Quantity"
              keyboardType="numeric"
              value={itemQuantity}
              onChangeText={setItemQuantity}
            />
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
        </View>
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

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#f5f5f5' },
  container: { flexGrow: 1, padding: 16 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  title: { fontSize: 28, fontWeight: '700', textAlign: 'center' },
  logoutButton: { backgroundColor: '#0a7ea4', padding: 8, borderRadius: 8 },
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
  addSheet: { backgroundColor:'#fff', padding:16, borderTopLeftRadius:12, borderTopRightRadius:12 },
  addTitle: { fontSize:20, fontWeight:'bold', marginBottom:12 },
  addInput: { borderWidth:1, borderColor:'#ddd', borderRadius:8, padding:12, marginBottom:12 },
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
  recipeText: { fontSize: 16, lineHeight: 24 },
  macrosContainer: { marginTop: 8 },
  macroRow: { marginBottom: 6 },
  macroText: { fontSize: 12, marginBottom: 2 },
  macroBar: { height: 8, borderRadius: 4 },
});
