import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-not-found',
  standalone: true,
  imports: [RouterLink, MatButtonModule],
  template: `
    <div class="not-found-container fade-in-entry">
      <h1>404</h1>
      <h2>Page Not Found</h2>
      <p>The page you are looking for does not exist or has been relocated.</p>
      <button mat-flat-button color="primary" routerLink="/">Go to Dashboard</button>
    </div>
  `,
  styles: [`
    .not-found-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
      height: 100vh;
      width: 100%;
      text-align: center;
      background-color: #0b0b0e;
      color: #f3f4f6;
      padding: 24px;
    }

    h1 {
      font-family: 'Outfit', sans-serif;
      font-size: 120px;
      font-weight: 800;
      line-height: 1;
      margin: 0;
      color: #6366f1;
      letter-spacing: -2px;
    }

    h2 {
      font-family: 'Outfit', sans-serif;
      font-size: 28px;
      font-weight: 600;
      margin: 12px 0 8px;
    }

    p {
      font-size: 15px;
      color: #9ca3af;
      max-width: 400px;
      margin-bottom: 24px;
      line-height: 1.5;
    }

    button {
      height: 44px;
      border-radius: 8px;
      font-weight: 600;
      background-color: #6366f1;
      
      &:hover {
        background-color: #4f46e5;
      }
    }
  `]
})
export class NotFoundComponent {}
