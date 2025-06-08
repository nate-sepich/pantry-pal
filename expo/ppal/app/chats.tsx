import React, { useState, useEffect } from 'react';
import { View, TextInput, FlatList, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { Appbar, Button } from 'react-native-paper';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Markdown from 'react-native-markdown-display';
import apiClient from '../src/api/client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatScreen() {
  const router = useRouter();
  const { recipe } = useLocalSearchParams<{ recipe?: string }>();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  useEffect(() => {
    if (recipe) {
      try {
        const obj = JSON.parse(recipe as string);
        setMessages([{ role: 'assistant', content: '```json\n' + JSON.stringify(obj, null, 2) + '\n```' }]);
      } catch {
        setMessages([{ role: 'assistant', content: recipe as string }]);
      }
    }
  }, [recipe]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg = { role: 'user', content: input.trim() } as Message;
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    try {
      const res = await apiClient.post('/openai/llm_chat', { prompt: input.trim() });
      const reply = res.data.response || '';
      setMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (e: any) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + String(e) }]);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title="Chat" />
      </Appbar.Header>
      <FlatList
        data={messages}
        keyExtractor={(_, idx) => idx.toString()}
        renderItem={({ item }) => (
          <View style={item.role === 'user' ? styles.userBubble : styles.botBubble}>
            <Markdown>{item.content}</Markdown>
          </View>
        )}
        contentContainerStyle={{ padding: 16 }}
      />
      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Send a message"
        />
        <Button mode="contained" onPress={send} style={styles.sendButton}>Send</Button>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#dcf8c6',
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
    maxWidth: '80%'
  },
  botBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#eee',
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
    maxWidth: '80%'
  },
  inputRow: {
    flexDirection: 'row',
    padding: 8,
    borderTopWidth: 1,
    borderColor: '#ddd',
    alignItems: 'center'
  },
  input: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginRight: 8
  },
  sendButton: { }
});
