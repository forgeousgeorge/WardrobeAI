import { useState } from 'react'
import { OutfitSuggestion as OutfitSuggestionType, outfitsApi } from '../../api/outfits'
import WeatherBanner from './WeatherBanner'
import ClothingCard from '../Clothing/ClothingCard'

interface Props {
  suggestion: OutfitSuggestionType
  onRated?: (updated: OutfitSuggestionType) => void
}

export default function OutfitSuggestionCard({ suggestion, onRated }: Props) {
  const [rating, setRating] = useState(suggestion.user_rating)
  const [submitting, setSubmitting] = useState(false)

  async function handleRate(value: number) {
    setSubmitting(true)
    try {
      const { data } = await outfitsApi.rate(suggestion.id, value)
      setRating(data.user_rating)
      onRated?.(data)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      {suggestion.weather_snapshot && <WeatherBanner weather={suggestion.weather_snapshot} />}

      <div className="px-4 mt-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-gray-800 capitalize">
            {suggestion.occasion_tag || 'casual'} outfit
          </h2>
          <span className="text-xs text-gray-400">
            {new Date(suggestion.suggested_date).toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
          </span>
        </div>

        {suggestion.reasoning && (
          <p className="text-sm text-gray-600 mb-4 bg-white rounded-xl p-3 shadow-sm">
            {suggestion.reasoning}
          </p>
        )}

        {suggestion.clothing_details && suggestion.clothing_details.length > 0 && (
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            {suggestion.clothing_details.map((item) => (
              <ClothingCard key={item.id} item={item} />
            ))}
          </div>
        )}

        {/* Rating */}
        <div className="bg-white rounded-xl p-4 shadow-sm">
          <p className="text-sm text-gray-600 mb-2 text-center">How was this outfit?</p>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => handleRate(star)}
                disabled={submitting}
                className={`text-2xl transition-transform active:scale-110 ${
                  rating && star <= rating ? 'text-yellow-400' : 'text-gray-300'
                }`}
              >
                ★
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
