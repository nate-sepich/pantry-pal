import React from 'react';
import { SafeAreaView, StyleSheet } from 'react-native';
import { RecipeGallery } from './cookbook'; // Import RecipeGallery
import { Globe } from 'lucide-react-native'; // Import Globe icon

interface Recipe {
  id: string;
  title: string;
  image: string;
}

const dummyRecipes: Recipe[] = [
  { id: '1', title: 'Spicy Tofu Noodles', image: 'https://via.placeholder.com/300x200' },
  { id: '2', title: 'Avocado Toast',      image: 'https://via.placeholder.com/300x200' },
  { id: '3', title: 'Berry Smoothie',     image: 'https://via.placeholder.com/300x200' },
  { id: '4', title: 'Vegan Burger',       image: 'https://via.placeholder.com/300x200' },
];

const DiscoverPage = () => (
  <SafeAreaView style={{ flex: 1, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
    <RecipeGallery
      title="Discover Recipes"
      icon={Globe}
      recipeList={dummyRecipes}
    />
  </SafeAreaView>
);

const styles = StyleSheet.create({
  row: { justifyContent: 'space-between' },
});

export default DiscoverPage;
