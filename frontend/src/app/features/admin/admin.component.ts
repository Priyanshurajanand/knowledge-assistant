import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AdminService } from '../../core/services/admin.service';
import { User } from '../../core/models/user.model';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    FormsModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule,
    MatProgressSpinnerModule,
    MatTableModule,
    MatCardModule,
    MatSnackBarModule
  ],
  template: `
    <div class="admin-wrapper fade-in-entry">
      <!-- Top Navigation bar -->
      <header class="admin-header border-divider">
        <div class="header-brand">
          <button mat-icon-button routerLink="/dashboard" matTooltip="Back to Chat">
            <span class="material-icons">arrow_back</span>
          </button>
          <h1>System Administration</h1>
        </div>
        <div class="header-actions">
          <button mat-stroked-button (click)="loadStats()"><span class="material-icons">refresh</span> Sync Stats</button>
        </div>
      </header>

      @if (isLoading()) {
        <div class="loader-overlay">
          <mat-spinner diameter="40"></mat-spinner>
          <span class="text-muted">Loading system metrics...</span>
        </div>
      } @else {
        <div class="admin-scrollable-container">
          <!-- 1. METRICS CARDS -->
          <div class="metrics-grid">
            <mat-card class="metric-card card-surface">
              <mat-card-content>
                <div class="metric-icon-wrap"><span class="material-icons icon-blue">group</span></div>
                <div class="metric-info">
                  <h3>Total Users</h3>
                  <p class="metric-val">{{ stats().total_users }}</p>
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="metric-card card-surface">
              <mat-card-content>
                <div class="metric-icon-wrap"><span class="material-icons icon-indigo">chat</span></div>
                <div class="metric-info">
                  <h3>Active Chats</h3>
                  <p class="metric-val">{{ stats().total_conversations }}</p>
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="metric-card card-surface">
              <mat-card-content>
                <div class="metric-icon-wrap"><span class="material-icons icon-purple">folder</span></div>
                <div class="metric-info">
                  <h3>Documents</h3>
                  <p class="metric-val">{{ stats().total_documents }}</p>
                </div>
              </mat-card-content>
            </mat-card>

            <mat-card class="metric-card card-surface">
              <mat-card-content>
                <div class="metric-icon-wrap"><span class="material-icons icon-orange">database</span></div>
                <div class="metric-info">
                  <h3>Storage Size</h3>
                  <p class="metric-val">{{ formatBytes(stats().total_storage_bytes) }}</p>
                </div>
              </mat-card-content>
            </mat-card>
          </div>

          <!-- 2. ANALYTICS GRID -->
          <div class="analytics-grid">
            <!-- LLM Provider Stats -->
            <mat-card class="analytics-card card-surface">
              <mat-card-header>
                <mat-card-title>LLM Provider Splits</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="provider-rows">
                  @for (prov of getProvidersList(); track prov.name) {
                    <div class="provider-row">
                      <div class="prov-name-wrap">
                        <span class="provider-badge">{{ prov.name | uppercase }}</span>
                      </div>
                      <div class="prov-progress-track">
                        <div class="prov-progress-fill" [style.width.%]="prov.percentage"></div>
                      </div>
                      <span class="prov-count">{{ prov.count }} chats ({{ prov.percentage }}%)</span>
                    </div>
                  } @empty {
                    <div class="empty-analytics text-muted">No provider usage logged yet.</div>
                  }
                </div>
              </mat-card-content>
            </mat-card>

            <!-- Vector DB Chunks -->
            <mat-card class="analytics-card card-surface">
              <mat-card-header>
                <mat-card-title>Vector Indexing Stats</mat-card-title>
              </mat-card-header>
              <mat-card-content class="flex-center-col">
                <span class="material-icons vector-db-icon">hub</span>
                <span class="vector-count">{{ stats().total_chunks }}</span>
                <span class="text-secondary font-weight-500">Vector Chunks Indexed in Qdrant</span>
                <p class="vector-desc text-muted">All chunks are tagged with a conversation filter payload, ensuring strict logical security boundaries locally.</p>
              </mat-card-content>
            </mat-card>
          </div>

          <!-- 3. USER MANAGEMENT & ACTIVITY TABLES -->
          <div class="tables-container">
            <!-- User Control Console -->
            <mat-card class="table-card card-surface">
              <mat-card-header>
                <mat-card-title>User Control Directory</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="table-scroll-wrapper">
                  <table class="admin-table">
                    <thead>
                      <tr>
                        <th>Email Address</th>
                        <th>Role</th>
                        <th>Created Date</th>
                        <th>Active Status</th>
                        <th>Administrative Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (user of users(); track user.id) {
                        <tr>
                          <td><strong>{{ user.email }}</strong></td>
                          <td>
                            <span class="role-badge" [class.badge-admin]="user.role === 'admin'">
                              {{ user.role | uppercase }}
                            </span>
                          </td>
                          <td class="text-muted">{{ user.created_at | date:'short' }}</td>
                          <td>
                            <span class="status-dot" [class.status-active]="user.is_active" [class.status-inactive]="!user.is_active"></span>
                            {{ user.is_active ? 'Enabled' : 'Deactivated' }}
                          </td>
                          <td>
                            <div class="actions-cell">
                              <button mat-stroked-button class="mini-action-btn" (click)="toggleUserActive(user)">
                                {{ user.is_active ? 'Deactivate' : 'Activate' }}
                              </button>
                              <button mat-stroked-button class="mini-action-btn" (click)="changeUserRole(user)">
                                Make {{ user.role === 'admin' ? 'User' : 'Admin' }}
                              </button>
                            </div>
                          </td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </mat-card-content>
            </mat-card>

            <!-- System Audit Log -->
            <mat-card class="table-card card-surface">
              <mat-card-header>
                <mat-card-title>Recent Workspace Activities</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="table-scroll-wrapper">
                  <table class="admin-table">
                    <thead>
                      <tr>
                        <th>Triggered Timestamp</th>
                        <th>Event Action</th>
                        <th>Description Details</th>
                        <th>IP Address</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (log of stats().recent_activity; track log.id) {
                        <tr>
                          <td class="text-muted">{{ log.created_at | date:'medium' }}</td>
                          <td><span class="action-label">{{ log.action | uppercase }}</span></td>
                          <td>{{ log.details }}</td>
                          <td class="text-muted">{{ log.ip_address }}</td>
                        </tr>
                      } @empty {
                        <tr>
                          <td colspan="4" class="text-center text-muted">No activities logged.</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </div>
      }
    </div>
  `,
  styles: [`
    .admin-wrapper {
      display: flex;
      flex-direction: column;
      height: 100vh;
      width: 100%;
      overflow: hidden;
      
      .dark-theme & {
        background-color: #0b0b0e;
        color: #f3f4f6;
      }
      .light-theme & {
        background-color: #f8fafc;
        color: #0f172a;
      }
    }

    .admin-header {
      height: 60px;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid;
      
      .dark-theme & { border-bottom-color: #262631; }
      .light-theme & { border-bottom-color: #e2e8f0; }

      .header-brand {
        display: flex;
        align-items: center;
        gap: 12px;

        h1 {
          font-family: 'Outfit', sans-serif;
          font-size: 18px;
          font-weight: 600;
          margin: 0;
        }
      }
    }

    .loader-overlay {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 16px;
    }

    .admin-scrollable-container {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      display: flex;
      flex-direction: column;
      gap: 24px;
      max-width: 1200px;
      width: 100%;
      margin: 0 auto;
    }

    // Metrics Cards
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }

    .metric-card {
      border-radius: 12px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);

      mat-card-content {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 20px !important;
      }

      .metric-icon-wrap {
        width: 44px;
        height: 44px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        
        .dark-theme & { background-color: rgba(255, 255, 255, 0.03); }
        .light-theme & { background-color: rgba(0, 0, 0, 0.02); }

        span { font-size: 24px; }
        .icon-blue { color: #3b82f6; }
        .icon-indigo { color: #6366f1; }
        .icon-purple { color: #a855f7; }
        .icon-orange { color: #f97316; }
      }

      .metric-info {
        display: flex;
        flex-direction: column;

        h3 {
          font-size: 12px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.5px;
          margin: 0 0 4px 0;
          color: #71717a;
        }

        .metric-val {
          font-family: 'Outfit', sans-serif;
          font-size: 24px;
          font-weight: 700;
          margin: 0;
          line-height: 1;
        }
      }
    }

    // Analytics Grid
    .analytics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 20px;
    }

    .analytics-card {
      border-radius: 12px;
      padding: 16px;

      mat-card-title {
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        font-weight: 600;
      }
    }

    .provider-rows {
      display: flex;
      flex-direction: column;
      gap: 14px;
      margin-top: 16px;
    }

    .provider-row {
      display: flex;
      align-items: center;
      gap: 12px;

      .prov-name-wrap {
        width: 80px;
      }
      .provider-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 6px;
        background-color: #272730;
        border-radius: 4px;
        letter-spacing: 0.5px;
        
        .light-theme & {
          background-color: #e2e8f0;
        }
      }

      .prov-progress-track {
        flex: 1;
        height: 8px;
        border-radius: 4px;
        
        .dark-theme & { background-color: #272730; }
        .light-theme & { background-color: #e2e8f0; }

        .prov-progress-fill {
          height: 100%;
          border-radius: 4px;
          background-color: #6366f1;
        }
      }

      .prov-count {
        font-size: 12px;
        min-width: 110px;
        text-align: right;
      }
    }

    .flex-center-col {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px 0 !important;
      text-align: center;

      .vector-db-icon {
        font-size: 48px;
        color: #a855f7;
        margin-bottom: 8px;
      }

      .vector-count {
        font-family: 'Outfit', sans-serif;
        font-size: 36px;
        font-weight: 700;
        line-height: 1.1;
        color: #a855f7;
      }

      .vector-desc {
        max-width: 320px;
        font-size: 11.5px;
        margin-top: 8px;
        line-height: 1.5;
      }
    }

    // Tables
    .tables-container {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .table-card {
      border-radius: 12px;
      padding: 16px;
      
      mat-card-title {
        font-family: 'Outfit', sans-serif;
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 12px;
      }
    }

    .table-scroll-wrapper {
      width: 100%;
      overflow-x: auto;
    }

    .admin-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      text-align: left;

      th {
        font-weight: 600;
        padding: 12px 16px;
        border-bottom: 2px solid;
        color: #71717a;
        
        .dark-theme & { border-bottom-color: #262631; }
        .light-theme & { border-bottom-color: #e2e8f0; }
      }

      td {
        padding: 12px 16px;
        border-bottom: 1px solid;
        
        .dark-theme & { border-bottom-color: #1a1a24; }
        .light-theme & { border-bottom-color: #f1f5f9; }
      }

      .role-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 3px 6px;
        border-radius: 4px;
        background-color: rgba(99, 102, 241, 0.1);
        color: #6366f1;
        letter-spacing: 0.5px;

        &.badge-admin {
          background-color: rgba(244, 63, 94, 0.1);
          color: #f43f5e;
        }
      }

      .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;

        &.status-active { background-color: #10b981; }
        &.status-inactive { background-color: #f43f5e; }
      }

      .actions-cell {
        display: flex;
        gap: 8px;
      }

      .mini-action-btn {
        height: 28px;
        line-height: 26px;
        font-size: 11px;
        border-radius: 4px;
        padding: 0 10px;
        border-color: #3f3f46;
        color: inherit;

        .light-theme & {
          border-color: #cbd5e1;
        }
      }

      .action-label {
        font-size: 11px;
        font-weight: 600;
      }
    }
  `]
})
export class AdminComponent implements OnInit {
  private adminService = inject(AdminService);
  private authService = inject(AuthService);
  private snackBar = inject(MatSnackBar);

  stats = signal<any>({
    total_users: 0,
    total_conversations: 0,
    total_documents: 0,
    total_chunks: 0,
    total_storage_bytes: 0,
    provider_usage: {},
    recent_activity: []
  });
  
  users = signal<User[]>([]);
  isLoading = signal<boolean>(false);

  ngOnInit(): void {
    this.loadStats();
    this.loadUsers();
  }

  loadStats(): void {
    this.isLoading.set(true);
    this.adminService.getStats().subscribe({
      next: (data) => {
        this.stats.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.isLoading.set(false);
        this.snackBar.open('Failed to load admin stats.', 'Close', { duration: 3000 });
      }
    });
  }

  loadUsers(): void {
    this.adminService.getUsers().subscribe({
      next: (data) => this.users.set(data)
    });
  }

  getProvidersList() {
    const usage = this.stats().provider_usage || {};
    const total = Object.values(usage).reduce((a: any, b: any) => a + b, 0) as number;
    return Object.keys(usage).map(key => {
      const count = usage[key] as number;
      const percentage = total > 0 ? Math.round((count / total) * 100) : 0;
      return { name: key, count, percentage };
    });
  }

  toggleUserActive(user: User): void {
    if (user.id === this.authService.currentUser()?.id) {
      this.snackBar.open('Cannot deactivate your own active session!', 'Close', { duration: 3000 });
      return;
    }
    
    this.adminService.toggleUserActive(user.id).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
        this.loadStats();
        this.snackBar.open(`User ${user.email} access changed.`, 'Close', { duration: 2000 });
      }
    });
  }

  changeUserRole(user: User): void {
    if (user.id === this.authService.currentUser()?.id) {
      this.snackBar.open('Cannot change your own role!', 'Close', { duration: 3000 });
      return;
    }

    const nextRole = user.role === 'admin' ? 'user' : 'admin';
    this.adminService.updateUserRole(user.id, nextRole).subscribe({
      next: (updated) => {
        this.users.update(list => list.map(u => u.id === updated.id ? updated : u));
        this.loadStats();
        this.snackBar.open(`User ${user.email} role set to ${nextRole}.`, 'Close', { duration: 2000 });
      }
    });
  }

  formatBytes(bytes: number): string {
    if (!bytes) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
}
