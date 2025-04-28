import axios from 'axios';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';

const API_BASE = process.env.API_BASE || 'https://op14f0voe4.execute-api.us-east-1.amazonaws.com/Prod/';
// const API_BASE = process.env.API_BASE || 'http://localhost:3000';
const apiClient = axios.create({
  baseURL: API_BASE,
});

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
    const { access_token, refresh_token: newRefreshToken } = response.data;

    if (Platform.OS === 'web') {
      await AsyncStorage.setItem('userToken', access_token);
      if (newRefreshToken) {
        await AsyncStorage.setItem('refreshToken', newRefreshToken);
      }
    } else {
      await SecureStore.setItemAsync('userToken', String(access_token)); // Ensure value is a string
      if (newRefreshToken) {
        await SecureStore.setItemAsync('refreshToken', String(newRefreshToken)); // Ensure value is a string
      }
    }

    return access_token;
  } catch (error) {
    console.error('Error refreshing auth token:', error.response?.data || error.message);
    await logout(); // Force logout if token refresh fails
    return null;
  }
}

// Attach JWT from secure storage to every request
apiClient.interceptors.request.use(async config => {
  const token = await getItem('userToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle token expiration and retry requests
apiClient.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const newToken = await refreshAuthToken();
      if (newToken) {
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
