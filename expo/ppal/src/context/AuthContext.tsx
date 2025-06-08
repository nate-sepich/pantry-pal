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
      const { id_token, refresh_token } = response.data;

      // Store id_token and refresh_token
      if (Platform.OS === 'web') {
        await AsyncStorage.setItem('userToken', id_token);
        if (refresh_token) await AsyncStorage.setItem('refreshToken', refresh_token);
      } else {
        await SecureStore.setItemAsync('userToken', id_token);
        if (refresh_token) await SecureStore.setItemAsync('refreshToken', refresh_token);
      }

      setUserToken(id_token);
      const payload = JSON.parse(atob(id_token.split('.')[1]));
      setUserId(payload.sub);

    } catch (error: any) {
      console.error('Error during sign-in:', error.response?.data || error.message);
      throw error;
    }
  };

  const signOut = async () => {
    if (Platform.OS === 'web') {
      await AsyncStorage.removeItem('userToken');
      await AsyncStorage.removeItem('refreshToken');
      await AsyncStorage.removeItem('userId');
    } else {
      await SecureStore.deleteItemAsync('userToken');
      await SecureStore.deleteItemAsync('refreshToken');
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
