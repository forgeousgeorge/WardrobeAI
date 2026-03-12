import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ThemeKey = 'light' | 'dark' | 'spring' | 'summer' | 'autumn' | 'winter'

export const THEME_LABELS: Record<ThemeKey, string> = {
  light: 'Light',
  dark: 'Dark',
  spring: 'Spring',
  summer: 'Summer',
  autumn: 'Autumn',
  winter: 'Winter',
}

interface ThemeState {
  theme: ThemeKey
  setTheme: (t: ThemeKey) => void
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: 'light',
      setTheme: (theme) => set({ theme }),
    }),
    { name: 'wardrobe-theme' }
  )
)
