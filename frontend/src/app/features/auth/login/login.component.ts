import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatSnackBarModule
  ],
  template: `
    <div class="auth-container">
      <div class="auth-bg-layer"></div>
      <div class="auth-blob blob-1"></div>
      <div class="auth-blob blob-2"></div>
      <div class="auth-blob blob-3"></div>
      <div class="auth-grid-overlay"></div>
      
      <!-- Floating theme toggle button -->
      <button type="button" mat-icon-button class="theme-toggle-floating" (click)="authService.toggleTheme()" matTooltip="Toggle Dark/Light Mode">
        <mat-icon>{{ authService.darkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
      </button>
      
      <mat-card class="auth-card card-surface fade-in-entry">
        <mat-card-header>
          <div class="brand-header">
            <span class="material-icons brand-icon">insights</span>
            <h1>Enterprise AI</h1>
          </div>
          <mat-card-subtitle>Knowledge Assistant</mat-card-subtitle>
        </mat-card-header>

        <mat-card-content>
          <form [formGroup]="loginForm" (ngSubmit)="onSubmit()">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Email Address</mat-label>
              <input matInput type="email" formControlName="email" placeholder="you@company.com" autocomplete="email">
              <mat-error *ngIf="loginForm.get('email')?.hasError('required')">Email is required</mat-error>
              <mat-error *ngIf="loginForm.get('email')?.hasError('email')">Invalid email address</mat-error>
            </mat-form-field>

            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Password</mat-label>
              <input matInput [type]="hidePassword() ? 'password' : 'text'" formControlName="password" autocomplete="current-password">
              <button type="button" mat-icon-button matSuffix (click)="togglePasswordVisibility()">
                <mat-icon>{{ hidePassword() ? 'visibility_off' : 'visibility' }}</mat-icon>
              </button>
              <mat-error *ngIf="loginForm.get('password')?.hasError('required')">Password is required</mat-error>
            </mat-form-field>

            <button mat-flat-button color="primary" type="submit" class="full-width submit-btn" [disabled]="isLoading() || loginForm.invalid">
              {{ isLoading() ? 'Signing in...' : 'Sign In' }}
            </button>
          </form>
        </mat-card-content>

        <mat-card-footer class="auth-footer">
          <p>Don't have an account? <a routerLink="/register" class="auth-link">Create one</a></p>
        </mat-card-footer>
      </mat-card>
    </div>
  `,
  styles: [`
    .auth-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      width: 100%;
      position: relative;
      overflow: hidden;
      transition: background 0.5s ease;

      .dark-theme & {
        background: linear-gradient(135deg, #0a0a12 0%, #0d0d1f 40%, #0f0826 70%, #0a0a12 100%);
      }
      .light-theme & {
        background: linear-gradient(135deg, #e8eaf6 0%, #ede7f6 30%, #e3f2fd 60%, #f3e5f5 100%);
      }
    }

    /* Solid gradient base layer */
    .auth-bg-layer {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;

      .dark-theme & {
        background:
          radial-gradient(ellipse 80% 60% at 20% 20%, rgba(99,102,241,0.18) 0%, transparent 60%),
          radial-gradient(ellipse 60% 50% at 80% 80%, rgba(139,92,246,0.14) 0%, transparent 60%),
          radial-gradient(ellipse 50% 40% at 50% 50%, rgba(59,130,246,0.08) 0%, transparent 70%);
      }
      .light-theme & {
        background:
          radial-gradient(ellipse 80% 60% at 20% 20%, rgba(99,102,241,0.15) 0%, transparent 60%),
          radial-gradient(ellipse 60% 50% at 80% 80%, rgba(168,85,247,0.12) 0%, transparent 60%),
          radial-gradient(ellipse 50% 40% at 50% 50%, rgba(59,130,246,0.10) 0%, transparent 70%);
      }
    }

    /* Animated floating blobs */
    .auth-blob {
      position: absolute;
      border-radius: 50%;
      filter: blur(72px);
      pointer-events: none;
      z-index: 0;
      animation: blobFloat 8s ease-in-out infinite alternate;
    }
    .blob-1 {
      width: 420px;
      height: 420px;
      top: -100px;
      left: -120px;
      animation-delay: 0s;
      .dark-theme & { background: rgba(99,102,241,0.22); }
      .light-theme & { background: rgba(99,102,241,0.18); }
    }
    .blob-2 {
      width: 320px;
      height: 320px;
      bottom: -80px;
      right: -80px;
      animation-delay: -3s;
      .dark-theme & { background: rgba(139,92,246,0.20); }
      .light-theme & { background: rgba(139,92,246,0.15); }
    }
    .blob-3 {
      width: 240px;
      height: 240px;
      top: 50%;
      right: 15%;
      animation-delay: -5s;
      .dark-theme & { background: rgba(59,130,246,0.15); }
      .light-theme & { background: rgba(59,130,246,0.12); }
    }

    @keyframes blobFloat {
      0%   { transform: translate(0, 0) scale(1); }
      50%  { transform: translate(30px, -20px) scale(1.05); }
      100% { transform: translate(-20px, 30px) scale(0.97); }
    }

    /* Subtle dot grid overlay */
    .auth-grid-overlay {
      position: absolute;
      inset: 0;
      z-index: 0;
      pointer-events: none;
      .dark-theme & {
        background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
        background-size: 28px 28px;
      }
      .light-theme & {
        background-image: radial-gradient(circle, rgba(99,102,241,0.08) 1px, transparent 1px);
        background-size: 28px 28px;
      }
    }

    .theme-toggle-floating {
      position: absolute !important;
      top: 24px;
      right: 24px;
      z-index: 10;
      color: #9ca3af;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;

      .light-theme & {
        color: #475569;
      }

      &:hover {
        transform: rotate(30deg) scale(1.1);
        color: #6366f1;
        .light-theme & {
          color: #4f46e5;
        }
      }
    }

    .auth-card {
      width: 100%;
      max-width: 420px;
      padding: 32px 24px;
      border-radius: 16px;
      z-index: 2;
      backdrop-filter: blur(2px);
      border: 1px solid;
      transition: all 0.3s ease;

      .dark-theme & {
        background-color: #17171e;
        border-color: #262631;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
      }
      .light-theme & {
        background-color: #ffffff;
        border-color: #cbd5e1;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
      }
    }

    mat-card-header {
      flex-direction: column;
      align-items: center;
      margin-bottom: 24px;
      text-align: center;
    }

    .brand-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 4px;
      
      .brand-icon {
        font-size: 28px;
        color: #6366f1;
      }

      h1 {
        font-family: 'Outfit', sans-serif;
        font-size: 24px;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
      }
    }

    mat-card-subtitle {
      font-family: 'Outfit', sans-serif;
      font-size: 14px;
      color: #9ca3af;
      margin: 0;
    }

    .full-width {
      width: 100%;
      margin-bottom: 12px;
    }

    .submit-btn {
      height: 48px;
      font-size: 15px;
      font-weight: 600;
      border-radius: 8px;
      background-color: #6366f1;
      color: #ffffff;
      margin-top: 12px;
      
      &:hover:not([disabled]) {
        background-color: #4f46e5;
      }
    }

    .auth-footer {
      margin-top: 24px;
      text-align: center;
      font-size: 13px;
      color: #9ca3af;

      .auth-link {
        color: #6366f1;
        text-decoration: none;
        font-weight: 500;
        
        &:hover {
          text-decoration: underline;
        }
      }
    }
  `]
})
export class LoginComponent implements OnInit {
  private fb = inject(FormBuilder);
  public authService = inject(AuthService);
  private router = inject(Router);
  private snackBar = inject(MatSnackBar);

  loginForm!: FormGroup;
  isLoading = signal<boolean>(false);
  hidePassword = signal<boolean>(true);

  ngOnInit(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/dashboard']);
    }

    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required]]
    });
  }

  togglePasswordVisibility(): void {
    this.hidePassword.update(v => !v);
  }

  onSubmit(): void {
    if (this.loginForm.invalid) return;

    this.isLoading.set(true);
    this.authService.login(this.loginForm.value).subscribe({
      next: () => {
        this.isLoading.set(false);
        this.router.navigate(['/dashboard']);
        this.snackBar.open('Welcome back!', 'Close', { duration: 3000 });
      },
      error: (err) => {
        this.isLoading.set(false);
        const errMsg = err.error?.detail || 'Authentication failed. Please verify credentials.';
        this.snackBar.open(errMsg, 'Close', { duration: 5000 });
      }
    });
  }
}
