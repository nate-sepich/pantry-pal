import React, { useState, useEffect } from 'react';
import { View, TextInput, FlatList, KeyboardAvoidingView, Platform, StyleSheet, Text, Modal } from 'react-native';
import { Appbar, Button, List, IconButton, ProgressBar, TextInput as PaperTextInput } from 'react-native-paper';
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

export default function ChatScreen() {
  const router = useRouter();
  const { recipe, chatId, system, ctx } = useLocalSearchParams<{ recipe?: string; chatId?: string; system?: string; ctx?: string }>();
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
      if (system) {
        if (ctx) {
          try {
            setContext(JSON.parse(ctx as string));
          } catch {}
        }
        const sysMsg: ChatMessage = { role: 'system', content: system as string };
        const userMsg: ChatMessage = {
          role: 'user',
          content: 'Generate a recipe using the provided items.'
        };
        const newId = Math.random().toString(36).slice(2);
        const res = await apiClient.post('/openai/llm_chat', { messages: [sysMsg, userMsg] });
        const reply = res.data.response || '';
        let display = reply;
        try { display = formatRecipeMarkdown(JSON.parse(reply)); } catch {}
        const assistant: ChatMessage = { role: 'assistant', content: display };
        const newChat: Chat = { id: newId, title: 'New Chat', messages: [sysMsg, assistant], updatedAt: new Date().toISOString() };
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
  }, [system, recipe, chatId, ctx]);

  const regenerateChat = async (items: any[]) => {
    const prompt = buildSystemPrompt(items);
    const sysMsg: ChatMessage = { role: 'system', content: prompt };
    const userMsg: ChatMessage = { role: 'user', content: 'Generate a recipe using the provided items.' };
    const res = await apiClient.post('/openai/llm_chat', { messages: [sysMsg, userMsg] });
    let text = res.data.response || '';
    try { text = formatRecipeMarkdown(JSON.parse(text)); } catch {}
    const assistant: ChatMessage = { role: 'assistant', content: text };
    const newMsgs = [sysMsg, assistant];
    setMessages(newMsgs);
    setContext(items);
    const updated: Chat = { id, title: 'New Chat', messages: newMsgs, updatedAt: new Date().toISOString() };
    setTitle(updated.title);
    await upsertChat(updated);
    await apiClient.post('/chats', {
      id: updated.id,
      title: updated.title,
      updatedAt: updated.updatedAt,
      length: updated.messages.length,
    });
  };

  const removeItem = (index: number) => {
    const items = context.filter((_, i) => i !== index);
    regenerateChat(items);
  };

  const handleAddItem = () => {
    if (!newItemName.trim()) { setAddModalVisible(false); return; }
    const qty = Number(newItemQty) || 1;
    const items = [...context, { product_name: newItemName.trim(), quantity: qty }];
    setNewItemName('');
    setNewItemQty('');
    setAddModalVisible(false);
    regenerateChat(items);
  };

  const send = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { role: 'user', content: input.trim() };
    const newMsgs = [...messages, userMsg];
    setMessages(newMsgs);
    setInput('');
    try {
      const res = await apiClient.post('/openai/llm_chat', { messages: newMsgs });
        let text = res.data.response || '';
        try { text = formatRecipeMarkdown(JSON.parse(text)); } catch {}
        const finalMsgs = [...newMsgs, { role: 'assistant', content: text } as ChatMessage];
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
