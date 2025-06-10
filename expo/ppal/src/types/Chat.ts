export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: ChatMessage[];
  context?: any[];
  updatedAt: string;
  length?: number;
}
