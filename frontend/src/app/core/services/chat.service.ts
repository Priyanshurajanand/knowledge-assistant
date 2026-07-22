import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AuthService } from './auth.service';
import { Conversation, Message } from '../models/conversation.model';
import { Document } from '../models/document.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private http = inject(HttpClient);
  private authService = inject(AuthService);

  // --- Conversations CRUD ---
  getConversations(query?: string): Observable<Conversation[]> {
    let params = new HttpParams();
    if (query) {
      params = params.set('q', query);
    }
    return this.http.get<Conversation[]>(`${environment.apiUrl}/conversations/`, { params });
  }

  createConversation(title: string, provider?: string, model?: string): Observable<Conversation> {
    return this.http.post<Conversation>(`${environment.apiUrl}/conversations/`, {
      title,
      provider,
      model
    });
  }

  updateConversation(id: string, data: Partial<Conversation>): Observable<Conversation> {
    return this.http.put<Conversation>(`${environment.apiUrl}/conversations/${id}`, data);
  }

  deleteConversation(id: string): Observable<any> {
    return this.http.delete(`${environment.apiUrl}/conversations/${id}`);
  }

  // --- Message History ---
  getMessages(conversationId: string): Observable<Message[]> {
    return this.http.get<Message[]>(`${environment.apiUrl}/conversations/${conversationId}/messages`);
  }

  // --- Documents Ingestion ---
  getDocuments(conversationId: string): Observable<Document[]> {
    return this.http.get<Document[]>(`${environment.apiUrl}/documents/conversation/${conversationId}`);
  }

  deleteDocument(documentId: string): Observable<any> {
    return this.http.delete(`${environment.apiUrl}/documents/${documentId}`);
  }

  uploadDocument(conversationId: string, file: File): Observable<Document> {
    const formData = new FormData();
    formData.append('conversation_id', conversationId);
    formData.append('file', file);
    return this.http.post<Document>(`${environment.apiUrl}/documents/upload`, formData);
  }

  // --- Streaming chat completions with RRF context ---
  /**
   * Sends a chat prompt to the backend and streams the response in real-time.
   * - Uses native browser `fetch` API (instead of Angular HttpClient) to read HTTP response streams directly.
   * - Parses Server-Sent Events (SSE) structured as "event: [type]" and "data: [JSON string]".
   * 
   * @param conversationId - The active chat session UUID
   * @param question - The user query prompt
   * @param onEvent - Callback function triggered for every received token or event chunk
   * @param abortSignal - Optional signal to abort the stream request mid-way (e.g. if the user cancels or submits a new prompt)
   */
  async streamResponse(
    conversationId: string,
    question: string,
    onEvent: (event: string, data: any) => void,
    abortSignal?: AbortSignal
  ): Promise<void> {
    // 1. Send POST request requesting stream completions
    const response = await fetch(`${environment.apiUrl}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authService.token()}`
      },
      body: JSON.stringify({ conversation_id: conversationId, question }),
      signal: abortSignal
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(errText || 'Connection failed.');
    }

    // 2. Fetch the stream reader and text decoder
    const reader = response.body?.getReader();
    const decoder = new TextDecoder('utf-8');
    if (!reader) return;

    let buffer = '';
    
    try {
      while (true) {
        // Read a chunk of binary data from the network stream
        const { value, done } = await reader.read();
        if (done) break;

        // Decode binary chunk to text and append to buffer
        buffer += decoder.decode(value, { stream: true });
        
        // Split buffered content by newlines to extract complete SSE lines
        const lines = buffer.split('\n');
        
        // Retain any incomplete line inside the buffer for the next iteration
        buffer = lines.pop() || '';

        let currentEvent = '';
        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;
          
          // Parse Server-Sent Events structure
          if (trimmed.startsWith('event: ')) {
            // Read event name (e.g., 'token' or 'citations')
            currentEvent = trimmed.substring(7).trim();
          } else if (trimmed.startsWith('data: ')) {
            // Read JSON content associated with the event
            const dataStr = trimmed.substring(6).trim();
            try {
              const data = JSON.parse(dataStr);
              onEvent(currentEvent, data);
            } catch {
              // Fallback if data is raw string
              onEvent(currentEvent, dataStr);
            }
          }
        }
      }
    } finally {
      // Release network reader lock when complete or aborted
      reader.releaseLock();
    }
  }
}
