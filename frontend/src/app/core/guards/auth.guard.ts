import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    // If user is accessing the admin route, check role
    if (state.url.startsWith('/admin') && authService.currentUser()?.role !== 'admin') {
      router.navigate(['/dashboard']);
      return false;
    }
    return true;
  }

  // Redirect to login page for unauthenticated access
  router.navigate(['/login']);
  return false;
};
