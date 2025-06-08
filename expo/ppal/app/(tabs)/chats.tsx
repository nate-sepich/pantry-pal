import React, { useCallback, useState } from 'react';
import { View, FlatList, TouchableOpacity, Text, StyleSheet } from 'react-native';
import { useRouter, useFocusEffect } from 'expo-router';
import { Chat } from '../../src/types/Chat';
import { loadChats, saveChats } from '../../src/utils/chatStore';
import apiClient from '../../src/api/client';

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
  );
}

const styles = StyleSheet.create({
  row: { padding: 16, borderBottomWidth: 1, borderColor: '#ddd' },
  title: { fontSize: 16, fontWeight: 'bold' },
  date: { fontSize: 12, color: '#666' },
});
