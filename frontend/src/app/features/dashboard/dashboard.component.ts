import { Component, OnInit, ElementRef, ViewChild, inject, signal, computed, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatOptionModule } from '@angular/material/core';

import { AuthService } from '../../core/services/auth.service';
import { ChatService } from '../../core/services/chat.service';
import { Conversation, Message, Citation } from '../../core/models/conversation.model';
import { Document } from '../../core/models/document.model';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';

interface ProviderModel {
  value: string;
  viewValue: string;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    MatButtonModule,
    MatIconModule,
    MatInputModule,
    MatFormFieldModule,
    MatSelectModule,
    MatOptionModule,
    MatTooltipModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MarkdownPipe
  ],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {
  authService = inject(AuthService);
  private chatService = inject(ChatService);
  private snackBar = inject(MatSnackBar);

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  // --- Sidebar States ---
  conversations = signal<Conversation[]>([]);
  searchQuery = signal<string>('');
  filteredConversations = computed(() => {
    const q = this.searchQuery().toLowerCase().trim();
    const all = this.conversations();
    if (!q) return all;
    return all.filter(c => c.title.toLowerCase().includes(q));
  });

  pinnedConversations = computed(() => this.filteredConversations().filter(c => c.is_pinned));
  unpinnedConversations = computed(() => this.filteredConversations().filter(c => !c.is_pinned));

  // --- Active Chat States ---
  activeConversation = signal<Conversation | null>(null);
  messages = signal<Message[]>([]);
  inputText = signal<string>('');
  isGenerating = signal<boolean>(false);
  streamingMessageText = signal<string>('');
  streamingCitations = signal<Citation[]>([]);

  // --- Collapsible Documents panel ---
  showDocPanel = signal<boolean>(true);
  documents = signal<Document[]>([]);
  isUploading = signal<boolean>(false);
  isDragging = signal<boolean>(false);
  uploadProgress = signal<number>(0);

  // --- Responsive states ---
  showSidebar = signal<boolean>(false);

  // --- Inline edit states ---
  editingConvId = signal<string | null>(null);
  editTitleText = signal<string>('');

  // --- Expanded Citation States ---
  expandedCitationMsgId = signal<string | null>(null);
  expandedCitationIndex = signal<number | null>(null);

  // --- Dynamic Model selection configuration ---
  selectedProvider = signal<string>('groq');
  selectedModel = signal<string>('llama-3.3-70b-versatile');

  providers = [
    { value: 'groq', viewValue: 'Groq' },
    { value: 'openai', viewValue: 'OpenAI' },
    { value: 'gemini', viewValue: 'Google Gemini' },
    { value: 'claude', viewValue: 'Anthropic Claude' }
  ];

  providerModels: Record<string, ProviderModel[]> = {
    openai: [
      { value: 'gpt-4o', viewValue: 'GPT-4o' },
      { value: 'gpt-4-turbo', viewValue: 'GPT-4 Turbo' },
      { value: 'gpt-3.5-turbo', viewValue: 'GPT-3.5 Turbo' }
    ],
    gemini: [
      { value: 'gemini-1.5-flash', viewValue: 'Gemini 1.5 Flash' },
      { value: 'gemini-1.5-pro', viewValue: 'Gemini 1.5 Pro' }
    ],
    claude: [
      { value: 'claude-3-5-sonnet-20240620', viewValue: 'Claude 3.5 Sonnet' },
      { value: 'claude-3-opus-20240229', viewValue: 'Claude 3 Opus' },
      { value: 'claude-3-haiku-20240307', viewValue: 'Claude 3 Haiku' }
    ],
    groq: [
      { value: 'llama-3.3-70b-versatile', viewValue: 'Llama 3.3 70B' },
      { value: 'deepseek-r1-distill-llama-70b', viewValue: 'DeepSeek R1 Llama 70B' },
      { value: 'deepseek-r1-distill-qwen-32b', viewValue: 'DeepSeek R1 Qwen 32B' }
    ]
  };

  currentModels = computed(() => {
    return this.providerModels[this.selectedProvider()] || [];
  });

  private abortController: AbortController | null = null;

  ngOnInit(): void {
    this.loadConversations();
  }

  // --- Sidebar Logic ---
  loadConversations(selectLast = false): void {
    this.chatService.getConversations().subscribe({
      next: (convs) => {
        this.conversations.set(convs);
        if (selectLast && convs.length > 0) {
          this.selectConversation(convs[0]);
        }
      },
      error: () => this.snackBar.open('Failed to load conversations.', 'Close', { duration: 3000 })
    });
  }

  createNewChat(): void {
    const defaultTitle = `Chat ${this.conversations().length + 1}`;
    this.chatService.createConversation(defaultTitle).subscribe({
      next: (newConv) => {
        this.loadConversations();
        this.selectConversation(newConv);
        this.snackBar.open('New conversation created.', 'Close', { duration: 2000 });
      },
      error: () => this.snackBar.open('Failed to create chat.', 'Close', { duration: 3000 })
    });
  }

  selectConversation(conv: Conversation): void {
    this.showSidebar.set(false); // Close mobile sidebar automatically
    this.editingConvId.set(null);
    this.activeConversation.set(conv);
    this.selectedProvider.set(conv.provider);
    this.selectedModel.set(conv.model);

    // Load historical messages
    this.chatService.getMessages(conv.id).subscribe({
      next: (msgs) => {
        this.messages.set(msgs);
        this.scrollToBottom();
      }
    });

    // Load conversation documents
    this.loadDocuments(conv.id);
  }

  togglePin(conv: Conversation, event: MouseEvent): void {
    event.stopPropagation();
    const targetState = !conv.is_pinned;
    this.chatService.updateConversation(conv.id, { is_pinned: targetState }).subscribe({
      next: () => {
        this.loadConversations();
        this.snackBar.open(targetState ? "Conversation pinned to top." : "Conversation unpinned.", "Close", { duration: 2000 });
      },
      error: (err) => {
        console.error("Pin conversation failed:", err);
        this.snackBar.open("Failed to pin conversation.", "Close", { duration: 3000 });
      }
    });
  }

  startRename(conv: Conversation, event: MouseEvent): void {
    event.stopPropagation();
    this.editingConvId.set(conv.id);
    this.editTitleText.set(conv.title);
  }

  saveRename(conv: Conversation): void {
    const title = this.editTitleText().trim();
    if (!title || title === conv.title) {
      this.editingConvId.set(null);
      return;
    }

    this.chatService.updateConversation(conv.id, { title }).subscribe({
      next: () => {
        this.editingConvId.set(null);
        this.loadConversations();
        if (this.activeConversation()?.id === conv.id) {
          this.activeConversation.update(c => c ? { ...c, title } : null);
        }
        this.snackBar.open("Conversation renamed successfully.", "Close", { duration: 2000 });
      },
      error: (err) => {
        console.error("Rename conversation failed:", err);
        this.snackBar.open("Failed to rename conversation.", "Close", { panelClass: ['error-snackbar'] });
      }
    });
  }

  cancelRename(): void {
    this.editingConvId.set(null);
  }

  deleteConversation(conv: Conversation, event: MouseEvent): void {
    event.stopPropagation();
    if (!confirm(`Are you sure you want to delete "${conv.title}"?`)) return;

    this.chatService.deleteConversation(conv.id).subscribe({
      next: () => {
        this.loadConversations();
        if (this.activeConversation()?.id === conv.id) {
          this.activeConversation.set(null);
          this.messages.set([]);
          this.documents.set([]);
        }
        this.snackBar.open('Conversation deleted successfully.', 'Close', { duration: 2500 });
      },
      error: (err) => {
        console.error("Delete conversation failed:", err);
        this.snackBar.open("Failed to delete conversation.", "Close", { panelClass: ['error-snackbar'] });
      }
    });
  }

  // --- Dynamic Model Selection ---
  onProviderChange(provider: string): void {
    this.selectedProvider.set(provider);
    // Auto-select first model of new provider
    const models = this.providerModels[provider];
    if (models && models.length > 0) {
      this.onModelChange(models[0].value);
    }
  }

  onModelChange(model: string): void {
    this.selectedModel.set(model);
    const active = this.activeConversation();
    if (active) {
      this.chatService.updateConversation(active.id, {
        provider: this.selectedProvider(),
        model
      }).subscribe({
        next: (updated) => {
          this.activeConversation.set(updated);
          this.loadConversations();
          this.snackBar.open(`Settings updated: Switched to ${updated.model} (${updated.provider}).`, "Close", { duration: 2500 });
        },
        error: (err) => {
          console.error("Model update failed:", err);
          this.snackBar.open("Failed to update conversation settings.", "Close", { panelClass: ['error-snackbar'] });
        }
      });
    }
  }

  // --- Documents Ingestion ---
  loadDocuments(convId: string): void {
    this.chatService.getDocuments(convId).subscribe({
      next: (docs) => this.documents.set(docs)
    });
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(true);
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragging.set(false);
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.uploadFile(files[0]);
    }
  }

  onFileSelected(event: any): void {
    const files = event.target?.files;
    if (files && files.length > 0) {
      this.uploadFile(files[0]);
    }
  }

  uploadFile(file: File): void {
    const active = this.activeConversation();
    if (!active) {
      this.snackBar.open('Please select or create a conversation first.', 'Close', { duration: 3000 });
      return;
    }

    this.isUploading.set(true);
    this.uploadProgress.set(20);
    this.snackBar.open(`Uploading "${file.name}"... Parsing text and creating vector embeddings.`, "Close", { duration: 4000 });

    this.chatService.uploadDocument(active.id, file).subscribe({
      next: (doc) => {
        this.isUploading.set(false);
        this.loadDocuments(active.id);
        this.snackBar.open(`"${file.name}" processed and vectorized successfully.`, 'Close', { duration: 3000 });
      },
      error: (err) => {
        this.isUploading.set(false);
        const errMsg = err.error?.detail || 'Failed to parse and upload file.';
        this.snackBar.open(errMsg, 'Close', { panelClass: ['error-snackbar'] });
      }
    });
  }

  deleteDocument(doc: Document, event: MouseEvent): void {
    event.stopPropagation();
    if (!confirm(`Remove "${doc.filename}" from this knowledge base?`)) return;

    this.chatService.deleteDocument(doc.id).subscribe({
      next: () => {
        const active = this.activeConversation();
        if (active) this.loadDocuments(active.id);
        this.snackBar.open('Document removed from database and vectors deleted.', 'Close', { duration: 2500 });
      },
      error: (err) => {
        console.error("Delete document failed:", err);
        this.snackBar.open("Failed to delete document from knowledge base.", "Close", { panelClass: ['error-snackbar'] });
      }
    });
  }

  formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  onKeyDown(event: any): void {
    if (!event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  // --- Expanded Citation Handlers ---
  toggleCitation(msgId: string, index: number): void {
    if (this.expandedCitationMsgId() === msgId && this.expandedCitationIndex() === index) {
      this.closeCitation();
    } else {
      this.expandedCitationMsgId.set(msgId);
      this.expandedCitationIndex.set(index);
    }
  }

  closeCitation(): void {
    this.expandedCitationMsgId.set(null);
    this.expandedCitationIndex.set(null);
  }

  // --- RAG Chat & Streaming Completion ---
  sendMessage(): void {
    const text = this.inputText().trim();
    const active = this.activeConversation();
    if (!text || !active || this.isGenerating()) return;

    this.inputText.set('');
    this.isGenerating.set(true);
    this.streamingMessageText.set('');
    this.streamingCitations.set([]);

    // Add temporary user message to UI immediately
    const userTempMsg: Message = {
      id: '',
      conversation_id: active.id,
      role: 'user',
      content: text,
      citations: null,
      created_at: new Date().toISOString()
    };
    this.messages.update(m => [...m, userTempMsg]);
    this.scrollToBottom();

    // Trigger SSE streaming call
    this.abortController = new AbortController();

    this.chatService.streamResponse(
      active.id,
      text,
      (event, data) => {
        if (event === 'citations') {
          this.streamingCitations.set(data);
        } else if (event === 'token') {
          this.streamingMessageText.update(t => t + data);
          this.scrollToBottom();
        } else if (event === 'end') {
          this.completeStream();
        }
      },
      this.abortController.signal
    ).catch((err) => {
      if (err.name !== 'AbortError') {
        const errAlert = `\n\n[Failed to connect: ${err.message || 'Check backend status'}]`;
        this.streamingMessageText.update(t => t + errAlert);
        this.snackBar.open("Connection error: Failed to generate response.", "Close", { panelClass: ['error-snackbar'] });
      }
      this.isGenerating.set(false);
    });
  }

  stopGeneration(): void {
    if (this.abortController) {
      this.abortController.abort();
      this.completeStream();
    }
  }

  completeStream(): void {
    this.isGenerating.set(false);
    const active = this.activeConversation();
    if (active) {
      // Reload final committed messages from PostgreSQL (to get correct db IDs)
      this.chatService.getMessages(active.id).subscribe({
        next: (msgs) => {
          this.messages.set(msgs);
          this.streamingMessageText.set('');
          this.streamingCitations.set([]);
          this.scrollToBottom();
        }
      });
    }
  }

  retryMessage(msg: Message): void {
    // Re-send the last user question. We find it in the history
    const userMsgs = this.messages().filter(m => m.role === 'user');
    if (userMsgs.length === 0) return;

    const lastUserMsg = userMsgs[userMsgs.length - 1];
    this.inputText.set(lastUserMsg.content);

    // If the last message was assistant, remove it locally before retry to avoid double display
    const lastMsg = this.messages()[this.messages().length - 1];
    if (lastMsg.role === 'assistant') {
      this.messages.update(m => m.slice(0, -1));
    }

    this.sendMessage();
  }

  copyResponse(text: string): void {
    navigator.clipboard.writeText(text);
    this.snackBar.open('Copied to clipboard.', 'Close', { duration: 2000 });
  }

  // --- Scroll Actions ---
  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.scrollContainer) {
        const element = this.scrollContainer.nativeElement;
        element.scrollTop = element.scrollHeight;
      }
    }, 100);
  }
}
