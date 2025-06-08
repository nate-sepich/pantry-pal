import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Swiper from 'react-native-deck-swiper';
import apiClient from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';
import sampleRecipes from '../../assets/sampleRecipes.json';
import { RecipeCard } from '../../src/types/RecipeCard';

export default function SwipeScreen() {
  const { userToken } = useAuth();
  const [cards, setCards] = useState<RecipeCard[]>(sampleRecipes as RecipeCard[]);

  useEffect(() => {
    if (userToken) {
      fetchRecs();
    } else {
      // fall back to bundled sample data when unauthenticated
      setCards(sampleRecipes as RecipeCard[]);
    }
  }, [userToken]);

  const fetchRecs = async () => {
    try {
      const res = await apiClient.get('/recipes/recommendations');
      setCards(res.data.recommendations || (sampleRecipes as RecipeCard[]));
    } catch (e) {
      console.warn('Failed to fetch recommendations, using sample data');
      setCards(sampleRecipes as RecipeCard[]);
    }
  };

  const likeCard = async (index: number) => {
    const card = cards[index];
    if (!card) return;
    try {
      await apiClient.post(`/recipes/${card.id}/like`);
    } catch (e) {
      console.error('Failed to like recipe', e);
    }
  };

  return (
    <View style={{ flex: 1 }}>
      {cards.length > 0 ? (
        <Swiper
          cards={cards}
          renderCard={(card) => (
            <View style={styles.card}>
              <Text style={styles.text}>{card.title}</Text>
            </View>
          )}
          onSwipedRight={likeCard}
          stackSize={3}
          cardIndex={0}
          backgroundColor="#f0f0f0"
        />
      ) : (
        <Text style={{ textAlign: 'center', marginTop: 40 }}>No recipes</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 0.8,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 16,
    borderColor: '#ccc',
    borderWidth: 1,
  },
  text: {
    fontSize: 18,
    textAlign: 'center',
  },
});
