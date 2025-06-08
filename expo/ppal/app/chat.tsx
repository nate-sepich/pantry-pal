import React, { useState, useEffect } from 'react';
import { View, TextInput, FlatList, KeyboardAvoidingView, Platform, StyleSheet, Text, Modal, Alert } from 'react-native';
import { Appbar, Button, List, IconButton, ProgressBar, TextInput as PaperTextInput } from 'react-native-paper';
import { useRouter, useLocalSearchParams } from 'expo-router';
import Markdown from 'react-native-markdown-display';
import apiClient from '../src/api/client';
import { ChatMessage, Chat } from '../src/types/Chat';
import { getChat, upsertChat, removeChat } from '../src/utils/chatStore';

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

function parseRecipeText(text: string): { markdown: string; title?: string } {
  try {
    const obj = JSON.parse(text);
    return { markdown: formatRecipeMarkdown(obj), title: obj.title };
  } catch {
    return { markdown: text };
  }
}

function renderMacroBars(macros: any) {
  if (!macros) return null;
  const data = [
    { label: 'Protein', value: Number(macros.protein || 0) },
    { label: 'Carbs', value: Number(macros.carbohydrates || 0) },
    { label: 'Fat', value: Number(macros.fat || 0) },
    { label: 'Sugar', value: Number(macros.sugar || 0) },
  ];
  const maxVal = Math.max(...data.map(d => d.value), 1);
  return data.map(d => (
    <View key={d.label} style={styles.macroRow}>
      <Text style={styles.macroText}>{`${d.label}: ${d.value}g`}</Text>
      <ProgressBar progress={d.value / maxVal} color="#0a7ea4" style={styles.macroBar} />
    </View>
  ));
}

function buildSystemPrompt(items: any[]): string {
  const lines = [
    'You are PantryPal, an AI culinary assistant.',
    'The user has selected:'
  ];
  for (const it of items) {
    let macro = '';
    if (it.macros) {
      const m = it.macros as any;
      const details: string[] = [];
      if (m.calories) details.push(`calories: ${m.calories}`);
      if (m.protein) details.push(`protein: ${m.protein}g`);
      if (m.carbohydrates) details.push(`carbs: ${m.carbohydrates}g`);
      if (m.fat) details.push(`fat: ${m.fat}g`);
      if (details.length) macro = ' (' + details.join(', ') + ')';
    }
    lines.push(`- ${it.product_name}${it.quantity ? ` x${it.quantity}` : ''}${macro}`);
  }
  lines.push('Provide recipes and suggestions based on these ingredients.');
  lines.push('Reply in Markdown with easy to read sections for Ingredients, Steps and Total Macros.');
  lines.push('Use bullet lists where appropriate and keep the language concise.');
  return lines.join('\n');
}

async function fetchMacros(name: string) {
  try {
    const res = await apiClient.get('/macros/item', { params: { item_name: name } });
    return res.data;
  } catch {
    return undefined;
  }
}

export default function ChatScreen() {
  const router = useRouter();
  const { recipe, chatId } = useLocalSearchParams<{ recipe?: string; chatId?: string }>();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [title, setTitle] = useState('Chat');
  const [id, setId] = useState<string>('');
  const [context, setContext] = useState<any[]>([]);
  const [showCtx, setShowCtx] = useState(false);
  const [addModalVisible, setAddModalVisible] = useState(false);
  const [newItemName, setNewItemName] = useState('');
  const [newItemQty, setNewItemQty] = useState('');
  const [input, setInput] = useState('');

  useEffect(() => {
    const init = async () => {
      if (chatId) {
        let existing = await getChat(chatId as string);
        if (!existing) {
          try {
            const res = await apiClient.get(`/chats/${chatId}`);
            existing = res.data as Chat;
            await upsertChat(existing);
          } catch {}
        }
        if (existing) {
          setMessages(existing.messages);
          setTitle(existing.title);
          setId(existing.id);
          setContext(existing.context || []);
          if (existing.messages.length === 1 && existing.messages[0].role === 'system') {
            await regenerateChat(existing.context || [], existing.id);
          }
        }
      } else if (recipe) {
        try {
          const obj = JSON.parse(recipe as string);
          const initial: ChatMessage = { role: 'assistant', content: formatRecipeMarkdown(obj) };
          const newId = Math.random().toString(36).slice(2);
          const newChat: Chat = { id: newId, title: obj.title || 'Recipe', messages: [initial], context: [], updatedAt: new Date().toISOString() };
          await upsertChat(newChat);
          await apiClient.put(`/chats/${newId}`, newChat);
          setMessages(newChat.messages);
          setTitle(newChat.title);
          setId(newId);
        } catch {
          const initial: ChatMessage = { role: 'assistant', content: recipe as string };
          const newId = Math.random().toString(36).slice(2);
          const newChat: Chat = { id: newId, title: 'Recipe', messages: [initial], context: [], updatedAt: new Date().toISOString() };
          await upsertChat(newChat);
          await apiClient.put(`/chats/${newId}`, newChat);
          setMessages(newChat.messages);
          setTitle(newChat.title);
          setId(newId);
        }
      }
    };
    init();
  }, [chatId, recipe]);

  const regenerateChat = async (items: any[], chatIdOverride?: string) => {
    const currentId = chatIdOverride || id;
    if (!currentId) return;
    const prompt = buildSystemPrompt(items);
    const sysMsg: ChatMessage = { role: 'system', content: prompt };
    const userMsg: ChatMessage = { role: 'user', content: 'Generate a recipe using the provided items.' };
    const res = await apiClient.post('/openai/llm_chat', { messages: [sysMsg, userMsg] });
    const raw = res.data.response || '';
    const parsed = parseRecipeText(raw);
    const assistant: ChatMessage = { role: 'assistant', content: parsed.markdown };
    const newMsgs = [sysMsg, assistant];
    setMessages(newMsgs);
    setContext(items);
    const updated: Chat = { id: currentId, title, messages: newMsgs, context: items, updatedAt: new Date().toISOString() };
    await upsertChat(updated);
    await apiClient.put(`/chats/${updated.id}`, updated);
  };

  const removeItem = (index: number) => {
    Alert.alert('Remove Item', 'Also remove this from your pantry?', [
      {
        text: 'Exclude Only',
        style: 'cancel',
        onPress: () => {
          const items = context.filter((_, i) => i !== index);
          regenerateChat(items);
        }
      },
      {
        text: 'Remove from Pantry',
        onPress: async () => {
          const target = context[index];
          if (target?.id) {
            try { await apiClient.delete(`/pantry/items/${target.id}`); } catch {}
          }
          const items = context.filter((_, i) => i !== index);
          regenerateChat(items);
        }
      }
    ]);
  };

  const handleAddItem = () => {
    if (!newItemName.trim()) { setAddModalVisible(false); return; }
    const qty = Number(newItemQty) || 1;
    const name = newItemName.trim();
    const finish = async (item: any) => {
      if (!item.macros) {
        item.macros = await fetchMacros(item.product_name);
      }
      const items = [...context, item];
      setNewItemName('');
      setNewItemQty('');
      setAddModalVisible(false);
      regenerateChat(items);
    };
    Alert.alert('Add to Pantry?', 'Add this item to your pantry as well?', [
      {
        text: 'Exclude from Pantry',
        style: 'cancel',
        onPress: () => finish({ product_name: name, quantity: qty })
      },
      {
        text: 'Update Pantry',
        onPress: async () => {
          try {
            const res = await apiClient.post('/pantry/items', { product_name: name, quantity: qty });
            const item = res.data.item || res.data;
            await finish(item);
          } catch {
            await finish({ product_name: name, quantity: qty });
          }
        }
      }
    ]);
  };

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setInput('');
    try {
      const res = await apiClient.post('/openai/llm_chat', { messages: newMsgs });
      const raw = res.data.response || '';
      const parsed = parseRecipeText(raw);
      const finalMsgs = [...newMsgs, { role: 'assistant', content: parsed.markdown } as ChatMessage];
      setMessages(finalMsgs);
      const updated: Chat = { id, title, messages: finalMsgs, context, updatedAt: new Date().toISOString() };
      await upsertChat(updated);
      await apiClient.put(`/chats/${updated.id}`, updated);
    } catch (e: any) {
      const errMsgs = [...newMsgs, { role: 'assistant', content: 'Error: ' + String(e) } as ChatMessage];
      setMessages(errMsgs);
    }
  };

  const deleteCurrent = async () => {
    Alert.alert('Delete Chat', 'Are you sure you want to delete this chat?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await apiClient.delete(`/chats/${id}`);
          } catch {}
          await removeChat(id);
          router.back();
        }
      }
    ]);
  };

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <Appbar.Header>
        <Appbar.BackAction onPress={() => router.back()} />
        <Appbar.Content title={title} />
        <Appbar.Action icon="delete" onPress={deleteCurrent} />
      </Appbar.Header>
      {context.length > 0 && (
        <List.Accordion
          title="Selected Items"
          expanded={showCtx}
          onPress={() => setShowCtx(!showCtx)}
        >
          {context.map((it, idx) => (
            <List.Item
              key={idx}
              title={`${it.product_name}${it.quantity ? ` x${it.quantity}` : ''}`}
              description={() => (
                <View style={styles.macrosContainer}>{renderMacroBars(it.macros)}</View>
              )}
              right={props => (
                <IconButton {...props} icon="delete" onPress={() => removeItem(idx)} />
              )}
            />
          ))}
          <List.Item
            title="Add Item"
            left={props => <List.Icon {...props} icon="plus" />}
            onPress={() => setAddModalVisible(true)}
          />
        </List.Accordion>
      )}
      <Modal visible={addModalVisible} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.addSheet}>
            <Text style={styles.addTitle}>Add Item</Text>
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Item name"
              value={newItemName}
              onChangeText={setNewItemName}
            />
            <PaperTextInput
              style={styles.addInput}
              mode="outlined"
              placeholder="Quantity"
              keyboardType="numeric"
              value={newItemQty}
              onChangeText={setNewItemQty}
            />
            <Button mode="contained" onPress={handleAddItem} style={styles.addButton}>Save</Button>
            <Button onPress={() => setAddModalVisible(false)}>Cancel</Button>
          </View>
        </View>
      </Modal>
      <FlatList
        data={messages.filter(m => m.role !== 'system')}
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
  sendButton: { },
  macrosContainer: { marginTop: 4 },
  macroRow: { marginBottom: 6 },
  macroText: { fontSize: 12, marginBottom: 2 },
  macroBar: { height: 8, borderRadius: 4 },
  modalOverlay: { flex:1, justifyContent:'flex-end', backgroundColor:'rgba(0,0,0,0.4)' },
  addSheet: { backgroundColor:'#fff', padding:16, borderTopLeftRadius:12, borderTopRightRadius:12 },
  addTitle: { fontSize:20, fontWeight:'bold', marginBottom:12 },
  addInput: { borderWidth:1, borderColor:'#ddd', borderRadius:8, padding:12, marginBottom:12 },
  addButton: { marginBottom:8 }
});
