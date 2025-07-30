import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Recipe } from '../types/Recipe';

// replace static API_BASE with platform-aware endpoints
const PROD_ENDPOINT = process.env.API_BASE || 'https://bo1uqpm579.execute-api.us-east-1.amazonaws.com/Prod/';
const LOCAL_ENDPOINT = 'http://localhost:8000';
const API_BASE = Platform.OS === 'web' ? LOCAL_ENDPOINT : PROD_ENDPOINT;

console.log('API Client: Platform:', Platform.OS);
console.log('API Client: Using API base URL:', API_BASE);
console.log('API Client: PROD_ENDPOINT:', PROD_ENDPOINT);
console.log('API Client: LOCAL_ENDPOINT:', LOCAL_ENDPOINT);

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 10000, // 10 second timeout
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
    const refreshToken = await getItem('refreshToken');
    console.log('RefreshAuthToken: Refresh token exists:', !!refreshToken);
    
    if (!refreshToken || refreshToken === 'null' || refreshToken === 'undefined') {
      console.warn('RefreshAuthToken: No valid refresh token found. Logging out.');
      await logout();
      return null;
    }

    console.log('RefreshAuthToken: Attempting token refresh...');
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken });
    
    console.log('RefreshAuthToken: Response status:', response.status);
    console.log('RefreshAuthToken: Response data keys:', Object.keys(response.data || {}));

    // Handle both possible field names from backend
    const responseData = response.data || {};
    const id_token = responseData.id_token || responseData.IdToken;
    const newRefreshToken = responseData.refresh_token || responseData.RefreshToken;

    if (!id_token) {
      console.error('RefreshAuthToken: No id_token received from refresh endpoint');
      await logout();
      return null;
    }

    console.log('RefreshAuthToken: Received new id_token:', !!id_token);
    console.log('RefreshAuthToken: Received new refresh_token:', !!newRefreshToken);

    // Store new tokens
    if (Platform.OS === 'web') {
      await AsyncStorage.setItem('userToken', id_token);
      if (newRefreshToken && newRefreshToken !== 'null') {
        await AsyncStorage.setItem('refreshToken', newRefreshToken);
      }
    } else {
      await SecureStore.setItemAsync('userToken', id_token);
      if (newRefreshToken && newRefreshToken !== 'null') {
        await SecureStore.setItemAsync('refreshToken', newRefreshToken);
      }
    }

    console.log('RefreshAuthToken: Token refresh successful');
    return id_token;
  } catch (error: any) {
    console.error('RefreshAuthToken: Error refreshing token:', error);
    console.error('RefreshAuthToken: Error response:', error.response?.data);
    console.error('RefreshAuthToken: Error status:', error.response?.status);
    await logout();
    return null;
  }
}

// Attach JWT from secure storage to every request
apiClient.interceptors.request.use(async config => {
  console.log('API Client: Making request to:', config.baseURL + config.url);
  console.log('API Client: Request method:', config.method);
  console.log('API Client: Request data:', JSON.stringify(config.data, null, 2));
  
  const token = await getItem('userToken');
  // Ensure headers object exists
  if (!config.headers) {
    (config as any).headers = {};
  }
  if (token) {
    // Attach JWT token
    (config.headers as any)['Authorization'] = `Bearer ${token}`;
    console.log('API Client: Added Authorization header');
  } else {
    console.log('API Client: No token available for request');
  }
  return config;
}, error => {
  console.error('API Client: Request interceptor error:', error);
  return Promise.reject(error);
});

// Handle token expiration and retry requests
apiClient.interceptors.response.use(
  response => {
    console.log('API Client: Response received from:', response.config.url);
    console.log('API Client: Response status:', response.status);
    console.log('API Client: Response data:', JSON.stringify(response.data, null, 2));
    return response;
  },
  async error => {
    console.error('API Client: Response error:', error.message);
    console.error('API Client: Error config:', error.config?.url);
    console.error('API Client: Error response status:', error.response?.status);
    console.error('API Client: Error response data:', error.response?.data);
    
    // Check if it's a network error
    if (!error.response) {
      console.error('API Client: Network error - no response received');
      return Promise.reject(new Error('Network error: Unable to connect to server'));
    }

    if (error.response?.status === 401) {
      console.warn('API Client: Received 401, attempting token refresh');
      const newToken = await refreshAuthToken();
      if (newToken && newToken !== 'null') {
        console.log('API Client: Token refresh succeeded, retrying request');
        error.config.headers.Authorization = `Bearer ${newToken}`;
        return apiClient.request(error.config);
      } else {
        console.warn('API Client: Token refresh failed or returned null. Request failed.');
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
