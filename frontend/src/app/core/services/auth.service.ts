import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User, UserSettings, TokenResponse } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private http = inject(HttpClient);
  private router = inject(Router);

  // Core Authentication Signals
  currentUser = signal<User | null>(null);
  token = signal<string | null>(localStorage.getItem('access_token'));
  userSettings = signal<UserSettings | null>(null);
  darkMode = signal<boolean>(localStorage.getItem('dark_mode') === 'true');

  // Computed state
  isAuthenticated = computed(() => this.token() !== null);
  isAdmin = computed(() => this.currentUser()?.role === 'admin');

  login(credentials: { email: string; password: string }): Observable<TokenResponse> {
    return this.http.post<TokenResponse>(`${environment.apiUrl}/auth/login`, credentials).pipe(
      tap((res) => {
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
        this.token.set(res.access_token);
        
        // Fetch profile and settings sequentially
        this.loadProfile().subscribe();
        this.loadSettings().subscribe();
      })
    );
  }

  register(userData: any): Observable<User> {
    return this.http.post<User>(`${environment.apiUrl}/auth/register`, userData);
  }

  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    this.token.set(null);
    this.currentUser.set(null);
    this.userSettings.set(null);
    this.router.navigate(['/login']);
  }

  autoLogin(): void {
    const savedToken = localStorage.getItem('access_token');
    if (savedToken) {
      this.token.set(savedToken);
      this.loadProfile().subscribe({
        error: () => this.logout() // Log out on invalid token
      });
      this.loadSettings().subscribe();
    }
  }

  loadProfile(): Observable<User> {
    return this.http.get<User>(`${environment.apiUrl}/auth/me`).pipe(
      tap((user) => this.currentUser.set(user))
    );
  }

  loadSettings(): Observable<UserSettings> {
    return this.http.get<UserSettings>(`${environment.apiUrl}/auth/me/settings`).pipe(
      tap((settings) => {
        this.userSettings.set(settings);
        this.darkMode.set(settings.dark_mode);
        localStorage.setItem('dark_mode', String(settings.dark_mode));
      })
    );
  }

  updateSettings(settings: Partial<UserSettings>): Observable<UserSettings> {
    return this.http.put<UserSettings>(`${environment.apiUrl}/auth/me/settings`, settings).pipe(
      tap((newSettings) => {
        this.userSettings.set(newSettings);
        if (newSettings.dark_mode !== undefined) {
          this.darkMode.set(newSettings.dark_mode);
          localStorage.setItem('dark_mode', String(newSettings.dark_mode));
        }
      })
    );
  }

  toggleTheme(): void {
    const nextMode = !this.darkMode();
    this.darkMode.set(nextMode);
    localStorage.setItem('dark_mode', String(nextMode));
    
    if (this.isAuthenticated()) {
      this.updateSettings({ dark_mode: nextMode }).subscribe({
        error: (err) => console.error("Could not persist theme preference to backend:", err)
      });
    }
  }
}
