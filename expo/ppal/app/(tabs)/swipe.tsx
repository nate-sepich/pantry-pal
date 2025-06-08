import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Swiper from 'react-native-deck-swiper';
import apiClient from '../../src/api/client';
import { useAuth } from '../../src/context/AuthContext';

interface Card {
  id: string;
  title: string;
}

export default function SwipeScreen() {
  const { userToken } = useAuth();
  const [cards, setCards] = useState<Card[]>([]);

  useEffect(() => {
    if (userToken) {
      fetchRecs();
    }
  }, [userToken]);

  const fetchRecs = async () => {
    try {
      const res = await apiClient.get('/recipes/recommendations');
      setCards(res.data.recommendations || []);
    } catch (e) {
      console.error('Failed to fetch recommendations', e);
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
