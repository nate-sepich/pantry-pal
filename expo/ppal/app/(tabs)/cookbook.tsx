import React, { useState, useCallback } from 'react';
import { Keyboard } from 'react-native';
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  Image,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Modal,
  Pressable,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect } from 'expo-router';
import { cookbookApi } from '../../src/api/client';
import { Recipe as ApiRecipe } from '../../src/types/Recipe';

interface Recipe {
  id: string;
  title: string;
  image: string;
  cookTime?: string;
  rating?: number;
  category?: string;
  ingredients?: string[];
  instructions?: string;
}

// RecipeCard Component
export const RecipeCard: React.FC<{
  recipe: Recipe;
  onPress?: (recipe: Recipe) => void;
}> = ({ recipe, onPress }) => (
  <TouchableOpacity
    style={styles.card}
    onPress={onPress ? () => onPress(recipe) : undefined}
  >
    <Image source={{ uri: recipe.image }} style={styles.cardImage} />
    <View style={styles.cardContent}>
      <Text style={styles.cardTitle} numberOfLines={1}>
        {recipe.title}
      </Text>
    </View>
  </TouchableOpacity>
);

// Props for RecipeGallery
export const RecipeGallery: React.FC<{
  title: string;
  recipeList: Recipe[];
  onPress?: (recipe: Recipe) => void;
}> = ({ title, recipeList, onPress }) => (
  <View style={styles.gallery}>
    <View style={styles.galleryHeader}>
      <View style={styles.galleryTitle}>
        <Ionicons name="star-outline" size={24} color="#0d9488" />
        <Text style={styles.galleryTitleText}>{title}</Text>
      </View>
    </View>
    <FlatList
      data={recipeList}
      renderItem={({ item }: { item: Recipe }) => (
        <RecipeCard key={item.id} recipe={item} onPress={onPress} />
      )}
      keyExtractor={(item: Recipe) => item.id.toString()}
      numColumns={2}
      columnWrapperStyle={styles.row}
      showsVerticalScrollIndicator={false}
    />
  </View>
);

export default function CookbookPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);

  // State to store the user's search query from the search input
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [importUrl, setImportUrl] = useState<string>('');

  const fetchRecipes = useCallback(async () => {
    try {
      const data = await cookbookApi.getRecipes();
      const mapped = data.map((r: ApiRecipe) => ({
        id: r.id,
        title: r.name,
        image: r.image_url || 'https://via.placeholder.com/300x400',
        ingredients: r.ingredients || [],
      }));
      setRecipes(mapped);
    } catch (e) {
      console.error('Failed to load recipes', e);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      fetchRecipes();
    }, [fetchRecipes])
  );

  // Open detail modal when a recipe card is pressed
  const handleCardPress = (recipe: Recipe) => {
    console.log('Preview:', recipe.title);
    setSelectedRecipe(recipe);
    setModalVisible(true);
  };

  const handleImport = async () => {
    if (!importUrl) return;
    try {
      const newRec = await cookbookApi.importRecipe(importUrl);
      setRecipes([...recipes, { id: newRec.id, title: newRec.name, image: newRec.image_url || 'https://via.placeholder.com/300x400', ingredients: newRec.ingredients || [] }]);
      setImportUrl('');
      Keyboard.dismiss();
      // import modal not used, only clear URL input
    } catch (e) {
      console.error('Import failed', e);
    }
  };

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
      <Modal
        visible={modalVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={() => setModalVisible(false)}
      >
        <Pressable style={styles.modalOverlay} onPress={() => setModalVisible(false)}>
          <View style={styles.modalContent}>
            {selectedRecipe && (
              <ScrollView>
                <Image source={{ uri: selectedRecipe.image }} style={styles.modalImage} />
                <Text style={styles.modalTitle}>{selectedRecipe.title}</Text>
                {selectedRecipe.ingredients?.length ? (
                  <View style={{ marginBottom: 16 }}>
                    <Text style={styles.sectionHeader}>Ingredients</Text>
                    {selectedRecipe.ingredients.map((ing, idx) => (
                      <Text key={idx} style={styles.bodyText}>• {ing}</Text>
                    ))}
                  </View>
                ) : null}
                {selectedRecipe.instructions ? (
                  <View style={{ marginBottom: 16 }}>
                    <Text style={styles.sectionHeader}>Instructions</Text>
                    <Text style={styles.bodyText}>{selectedRecipe.instructions}</Text>
                  </View>
                ) : null}
                <TouchableOpacity
                  style={[styles.closeButton, { alignSelf: 'flex-end' }]}
                  onPress={() => setModalVisible(false)}
                >
                  <Ionicons name="close" size={24} color="white" />
                </TouchableOpacity>
              </ScrollView>
            )}
          </View>
        </Pressable>
      </Modal>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Ionicons name="restaurant-outline" size={32} color="white" />
          <Text style={styles.headerTitle}>Cookbook Gallery</Text>
        </View>
        <TextInput
          style={styles.searchInput}
          placeholder="Search recipes, ingredients, categories..."
          placeholderTextColor="#94a3b8"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <View style={styles.importRow}>
          <TextInput
            style={[styles.searchInput, { flex: 1, marginTop: 8 }]}
            placeholder="Paste recipe URL"
            placeholderTextColor="#94a3b8"
            value={importUrl}
            autoCapitalize="none"
            onChangeText={setImportUrl}
          />
          <TouchableOpacity style={styles.importButton} onPress={handleImport}>
            <Text style={{ color: 'white' }}>Import</Text>
          </TouchableOpacity>
        </View>
      </View>
      <View style={styles.content}>
        <RecipeGallery
          title="My Recipes"
          recipeList={recipes}
          onPress={handleCardPress}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { backgroundColor: '#0d9488', padding: 16 },
  headerContent: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  headerTitle: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  searchInput: {
    marginTop: 16,
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 12,
    fontSize: 14,
    color: '#1e293b',
  },
  content: { flex: 1, padding: 16 },
  gallery: { marginBottom: 24 },
  galleryHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  galleryTitle: { flexDirection: 'row', alignItems: 'center' },
  galleryTitleText: { marginLeft: 8, fontSize: 18, fontWeight: 'bold', color: '#0f172a' },
  row: { justifyContent: 'space-between' },
  card: {
    flex: 1,
    margin: 8,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#fff',
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 4,
    elevation: 3,
  },
  cardImage: { width: '100%', height: 120 },
  cardContent: { padding: 12 },
  cardTitle: { fontSize: 20, fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: {
    width: '90%',
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  modalImage: { width: '100%', height: 200, borderRadius: 8, marginBottom: 16 },
  modalTitle: { fontSize: 20, fontWeight: '600', color: '#1e293b', marginBottom: 8 },
  modalCategory: { fontSize: 14, color: '#94a3b8', marginBottom: 16 },
  modalDetails: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', marginBottom: 16 },
  modalDetailItem: { flexDirection: 'row', alignItems: 'center' },
  modalDetailText: { marginLeft: 4, fontSize: 12, color: '#475569' },
  closeButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#0d9488',
    borderRadius: 16,
    padding: 8,
  },
  importRow: { flexDirection: 'row', alignItems: 'center' },
  importButton: {
    backgroundColor: '#0d9488',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    marginLeft: 8,
  },
  sectionHeader: { fontSize: 20, fontWeight: '600', marginBottom: 8 },
  bodyText: { fontSize: 14, marginBottom: 4 },
});

