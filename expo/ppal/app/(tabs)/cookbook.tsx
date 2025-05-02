import React, { useState } from 'react';
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
import { Heart, Globe, Clock, Star, ChefHat, Menu, X, ShoppingCart, LucideProps } from 'lucide-react-native'; // Import LucideProps
import pizzaImg from '../assets/images/margherita-pizza.jpg';
import tacosImg from '../assets/images/tacos.png';
import cakeImg from '../assets/images/cake.png';
import curryImg from '../assets/images/curry.png';
import breadImg from '../assets/images/bread.png';

interface Recipe {
  id: string;
  title: string;
  image: string;
  cookTime?: string;
  rating?: number;
  category?: string;
  ingredients?: string[];
}

interface Tab {
  id: 'all' | 'favorites' | 'web' | 'recent' | 'recentlyAdded' | 'bookmarked';
  label: string;
  icon: React.ComponentType<LucideProps>; // Updated to use LucideProps
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
  // State to track the currently active tab
  const [activeTab, setActiveTab] = useState<Tab['id']>('all');

  // State to store the recipes categorized by type
  const [recipes] = useState<Record<'favorites' | 'web' | 'recentlyAdded' | 'bookmarked', Recipe[]>>({
    favorites: [
      { id: '1', title: 'Classic Margherita Pizza', image: 'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimages.ricardocuisine.com%2Fservices%2Frecipes%2Fpizza-1498148703.jpg&f=1&nofb=1&ipt=f58b25b39d225a4a5b665581df8ef35b2b16df1341f7f5efa3d00048ec532daf', cookTime: '25 min', rating: 5, category: 'Italian' },
      { id: '2', title: 'Garlic Lemon Pasta', image: 'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Ffrenchbydesignblog.com%2Fwp-content%2Fuploads%2F2022%2F02%2Fgarlic-lemon-pasta.jpg&f=1&nofb=1&ipt=9b56f9763b77b15be323705d5e75fb0508e8a0c981455d15491b75bc6b8681bb', cookTime: '20 min', rating: 4.5, category: 'Pasta' },
    ],
    web: [
      { id: '3', title: 'Thai Green Curry', image: 'https://via.placeholder.com/300x400', cookTime: '35 min', rating: 4.8, category: 'Asian' },
    ],
    recentlyAdded: [
      { id: '4', title: 'Mushroom Risotto', image: 'https://via.placeholder.com/300x400', cookTime: '40 min', rating: 4.6, category: 'Italian' },
    ],
    bookmarked: [
      { id: '5', title: 'Banana Bread', image: 'https://via.placeholder.com/300x400', cookTime: '60 min', rating: 4.9, category: 'Baking' },
    ],
  });

  // State to store the user's search query from the search input
  const [searchQuery, setSearchQuery] = useState<string>('');

  // State to store the currently selected recipe for the modal preview
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  // State to control the visibility of the modal
  const [modalVisible, setModalVisible] = useState<boolean>(false);

  // State to store pantry recipe suggestions
  const [pantryRecipeSuggestions] = useState<Recipe[]>([]);

  // Handle long press on a recipe card
  const handleLongPress = (recipe: Recipe) => {
    console.log('Preview:', recipe.title);
    setSelectedRecipe(recipe);
    setModalVisible(true);
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
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <ChefHat width={32} height={32} color="white" />
          <Text style={styles.headerTitle}>Cookbook Gallery</Text>
          <TouchableOpacity>
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
      <View style={styles.tabs}>
        {([
          { id: 'all', label: 'All Recipes', icon: Star },
          { id: 'favorites', label: 'Favorites', icon: Heart },
          { id: 'web', label: 'From Web', icon: Globe },
          { id: 'recentlyAdded', label: 'Recently Added', icon: Clock },
          { id: 'bookmarked', label: 'Bookmarked', icon: Star },
        ] as Tab[]).map((tab) => (
          <TouchableOpacity
            key={tab.id}
            style={[
              styles.tab,
              activeTab === tab.id && styles.activeTab,
            ]}
            onPress={() => setActiveTab(tab.id)}
          >
            <tab.icon width={16} height={16} color={activeTab === tab.id ? 'white' : '#475569'} />
            <Text style={[styles.tabText, activeTab === tab.id && styles.activeTabText]}>
              {tab.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.content}>
        {/* Pantry Suggestions Section */}
        {pantryRecipeSuggestions.length > 0 ? (
          <RecipeGallery
            title="Pantry Suggestions"
            icon={ShoppingCart}
            recipeList={pantryRecipeSuggestions}
            onLongPress={handleLongPress}
          />
        ) : (
          <Text style={{ textAlign: 'center', marginVertical: 16 }}>
            Add items to your pantry to get personalized recipe suggestions!
          </Text>
        )}

        {/* Existing RecipeGallery Components */}
        {activeTab === 'all' && (
          <>
            <RecipeGallery title="Favorites" icon={Heart} recipeList={recipes.favorites} onLongPress={handleLongPress} />
            <RecipeGallery title="Pulled from Web" icon={Globe} recipeList={recipes.web} onLongPress={handleLongPress} />
            <RecipeGallery title="Recently Added" icon={Clock} recipeList={recipes.recentlyAdded} onLongPress={handleLongPress} />
            <RecipeGallery title="Bookmarked Recipes" icon={Star} recipeList={recipes.bookmarked} onLongPress={handleLongPress} />
          </>
        )}
        {activeTab === 'favorites' && (
          <RecipeGallery title="Your Favorite Recipes" icon={Heart} recipeList={recipes.favorites} onLongPress={handleLongPress} />
        )}
        {activeTab === 'web' && (
          <RecipeGallery title="Recipes Pulled from the Web" icon={Globe} recipeList={recipes.web} onLongPress={handleLongPress} />
        )}
        {activeTab === 'recentlyAdded' && (
          <RecipeGallery title="Recently Added Recipes" icon={Clock} recipeList={recipes.recentlyAdded} onLongPress={handleLongPress} />
        )}
        {activeTab === 'bookmarked' && (
          <RecipeGallery title="Your Bookmarked Recipes" icon={Star} recipeList={recipes.bookmarked} onLongPress={handleLongPress} />
        )}
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
  tabs: { flexDirection: 'row', justifyContent: 'space-around', paddingVertical: 8, backgroundColor: 'white' },
  tab: { flexDirection: 'row', alignItems: 'center', padding: 8, borderRadius: 8 },
  activeTab: { backgroundColor: '#0d9488' },
  tabText: { marginLeft: 4, color: '#475569' },
  activeTabText: { color: 'white' },
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

