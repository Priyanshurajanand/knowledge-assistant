export interface User {
  id: string;
  email: string;
  name?: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UserSettings {
  preferred_provider: string;
  preferred_model: string;
  dark_mode: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
