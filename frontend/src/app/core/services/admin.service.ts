import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User } from '../models/user.model';

@Injectable({
  providedIn: 'root'
})
export class AdminService {
  private http = inject(HttpClient);

  getStats(): Observable<any> {
    return this.http.get<any>(`${environment.apiUrl}/admin/stats`);
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${environment.apiUrl}/admin/users`);
  }

  updateUserRole(userId: string, role: string): Observable<User> {
    return this.http.put<User>(`${environment.apiUrl}/admin/users/${userId}/role`, null, {
      params: { role }
    });
  }

  toggleUserActive(userId: string): Observable<User> {
    return this.http.put<User>(`${environment.apiUrl}/admin/users/${userId}/toggle-active`, null);
  }
}
