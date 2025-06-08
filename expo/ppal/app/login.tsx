import React, { useState } from 'react';
import { View, TextInput, Button, Text, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../src/context/AuthContext';

const API_BASE = 'http://localhost:8000/auth';

export default function LoginScreen() {
  const router = useRouter();
  const { signIn } = useAuth();
  const [loading, setLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [mode, setMode] = useState<'login' | 'register' | 'confirm'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');

  const handleRegister = async () => {
    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      const res = await fetch(`${API_BASE}/register`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ username, password, email }),
      });
      if (res.ok) {
        setStatusMsg('Registration initiated. Check your email for the confirmation code.');
        setMode('confirm');
      } else {
        const err = await res.json().catch(() => ({}));
        const msg = err.detail || err.message || JSON.stringify(err) || 'Registration failed';
        setErrorMsg(msg);
      }
    } catch (e: any) {
      setErrorMsg(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    setLoading(true);
    setErrorMsg(''); setStatusMsg('');
    try {
      const res = await fetch(`${API_BASE}/confirm`, {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({ username, confirmation_code: code }),
      });
      if (res.ok) {
        setStatusMsg('Account confirmed! Please login.');
        setMode('login');
      } else {
        const err = await res.json().catch(() => ({}));
        const msg = err.detail || err.message || JSON.stringify(err) || 'Confirmation failed';
        setErrorMsg(msg);
      }
    } catch (e: any) {
      setErrorMsg(String(e));
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async () => {
    setLoading(true);
    setErrorMsg('');
    try {
      await signIn(username, password);
      // Redirect to root; Index will route based on auth state
      router.replace('/');
    } catch (e: any) {
      setErrorMsg(String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      {loading && <ActivityIndicator size="large" />}
      {!!statusMsg && <Text style={styles.status}>{statusMsg}</Text>}
      {!!errorMsg && <Text style={styles.error}>{errorMsg}</Text>}
      <Text style={styles.title}>{mode === 'login' ? 'Login' : mode === 'register' ? 'Register' : 'Confirm Account'}</Text>
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
      {mode === 'confirm' && (
        <TextInput
          style={styles.input}
          placeholder="Confirmation Code"
          value={code}
          onChangeText={setCode}
          keyboardType="number-pad"
        />
      )}
      {mode === 'login' && <Button title="Login" onPress={handleLogin} disabled={loading} />}
      {mode === 'login' && <Button title="Register" onPress={() => setMode('register')} disabled={loading} />}
      {mode === 'register' && <Button title="Sign Up" onPress={handleRegister} disabled={loading} />}
      {mode === 'register' && <Button title="Back to Login" onPress={() => setMode('login')} disabled={loading} />}
      {mode === 'confirm' && <Button title="Confirm" onPress={handleConfirm} disabled={loading} />}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex:1, justifyContent:'center', padding:20 },
  input: { borderWidth:1, borderColor:'#ccc', borderRadius:5, padding:10, marginBottom:10 },
  title: { fontSize:24, marginBottom:20, textAlign:'center' },
  status: { color: 'green', textAlign:'center', marginBottom:10 },
  error: { color: 'red', textAlign:'center', marginBottom:10 },
});