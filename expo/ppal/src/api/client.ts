import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Recipe } from '../types/Recipe';

// replace static API_BASE with platform-aware endpoints
const PROD_ENDPOINT = process.env.API_BASE || 'https://bo1uqpm579.execute-api.us-east-1.amazonaws.com/Prod/';
const LOCAL_ENDPOINT = 'http://localhost:8000';
const API_BASE = Platform.OS === 'web' ? LOCAL_ENDPOINT : PROD_ENDPOINT;
const apiClient = axios.create({
  baseURL: API_BASE,
});

export const cookbookApi = {
  async getRecipes(): Promise<Recipe[]> {
    const res = await apiClient.get<Recipe[]>('/cookbook');
    return res.data;
  },
  async addRecipe(recipe: Recipe): Promise<Recipe> {
    const res = await apiClient.post<Recipe>('/cookbook', recipe);
    return res.data;
  },
  async importRecipe(url: string): Promise<Recipe> {
    const res = await apiClient.post<Recipe>('/cookbook/import', { url });
    return res.data;
  },
  async deleteRecipe(id: string) {
    return apiClient.delete(`/cookbook/${id}`);
  },
};

// Helper to get stored value on native or web
async function getItem(key: string): Promise<string | null> {
  if (Platform.OS === 'web') {
    return AsyncStorage.getItem(key);
  }
  return SecureStore.getItemAsync(key);
}

// Logout by clearing the stored token
export async function logout() {
  if (Platform.OS === 'web') {
    await AsyncStorage.removeItem('userToken');
    await AsyncStorage.removeItem('refreshToken');
  } else {
    await SecureStore.deleteItemAsync('userToken');
    await SecureStore.deleteItemAsync('refreshToken');
  }
}

// Refresh the auth token
export async function refreshAuthToken(): Promise<string | null> {
  try {
    const refreshToken = await getItem('refreshToken'); // Retrieve the refresh token
    if (!refreshToken) {
      console.warn('No refresh token found. Logging out.');
      await logout(); // Ensure logout is called if no refresh token is found
      return null;
    }

    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    const { id_token, refresh_token: newRefreshToken } = response.data;

    // Store new ID token for authentication
    if (Platform.OS === 'web') {
      await AsyncStorage.setItem('userToken', id_token);
      if (newRefreshToken) {
        await AsyncStorage.setItem('refreshToken', newRefreshToken);
      }
    } else {
      await SecureStore.setItemAsync('userToken', id_token);
      if (newRefreshToken) {
        await SecureStore.setItemAsync('refreshToken', newRefreshToken);
      }
    }

    return id_token;
  } catch (error: any) {
    console.error('Error refreshing auth token:', error.response?.data || error.message);
    await logout(); // Force logout if token refresh fails
    return null;
  }
}

// Attach JWT from secure storage to every request
apiClient.interceptors.request.use(async config => {
  const token = await getItem('userToken');
  // Ensure headers object exists
  if (!config.headers) {
    (config as any).headers = {};
  }
  if (token) {
    // Attach JWT token
    (config.headers as any)['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration and retry requests
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      console.warn('API Request received 401, attempting token refresh');
      const newToken = await refreshAuthToken();
      if (newToken) {
        console.log('Token refresh succeeded, retrying with new token:', newToken);
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return apiClient.request(error.config);
      } else {
        console.warn('Token refresh failed. Forcing logout.');
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
