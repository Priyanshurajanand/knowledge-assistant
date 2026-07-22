export interface Conversation {
  id: string;
  title: string;
  user_id: string;
  provider: string;
  model: string;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  filename: string;
  page_number: number;
  text: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant';
  content: string;
  citations: Citation[] | null;
  created_at: string;
}
