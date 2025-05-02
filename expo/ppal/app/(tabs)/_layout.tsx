import React from 'react';
import { Tabs } from 'expo-router';
import { Globe, ChefHat, ShoppingCart } from 'lucide-react-native';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen
        name="cookbook"
        options={{
          title: 'Cookbook',
          tabBarIcon: ({ color, size }: { color: string; size: number }) => (
            <ChefHat width={size} height={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="discover"
        options={{
          title: 'Discover',
          tabBarIcon: ({ color, size }: { color: string; size: number }) => (
            <Globe width={size} height={size} color={color} />
          ),
        }}
      />
      <Tabs.Screen
        name="pantry"
        options={{
          title: 'Pantry',
          tabBarIcon: ({ color, size }: { color: string; size: number }) => (
            <ShoppingCart width={size} height={size} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}
