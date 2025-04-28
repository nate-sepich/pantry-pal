import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import apiClient from '../api/client';

interface AuthContextData {
  userToken: string | null;
  userId: string | null;
  loading: boolean;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextData>({} as AuthContextData);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [userToken, setUserToken] = useState<string | null>(null);
  const [userId, setUserId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadToken = async () => {
      let token: string | null = null;
      let id: string | null = null;

      if (Platform.OS === 'web') {
        token = await AsyncStorage.getItem('userToken');
        id = await AsyncStorage.getItem('userId'); // Retrieve userId
      } else {
        token = await SecureStore.getItemAsync('userToken');
        id = await SecureStore.getItemAsync('userId'); // Retrieve userId
      }

      if (token) setUserToken(token);
      if (id) setUserId(id); // Set userId in state
      setLoading(false);
    };

    loadToken();
  }, []);

  const signIn = async (username: string, password: string) => {
    try {
      const response = await apiClient.post('/auth/login', { username, password });
      const { access_token, id } = response.data;

      if (Platform.OS === 'web') {
        await AsyncStorage.setItem('userToken', access_token);
        await AsyncStorage.setItem('userId', id); // Store userId
      } else {
        await SecureStore.setItemAsync('userToken', access_token);
        await SecureStore.setItemAsync('userId', id); // Store userId
      }

      setUserToken(access_token);
      setUserId(id); // Set userId in state
    } catch (error) {
      console.error('Error during sign-in:', error.response?.data || error.message);
    }
  };

  const signOut = async () => {
    if (Platform.OS === 'web') {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('userId');
    } else {
      await SecureStore.deleteItemAsync('userToken');
      await SecureStore.deleteItemAsync('userId');
    }
    setUserToken(null);
    setUserId(null);
  };

  return (
    <AuthContext.Provider value={{ userToken, userId, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
