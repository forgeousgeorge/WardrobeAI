import api from './client'

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface User {
  id: string
  email: string
  display_name: string | null
  city: string | null
  country_code: string | null
  created_at: string
}

export const authApi = {
  register: (email: string, password: string, display_name?: string) =>
    api.post<TokenPair>('/auth/register', { email, password, display_name }),

  login: (email: string, password: string) =>
    api.post<TokenPair>('/auth/login', { email, password }),

  logout: (refresh_token: string) =>
    api.post('/auth/logout', { refresh_token }),

  me: () => api.get<User>('/auth/me'),

  updateMe: (data: { display_name?: string; city?: string; country_code?: string }) =>
    api.patch<User>('/auth/me', data),
}
