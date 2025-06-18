import React, { useState, useCallback } from 'react';
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
} from 'react-native';
import { Star, ChefHat, Menu, X, ShoppingCart, LucideProps } from 'lucide-react-native';
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
}


// RecipeCard Component
export const RecipeCard: React.FC<{
  recipe: Recipe;
  onLongPress?: (recipe: Recipe) => void;
}> = ({ recipe, onLongPress }) => (
  <TouchableOpacity
    style={styles.card}
    onLongPress={onLongPress ? () => onLongPress(recipe) : undefined} // Add onLongPress handling
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
  icon: React.ComponentType<LucideProps>;
  recipeList: Recipe[];
  onLongPress?: (recipe: Recipe) => void;
}> = ({ title, icon: Icon, recipeList, onLongPress }) => (
  <View style={styles.gallery}>
    <View style={styles.galleryHeader}>
      <View style={styles.galleryTitle}>
        <Icon width={24} height={24} color="#0d9488" />
        <Text style={styles.galleryTitleText}>{title}</Text>
      </View>
    </View>
    <FlatList
      data={recipeList}
      renderItem={({ item }: { item: Recipe }) => (
        <RecipeCard key={item.id} recipe={item} onLongPress={onLongPress} />
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
  const [importVisible, setImportVisible] = useState<boolean>(false);
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

  // Handle long press on a recipe card
  const handleLongPress = (recipe: Recipe) => {
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
      setImportVisible(false);
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
              <>
                <Image source={{ uri: selectedRecipe.image }} style={styles.modalImage} />
                <Text style={styles.modalTitle}>{selectedRecipe.title}</Text>
                <Text style={styles.modalCategory}>{selectedRecipe.category}</Text>
                <View style={styles.modalDetails}>
                  <View style={styles.modalDetailItem}>
                    <Clock width={16} height={16} />
                    <Text style={styles.modalDetailText}>{selectedRecipe.cookTime}</Text>
                  </View>
                  <View style={styles.modalDetailItem}>
                    <Star width={16} height={16} color="gold" />
                    <Text style={styles.modalDetailText}>{selectedRecipe.rating}</Text>
                  </View>
                </View>
                <TouchableOpacity
                  style={styles.closeButton}
                  onPress={() => setModalVisible(false)}
                >
                  <X width={24} height={24} color="white" />
                </TouchableOpacity>
              </>
            )}
          </View>
        </Pressable>
      </Modal>
      <Modal visible={importVisible} transparent animationType="slide" onRequestClose={() => setImportVisible(false)}>
        <Pressable style={styles.modalOverlay} onPress={() => setImportVisible(false)}>
          <View style={styles.modalContent}>
            <Text style={{ marginBottom: 8 }}>Paste recipe URL</Text>
            <TextInput style={styles.searchInput} value={importUrl} onChangeText={setImportUrl} autoCapitalize="none" />
            <TouchableOpacity style={[styles.closeButton,{position:'relative', marginTop:12}]} onPress={handleImport}>
              <Text style={{color:'white'}}>Import</Text>
            </TouchableOpacity>
          </View>
        </Pressable>
      </Modal>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <ChefHat width={32} height={32} color="white" />
          <Text style={styles.headerTitle}>Cookbook Gallery</Text>
          <TouchableOpacity onPress={() => setImportVisible(true)}>
            <Menu width={24} height={24} color="white" />
          </TouchableOpacity>
        </View>
        <TextInput
          style={styles.searchInput}
          placeholder="Search recipes, ingredients, categories..."
          placeholderTextColor="#94a3b8"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>
      <View style={styles.content}>
        <RecipeGallery
          title="My Recipes"
          icon={Star}
          recipeList={recipes}
          onLongPress={handleLongPress}
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
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#fff',
    elevation: 2,
  },
  cardImage: { width: '100%', height: 120 },
  cardContent: { padding: 8 },
  cardTitle: { fontSize: 16, fontWeight: '600' },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0, 0, 0, 0.5)', justifyContent: 'center', alignItems: 'center' },
  modalContent: {
    width: '90%',
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  modalImage: { width: '100%', height: 200, borderRadius: 8, marginBottom: 16 },
  modalTitle: { fontSize: 18, fontWeight: 'bold', color: '#1e293b', marginBottom: 8 },
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
});

