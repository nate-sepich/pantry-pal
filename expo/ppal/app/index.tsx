import { Redirect } from 'expo-router';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useAuth } from '../src/context/AuthContext';

export default function Index() {
  const { userToken, loading } = useAuth();
  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }
  if (!userToken) {
    return <Redirect href="/login" />;
  }
  return <Redirect href="/(tabs)/pantry" />;
}
