import React, { useCallback, useState } from 'react';
import { SafeAreaView, View, FlatList, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Chat } from '../src/types/Chat';
import { loadChats, saveChats } from '../src/utils/chatStore';
import apiClient from '../src/api/client';
import { ArrowLeft, Menu, MessageCircle } from 'lucide-react-native';

export default function ChatsTab() {
  const router = useRouter();
  const [chats, setChats] = useState<Chat[]>([]);

  const refresh = useCallback(async () => {
    try {
      const server = await apiClient.get('/chats');
      const metas: Chat[] = server.data;
      const local = await loadChats();
      const map: Record<string, Chat> = {};
      for (const c of local) map[c.id] = c;
      for (const m of metas) {
        if (map[m.id]) {
          map[m.id].title = m.title;
          map[m.id].updatedAt = m.updatedAt;
          map[m.id].length = m.length;
        } else {
          map[m.id] = { ...m, messages: [] };
        }
      }
      const items = Object.values(map);
      items.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
      await saveChats(items);
      setChats(items);
    } catch (e) {
      const items = await loadChats();
      items.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
      setChats(items);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh])
  );

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: 'rgba(255, 255, 255, 0.7)' }}>
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <TouchableOpacity onPress={() => router.push('/pantry')}>
            <ArrowLeft width={24} height={24} color="white" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Chats</Text>
          <TouchableOpacity onPress={() => router.push('/pantry')}>
            <Menu width={24} height={24} color="white" />
          </TouchableOpacity>
        </View>
      </View>
      <View style={{ flex: 1 }}>
        <FlatList
          data={chats}
          keyExtractor={(c) => c.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.row}
              onPress={() => router.push({ pathname: '/chat', params: { chatId: item.id } })}
            >
              <Text style={styles.title}>{item.title}</Text>
              <Text style={styles.date}>{new Date(item.updatedAt).toLocaleDateString()}</Text>
            </TouchableOpacity>
          )}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  header: { backgroundColor: '#0d9488', padding: 16 },
  headerContent: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  headerTitle: { color: 'white', fontSize: 20, fontWeight: 'bold' },
  row: { padding: 16, borderBottomWidth: 1, borderColor: '#ddd' },
  title: { fontSize: 16, fontWeight: 'bold' },
  date: { fontSize: 12, color: '#666' },
});
