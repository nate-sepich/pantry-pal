import AsyncStorage from '@react-native-async-storage/async-storage';
import { Chat } from '../types/Chat';

const KEY = 'ppal.chats';

export async function loadChats(): Promise<Chat[]> {
  const raw = await AsyncStorage.getItem(KEY);
  if (!raw) return [];
  try {
    return JSON.parse(raw) as Chat[];
  } catch {
    return [];
  }
}

export async function saveChats(chats: Chat[]): Promise<void> {
  await AsyncStorage.setItem(KEY, JSON.stringify(chats));
}

export async function upsertChat(chat: Chat): Promise<void> {
  const chats = await loadChats();
  const index = chats.findIndex(c => c.id === chat.id);
  if (index !== -1) {
    chats[index] = chat;
  } else {
    chats.unshift(chat);
  }
  await saveChats(chats);
}

export async function getChat(id: string): Promise<Chat | undefined> {
  const chats = await loadChats();
  return chats.find(c => c.id === id);
}

export async function removeChat(id: string): Promise<void> {
  const chats = await loadChats();
  const filtered = chats.filter(c => c.id !== id);
  await saveChats(filtered);
}
