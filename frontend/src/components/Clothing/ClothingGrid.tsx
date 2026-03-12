import { ClothingItem } from '../../api/clothing'
import ClothingCard from './ClothingCard'

interface Props {
  items: ClothingItem[]
  onSelect?: (item: ClothingItem) => void
  onArchive?: (id: string) => void
}

export default function ClothingGrid({ items, onSelect, onArchive }: Props) {
  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center px-6">
        <div className="text-6xl mb-4">👗</div>
        <h3 className="text-lg font-semibold text-brand-700 mb-1">Your wardrobe is empty</h3>
        <p className="text-sm text-brand-500">Tap the camera button above to add your first clothing item.</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3 p-4">
      {items.map((item) => (
        <ClothingCard key={item.id} item={item} onSelect={onSelect} onArchive={onArchive} />
      ))}
    </div>
  )
}
