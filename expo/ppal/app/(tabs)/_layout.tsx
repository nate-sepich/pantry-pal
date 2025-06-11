import React from 'react';
import { Tabs } from 'expo-router';
import { ShoppingCart, ChefHat, Globe } from 'lucide-react-native';

export default function TabsLayout() {
  return (
    <Tabs screenOptions={{ headerShown: false }}>
      <Tabs.Screen
        name="pantry"
        options={{
          title: 'Pantry',
          tabBarIcon: ({ color, size }) => <ShoppingCart width={size} height={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="cookbook"
        options={{
          title: 'Cookbook',
          tabBarIcon: ({ color, size }) => <ChefHat width={size} height={size} color={color} />,
        }}
      />
      <Tabs.Screen
        name="discover"
        options={{
          title: 'Discover',
          tabBarIcon: ({ color, size }) => <Globe width={size} height={size} color={color} />,
        }}
      />
    </Tabs>
  );
}
