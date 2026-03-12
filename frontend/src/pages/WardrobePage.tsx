import { useEffect, useState } from 'react'
import { ClothingItem, clothingApi } from '../api/clothing'
import PhotoUploader from '../components/Camera/PhotoUploader'
import ClothingGrid from '../components/Clothing/ClothingGrid'
import ClothingDetailModal from '../components/Clothing/ClothingDetailModal'
import { useWardrobeStore } from '../stores/wardrobeStore'

export default function WardrobePage() {
  const { items, loading, setItems, removeItem, setLoading } = useWardrobeStore()
  const [showUploader, setShowUploader] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedItem, setSelectedItem] = useState<ClothingItem | null>(null)

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const { data } = await clothingApi.list()
        setItems(data)
      } catch {
        setError('Failed to load wardrobe')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleArchive(id: string) {
    try {
      await clothingApi.delete(id)
      removeItem(id)
    } catch {
      // ignore
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between px-4 pt-[calc(1rem+env(safe-area-inset-top))] pb-2 bg-white border-b border-gray-100">
        <h1 className="text-xl font-bold text-gray-900">My Wardrobe</h1>
        <button
          onClick={() => setShowUploader((v) => !v)}
          className="flex items-center gap-1.5 bg-brand-600 text-white text-sm font-medium px-4 py-2 rounded-xl active:bg-brand-700"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add Item
        </button>
      </div>

      {showUploader && (
        <div className="bg-white border-b border-gray-100">
          <PhotoUploader />
        </div>
      )}

      {error && <p className="text-center text-red-500 text-sm py-4">{error}</p>}

      {loading ? (
        <div className="flex justify-center py-16">
          <div className="w-8 h-8 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <ClothingGrid items={items} onSelect={setSelectedItem} onArchive={handleArchive} />
      )}

      <ClothingDetailModal
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
        onArchive={handleArchive}
      />
    </div>
  )
}
