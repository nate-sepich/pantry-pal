import { Redirect } from 'expo-router';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useAuth } from '../src/context/AuthContext';

export default function Index() {
  const { userToken, loading } = useAuth();
  
  console.log('Index: Loading state:', loading);
  console.log('Index: UserToken exists:', !!userToken);
  
  if (loading) {
    console.log('Index: Showing loading screen');
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }
  
  if (!userToken || userToken === 'null') {
    console.log('Index: No valid token, redirecting to login');
    return <Redirect href="/login" />;
  }
  
  console.log('Index: Valid token found, redirecting to pantry');
  return <Redirect href="/(tabs)/pantry" />;
}
