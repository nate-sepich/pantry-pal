import React from 'react';
import { SafeAreaView, View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { RecipeGallery } from './cookbook';
import { Globe, Menu } from 'lucide-react-native';

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

const DiscoverPage = () => {
  const router = useRouter();
  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Globe width={32} height={32} color="white" />
          <Text style={styles.headerTitle}>Discover Recipes</Text>
          <TouchableOpacity onPress={() => router.push('/pantry')}>
            <Menu width={24} height={24} color="white" />
          </TouchableOpacity>
        </View>
      </View>
      <RecipeGallery
        title="Discover Recipes"
        icon={Globe}
        recipeList={dummyRecipes}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  header: { backgroundColor: '#0d9488', padding: 16 },
  headerContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerTitle: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  row: { justifyContent: 'space-between' },
});

export default DiscoverPage;
