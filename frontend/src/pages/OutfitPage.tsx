import { useEffect, useState } from 'react'
import { OutfitSuggestion, outfitsApi } from '../api/outfits'
import OutfitSuggestionCard from '../components/Outfit/OutfitSuggestion'

const OCCASIONS = ['casual', 'work', 'outdoor', 'formal', 'evening']

export default function OutfitPage() {
  const [suggestion, setSuggestion] = useState<OutfitSuggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [occasion, setOccasion] = useState('casual')
  const [error, setError] = useState<string | null>(null)

  async function fetchSuggestion(occ: string) {
    setLoading(true)
    setError(null)
    try {
      const today = new Date().toISOString().split('T')[0]
      const { data } = await outfitsApi.suggest({ for_date: today, occasion: occ })
      setSuggestion(data)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Failed to get outfit suggestion')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSuggestion(occasion)
  }, [occasion])

  return (
    <div>
      <div className="px-4 pt-[calc(1rem+env(safe-area-inset-top))] pb-3 bg-white border-b border-gray-100">
        <h1 className="text-xl font-bold text-gray-900 mb-3">Today's Outfit</h1>
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
          {OCCASIONS.map((occ) => (
            <button
              key={occ}
              onClick={() => setOccasion(occ)}
              className={`flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium capitalize transition-colors ${
                occasion === occ
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-600 active:bg-gray-200'
              }`}
            >
              {occ}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-20">
          <div className="w-10 h-10 border-4 border-brand-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm text-gray-500">Picking the perfect outfit…</p>
        </div>
      ) : error ? (
        <div className="text-center py-16 px-6">
          <p className="text-gray-500 text-sm mb-4">{error}</p>
          <button
            onClick={() => fetchSuggestion(occasion)}
            className="text-brand-600 font-medium text-sm"
          >
            Try again
          </button>
        </div>
      ) : suggestion ? (
        <OutfitSuggestionCard suggestion={suggestion} onRated={setSuggestion} />
      ) : null}
    </div>
  )
}
