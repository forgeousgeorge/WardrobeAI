import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '../api/auth'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  setTokens: (access: string, refresh: string) => void
  setUser: (user: User) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (access, refresh) => set({ accessToken: access, refreshToken: refresh }),
      setUser: (user) => set({ user }),
      clearAuth: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    {
      name: 'wardrobe-auth',
      // Only persist refresh token and user to localStorage; access token lives in memory
      partialize: (state) => ({ refreshToken: state.refreshToken, user: state.user }),
    }
  )
)
