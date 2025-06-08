export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: ChatMessage[];
  updatedAt: string;
  length?: number;
}
