import { Component, OnInit, effect, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { AuthService } from './core/services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <router-outlet></router-outlet>
  `,
  styles: [`
    :host {
      display: block;
      height: 100%;
    }
  `]
})
export class AppComponent implements OnInit {
  private authService = inject(AuthService);

  constructor() {
    // Reactively watch for dark mode signal changes and toggle classes on body
    effect(() => {
      const isDark = this.authService.darkMode();
      const body = document.body;
      if (isDark) {
        body.classList.add('dark-theme');
        body.classList.remove('light-theme');
      } else {
        body.classList.add('light-theme');
        body.classList.remove('dark-theme');
      }
    });
  }

  ngOnInit(): void {
    // Attempt token automatic login on startup
    this.authService.autoLogin();
  }
}
