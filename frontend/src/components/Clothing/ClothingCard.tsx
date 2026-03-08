import { ClothingItem } from '../../api/clothing'

const categoryEmoji: Record<string, string> = {
  top: '👕', bottom: '👖', outerwear: '🧥', shoes: '👟',
  accessory: '👜', full_outfit: '👗', unknown: '❓',
}

interface Props {
  item: ClothingItem
  onArchive?: (id: string) => void
}

export default function ClothingCard({ item, onArchive }: Props) {
  return (
    <div className="relative rounded-2xl overflow-hidden bg-white shadow-sm">
      <div className="aspect-[3/4] bg-gray-100">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.subcategory || item.category}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-4xl">
            {categoryEmoji[item.category] || '👕'}
          </div>
        )}
      </div>
      <div className="p-2">
        <p className="text-xs font-semibold text-gray-800 truncate capitalize">
          {item.subcategory || item.category}
        </p>
        {item.primary_color && (
          <p className="text-xs text-gray-500 capitalize">{item.primary_color}</p>
        )}
        {item.style_tags && item.style_tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-1">
            {item.style_tags.slice(0, 2).map((tag) => (
              <span key={tag} className="text-[10px] bg-brand-50 text-brand-700 px-1.5 py-0.5 rounded-full capitalize">
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>
      {onArchive && (
        <button
          onClick={() => onArchive(item.id)}
          className="absolute top-2 right-2 bg-white/80 rounded-full p-1.5 text-gray-500 active:bg-gray-100"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8l1 12a2 2 0 002 2h8a2 2 0 002-2l1-12M10 12v4m4-4v4" />
          </svg>
        </button>
      )}
    </div>
  )
}
