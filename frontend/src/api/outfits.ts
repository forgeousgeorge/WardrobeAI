import api from './client'
import { ClothingItem } from './clothing'

export interface OutfitSuggestion {
  id: string
  user_id: string
  suggested_date: string
  weather_snapshot: {
    temp_c: number
    feels_like_c: number
    temp_f: number
    feels_like_f: number
    description: string
    icon_code: string
    humidity: number
    wind_kph: number
    wind_mph: number
  } | null
  items: string[]
  reasoning: string | null
  occasion_tag: string | null
  user_rating: number | null
  created_at: string
  clothing_details: ClothingItem[] | null
}

export const outfitsApi = {
  suggest: (params?: { for_date?: string; occasion?: string }) =>
    api.get<OutfitSuggestion>('/outfits/suggest', { params }),

  list: (params?: { limit?: number; offset?: number }) =>
    api.get<OutfitSuggestion[]>('/outfits/', { params }),

  get: (id: string) => api.get<OutfitSuggestion>(`/outfits/${id}`),

  rate: (id: string, rating: number) =>
    api.post<OutfitSuggestion>(`/outfits/${id}/rate`, { rating }),
}
