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
      try {
        console.log('AuthProvider: Loading stored tokens...');
        let token: string | null = null;
        let id: string | null = null;

        if (Platform.OS === 'web') {
          token = await AsyncStorage.getItem('userToken');
          id = await AsyncStorage.getItem('userId');
        } else {
          token = await SecureStore.getItemAsync('userToken');
          id = await SecureStore.getItemAsync('userId');
        }

        console.log('AuthProvider: Loaded token exists:', !!token);
        console.log('AuthProvider: Loaded userId exists:', !!id);

        if (token && token !== 'null' && token !== 'undefined') {
          setUserToken(token);
          console.log('AuthProvider: Token set successfully');
        } else {
          console.log('AuthProvider: No valid token found');
        }

        if (id && id !== 'null' && id !== 'undefined') {
          setUserId(id);
          console.log('AuthProvider: UserId set successfully');
        } else {
          console.log('AuthProvider: No valid userId found');
        }
      } catch (error) {
        console.error('AuthProvider: Error loading stored auth data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadToken();
  }, []);

  const signIn = async (username: string, password: string) => {
    try {
      console.log('AuthProvider: Attempting sign in for user:', username);
      const response = await apiClient.post('/auth/login', { username, password });
      
      console.log('AuthProvider: Login response status:', response.status);
      console.log('AuthProvider: Full response data:', JSON.stringify(response.data, null, 2));
      console.log('AuthProvider: Response headers:', response.headers);

      // Check if response exists and has data
      if (!response || !response.data) {
        console.error('AuthProvider: No response data received');
        throw new Error('Authentication failed: No response from server');
      }

      // Handle different possible response structures from backend
      const responseData = response.data || {};
      const id_token = responseData.id_token || responseData.IdToken;
      const refresh_token = responseData.refresh_token || responseData.RefreshToken;

      console.log('AuthProvider: Extracted id_token:', id_token ? 'EXISTS' : 'NULL');
      console.log('AuthProvider: Extracted refresh_token:', refresh_token ? 'EXISTS' : 'NULL');

      if (!id_token) {
        console.error('AuthProvider: No id_token found in response. Available fields:', Object.keys(responseData));
        throw new Error('Authentication failed: No token received from server');
      }

      console.log('AuthProvider: Received id_token:', !!id_token);
      console.log('AuthProvider: Received refresh_token:', !!refresh_token);

      // Store tokens
      if (Platform.OS === 'web') {
        await AsyncStorage.setItem('userToken', id_token);
        if (refresh_token) {
          await AsyncStorage.setItem('refreshToken', refresh_token);
        }
      } else {
        await SecureStore.setItemAsync('userToken', id_token);
        if (refresh_token) {
          await SecureStore.setItemAsync('refreshToken', refresh_token);
        }
      }

      setUserToken(id_token);

      // Extract userId from JWT token
      try {
        const payload = JSON.parse(atob(id_token.split('.')[1]));
        console.log('AuthProvider: JWT payload keys:', Object.keys(payload));
        const userId = payload.sub || payload.user_id || payload.username;
        
        if (userId) {
          setUserId(userId);
          // Store userId separately for easier access
          if (Platform.OS === 'web') {
            await AsyncStorage.setItem('userId', userId);
          } else {
            await SecureStore.setItemAsync('userId', userId);
          }
          console.log('AuthProvider: UserId extracted and stored:', userId);
        } else {
          console.warn('AuthProvider: No userId found in JWT payload');
        }
      } catch (jwtError) {
        console.error('AuthProvider: Error parsing JWT token:', jwtError);
      }

      console.log('AuthProvider: Sign in completed successfully');
    } catch (error: any) {
      console.error('AuthProvider: Sign-in error:', error);
      console.error('AuthProvider: Error response:', error.response?.data);
      console.error('AuthProvider: Error status:', error.response?.status);
      throw error;
    }
  };

  const signOut = async () => {
    try {
      console.log('AuthProvider: Signing out...');
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
      console.log('AuthProvider: Sign out completed');
    } catch (error) {
      console.error('AuthProvider: Error during sign out:', error);
    }
  };

  return (
    <AuthContext.Provider value={{ userToken, userId, loading, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
};


export const useAuth = () => useContext(AuthContext);
