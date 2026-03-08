import { create } from 'zustand'
import { ClothingItem } from '../api/clothing'

interface WardrobeState {
  items: ClothingItem[]
  loading: boolean
  setItems: (items: ClothingItem[]) => void
  prependItem: (item: ClothingItem) => void
  updateItem: (id: string, item: ClothingItem) => void
  removeItem: (id: string) => void
  setLoading: (loading: boolean) => void
}

export const useWardrobeStore = create<WardrobeState>((set) => ({
  items: [],
  loading: false,
  setItems: (items) => set({ items }),
  prependItem: (item) => set((state) => ({ items: [item, ...state.items] })),
  updateItem: (id, item) =>
    set((state) => ({ items: state.items.map((i) => (i.id === id ? item : i)) })),
  removeItem: (id) => set((state) => ({ items: state.items.filter((i) => i.id !== id) })),
  setLoading: (loading) => set({ loading }),
}))
