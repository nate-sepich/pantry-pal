import React, { useState } from 'react';
import { View, TextInput, Text, StyleSheet, ActivityIndicator, Button } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../src/context/AuthContext';
import apiClient from '../src/api/client';

export default function LoginScreen() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [mode, setMode] = useState<'login' | 'register' | 'confirm' | 'forgot-password' | 'reset-password'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');

  const handleRegister = async () => {
    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      const res = await apiClient.post('/auth/register', { username, password, email });
      setStatusMsg('Registration initiated. Check your email for the confirmation code.');
      setMode('confirm');
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Registration failed';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      await apiClient.post('/auth/confirm', { username, confirmation_code: code });
      setStatusMsg('Account confirmed! Please login.');
      setMode('login');
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Confirmation failed';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!username.trim()) {
      setErrorMsg('Please enter your username');
      return;
    }

    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      await apiClient.post('/auth/forgot-password', { username });
      setStatusMsg('Password reset code sent to your email. Check your inbox.');
      setMode('reset-password');
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Password reset failed';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    if (!username.trim() || !code.trim() || !newPassword.trim()) {
      setErrorMsg('Please fill in all fields');
      return;
    }

    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      await apiClient.post('/auth/reset-password', { 
        username, 
        confirmation_code: code, 
        new_password: newPassword 
      });
      setStatusMsg('Password reset successfully! You can now login.');
      setPassword(''); // Clear old password
      setNewPassword('');
      setCode('');
      setMode('login');
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Password reset failed';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    if (!username.trim() || !password.trim()) {
      setErrorMsg('Please enter both username and password');
      return;
    }

    setLoading(true);
    setErrorMsg('');
    setStatusMsg('Signing in...');
    
    try {
      console.log('LoginScreen: Attempting login...');
      await signIn(username, password);
      console.log('LoginScreen: Login successful, redirecting...');
      setStatusMsg('Login successful! Redirecting...');
      router.replace('/');
    } catch (e: any) {
      console.error('LoginScreen: Login failed:', e);
      setStatusMsg('');
      
      let errorMessage = 'Login failed';
      
      if (e.message?.includes('Network error')) {
        errorMessage = 'Unable to connect to server. Please check your internet connection.';
      } else if (e.message?.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      } else if (e.response?.status === 400) {
        const detail = e.response?.data?.detail || e.message;
        if (detail === 'RESET_PASSWORD_REQUIRED') {
          errorMessage = 'Your password needs to be reset. Redirecting to password reset...';
          setErrorMsg(errorMessage);
          setTimeout(() => {
            setErrorMsg('');
            setStatusMsg('Please reset your password to continue.');
            setMode('forgot-password');
          }, 2000);
          return;
        } else if (detail.includes('new password')) {
          errorMessage = 'Your account requires a new password. Please contact support for assistance.';
        } else if (detail.includes('password has expired') || detail.includes('password reset required')) {
          errorMessage = 'Your password has expired. Please contact support to reset your password.';
        } else if (detail.includes('Multi-factor authentication')) {
          errorMessage = 'Your account has MFA enabled, which is not yet supported. Please contact support.';
        } else if (detail.includes('SMS verification')) {
          errorMessage = 'Your account requires SMS verification, which is not yet supported. Please contact support.';
        } else if (detail.includes('not confirmed')) {
          errorMessage = 'Your account is not confirmed. Please check your email or register a new account.';
        } else if (detail.includes('additional steps')) {
          errorMessage = 'Your account requires additional authentication steps. Please contact support.';
        } else {
          errorMessage = detail;
        }
      } else if (e.response?.status === 401) {
        errorMessage = 'Invalid username or password. Please try again.';
      } else if (e.response?.status === 429) {
        errorMessage = 'Too many login attempts. Please wait a few minutes and try again.';
      } else if (e.response?.status >= 500) {
        errorMessage = 'Server error. Please try again later.';
      } else if (e.response?.data?.detail) {
        errorMessage = e.response.data.detail;
      } else if (e.message) {
        errorMessage = e.message;
      }
      
      console.error('LoginScreen: Displaying error:', errorMessage);
      setErrorMsg(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getTitle = () => {
    switch (mode) {
      case 'login': return 'Login';
      case 'register': return 'Register';
      case 'confirm': return 'Confirm Account';
      case 'forgot-password': return 'Reset Password';
      case 'reset-password': return 'Enter New Password';
      default: return 'Login';
    }
  };

  return (
    <View style={styles.container}>
      {loading && <ActivityIndicator size="large" />}
      {!!statusMsg && <Text style={styles.status}>{statusMsg}</Text>}
      {!!errorMsg && <Text style={styles.error}>{errorMsg}</Text>}
      <Text style={styles.title}>{getTitle()}</Text>
      
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
        autoCapitalize="none"
      />
      
      {mode === 'register' && (
        <TextInput
          style={styles.input}
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          keyboardType="email-address"
          autoCapitalize="none"
        />
      )}
      
      {(mode === 'login' || mode === 'register') && (
        <TextInput
          style={styles.input}
          placeholder="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
        />
      )}
      
      {mode === 'reset-password' && (
        <>
          <TextInput
            style={styles.input}
            placeholder="Confirmation Code"
            value={code}
            onChangeText={setCode}
            keyboardType="number-pad"
          />
          <TextInput
            style={styles.input}
            placeholder="New Password"
            value={newPassword}
            onChangeText={setNewPassword}
            secureTextEntry
          />
        </>
      )}
      
      {mode === 'confirm' && (
        <TextInput
          style={styles.input}
          placeholder="Confirmation Code"
          value={code}
          onChangeText={setCode}
          keyboardType="number-pad"
        />
      )}

      {/* Action Buttons */}
      {mode === 'login' && (
        <>
          <Button title="Login" onPress={handleLogin} disabled={loading} />
          <Button title="Forgot Password?" onPress={() => setMode('forgot-password')} disabled={loading} />
          <Button title="Register" onPress={() => setMode('register')} disabled={loading} />
        </>
      )}
      
      {mode === 'register' && (
        <>
          <Button title="Sign Up" onPress={handleRegister} disabled={loading} />
          <Button title="Back to Login" onPress={() => setMode('login')} disabled={loading} />
        </>
      )}
      
      {mode === 'confirm' && (
        <>
          <Button title="Confirm" onPress={handleConfirm} disabled={loading} />
          <Button title="Back to Login" onPress={() => setMode('login')} disabled={loading} />
        </>
      )}
      
      {mode === 'forgot-password' && (
        <>
          <Button title="Send Reset Code" onPress={handleForgotPassword} disabled={loading} />
          <Button title="Back to Login" onPress={() => setMode('login')} disabled={loading} />
        </>
      )}
      
      {mode === 'reset-password' && (
        <>
          <Button title="Reset Password" onPress={handleResetPassword} disabled={loading} />
          <Button title="Resend Code" onPress={handleForgotPassword} disabled={loading} />
          <Button title="Back to Login" onPress={() => setMode('login')} disabled={loading} />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', padding: 20 },
  input: { borderWidth: 1, borderColor: '#ccc', borderRadius: 5, padding: 10, marginBottom: 10 },
  title: { fontSize: 24, marginBottom: 20, textAlign: 'center' },
  status: { color: 'green', textAlign: 'center', marginBottom: 10 },
  error: { color: 'red', textAlign: 'center', marginBottom: 10 },
});
