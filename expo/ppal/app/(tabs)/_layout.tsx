import React from 'react';
import { Tabs } from 'expo-router';
import { ShoppingCart } from 'lucide-react-native';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen name="pantry" options={{ title: 'Pantry' }} />
      <Tabs.Screen name="cookbook" options={{ title: 'Cookbook' }} />
      <Tabs.Screen name="discover" options={{ title: 'Discover' }} />
    </Tabs>
  );
}
