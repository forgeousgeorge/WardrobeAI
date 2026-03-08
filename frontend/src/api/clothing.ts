import api from './client'

export interface ClothingItem {
  id: string
  user_id: string
  image_url: string | null
  category: string
  subcategory: string | null
  primary_color: string | null
  secondary_colors: string[] | null
  style_tags: string[] | null
  season_tags: string[] | null
  warmth_level: number | null
  brand: string | null
  notes: string | null
  is_active: boolean
  created_at: string
}

export const clothingApi = {
  upload: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post<ClothingItem>('/clothing/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  list: (params?: { category?: string; season?: string; is_active?: boolean; page?: number; limit?: number }) =>
    api.get<ClothingItem[]>('/clothing/', { params }),

  get: (id: string) => api.get<ClothingItem>(`/clothing/${id}`),

  update: (id: string, data: Partial<Pick<ClothingItem, 'brand' | 'notes' | 'style_tags' | 'season_tags' | 'category' | 'subcategory'>>) =>
    api.patch<ClothingItem>(`/clothing/${id}`, data),

  delete: (id: string) => api.delete(`/clothing/${id}`),

  toggleArchive: (id: string) => api.post<ClothingItem>(`/clothing/${id}/archive`),
}
