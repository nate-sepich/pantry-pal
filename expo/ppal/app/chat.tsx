import React, { useState, useEffect } from 'react';
import { View, TextInput, FlatList, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { Appbar, Button } from 'react-native-paper';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Markdown from 'react-native-markdown-display';
import apiClient from '../src/api/client';
import { ChatMessage, Chat } from '../src/types/Chat';
import { getChat, upsertChat } from '../src/utils/chatStore';

function formatRecipeMarkdown(recipe: any): string {
  let out = `# ${recipe.title || 'Recipe'}\n\n`;

  if (Array.isArray(recipe.ingredients)) {
    out += '## Ingredients\n';
    for (const ing of recipe.ingredients) {
      if (typeof ing === 'string') {
        out += `- ${ing}\n`;
      } else if (ing.name && ing.quantity) {
        out += `- ${ing.name}: ${ing.quantity}\n`;
      } else if (ing.item && ing.qty) {
        out += `- ${ing.item}: ${ing.qty}\n`;
      } else {
        out += `- ${JSON.stringify(ing)}\n`;
      }
    }
    out += '\n';
  }

  if (Array.isArray(recipe.steps)) {
    out += '## Steps\n';
    recipe.steps.forEach((step: string, idx: number) => {
      out += `${idx + 1}. ${step}\n`;
    });
    out += '\n';
  } else if (recipe.steps) {
    out += `## Steps\n${recipe.steps}\n`;
  }

  if (recipe.total_macros) {
    out += '## Total Macros\n';
    for (const [k, v] of Object.entries(recipe.total_macros)) {
      out += `- ${k}: ${v}\n`;
    }
  }

  return out;
}

export default function ChatScreen() {
  const router = useRouter();
  const { recipe, chatId, system } = useLocalSearchParams<{ recipe?: string; chatId?: string; system?: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [title, setTitle] = useState('Chat');
  const [id, setId] = useState<string>('');
  const [input, setInput] = useState('');

  useEffect(() => {
    const init = async () => {
      if (system) {
        const initial: ChatMessage = { role: 'system', content: system as string };
        const newId = Math.random().toString(36).slice(2);
        const newChat: Chat = { id: newId, title: 'New Chat', messages: [initial], updatedAt: new Date().toISOString() };
        await upsertChat(newChat);
        await apiClient.post('/chats', {
          id: newId,
          title: newChat.title,
          updatedAt: newChat.updatedAt,
          length: newChat.messages.length,
        });
        setMessages(newChat.messages);
        setTitle(newChat.title);
        setId(newId);
      } else if (recipe) {
        try {
          const obj = JSON.parse(recipe as string);
          const initial: ChatMessage = { role: 'assistant', content: formatRecipeMarkdown(obj) };
          const newId = Math.random().toString(36).slice(2);
          const newChat: Chat = { id: newId, title: obj.title || 'Recipe', messages: [initial], updatedAt: new Date().toISOString() };
          await upsertChat(newChat);
          await apiClient.post('/chats', {
            id: newId,
            title: newChat.title,
            updatedAt: newChat.updatedAt,
            length: newChat.messages.length,
          });
          setMessages(newChat.messages);
          setTitle(newChat.title);
          setId(newId);
        } catch {
          const initial: ChatMessage = { role: 'assistant', content: recipe as string };
          const newId = Math.random().toString(36).slice(2);
          const newChat: Chat = { id: newId, title: 'Recipe', messages: [initial], updatedAt: new Date().toISOString() };
          await upsertChat(newChat);
          await apiClient.post('/chats', {
            id: newId,
            title: newChat.title,
            updatedAt: newChat.updatedAt,
            length: newChat.messages.length,
          });
          setMessages(newChat.messages);
          setTitle(newChat.title);
          setId(newId);
        }
      } else if (chatId) {
        const existing = await getChat(chatId as string);
        if (existing) {
          setMessages(existing.messages);
          setTitle(existing.title);
          setId(existing.id);
        }
      }
    };
    init();
  }, [system, recipe, chatId]);

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setInput('');
    try {
      const res = await apiClient.post('/openai/llm_chat', { messages: newMsgs });
      const reply = res.data.response || '';
      const finalMsgs = [...newMsgs, { role: 'assistant', content: reply } as ChatMessage];
      setMessages(finalMsgs);
      const updated: Chat = { id, title, messages: finalMsgs, updatedAt: new Date().toISOString() };
      await upsertChat(updated);
      await apiClient.post('/chats', {
        id: updated.id,
        title: updated.title,
        updatedAt: updated.updatedAt,
        length: updated.messages.length,
      });
    } catch (e: any) {
      const errMsgs = [...newMsgs, { role: 'assistant', content: 'Error: ' + String(e) } as ChatMessage];
      setMessages(errMsgs);
    }
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={title} />
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
          onSubmitEditing={send}
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
