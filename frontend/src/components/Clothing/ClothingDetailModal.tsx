import { useEffect } from 'react'
import { ClothingItem } from '../../api/clothing'

interface Props {
  item: ClothingItem | null
  onClose: () => void
  onArchive?: (id: string) => void
}

const warmthLabel = ['', 'Very Light', 'Light', 'Medium', 'Warm', 'Very Warm']

function TagList({ tags }: { tags: string[] }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((t) => (
        <span key={t} className="text-xs bg-brand-50 text-brand-700 px-2 py-0.5 rounded-full capitalize">
          {t}
        </span>
      ))}
    </div>
  )
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 py-2.5 border-b border-gray-100 last:border-0">
      <span className="text-xs text-gray-400 w-28 shrink-0 pt-0.5">{label}</span>
      <div className="flex-1 text-sm text-gray-800">{children}</div>
    </div>
  )
}

export default function ClothingDetailModal({ item, onClose, onArchive }: Props) {
  useEffect(() => {
    if (!item) return
    const handler = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [item, onClose])

  if (!item) return null

  const raw = item.classification_raw ?? {}
  const pattern = raw.pattern as string | undefined
  const silhouette = raw.silhouette as string | undefined
  const occasionTags = raw.occasion_tags as string[] | undefined
  const tempRange = raw.temp_range_c as { min: number; max: number } | undefined
  const confidence = raw.confidence as number | undefined

  function handleArchive() {
    if (onArchive) {
      onArchive(item!.id)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />

      {/* Sheet */}
      <div className="relative w-full bg-white rounded-t-3xl max-h-[90dvh] flex flex-col">
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-10 h-1 bg-gray-300 rounded-full" />
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 active:text-gray-600"
          aria-label="Close"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <div className="overflow-y-auto flex-1 px-4 pb-6">
          {/* Image */}
          <div className="w-full aspect-[3/4] bg-gray-100 rounded-2xl overflow-hidden mb-4">
            {item.image_url ? (
              <img src={item.image_url} alt={item.name ?? item.subcategory ?? item.category} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-6xl">👕</div>
            )}
          </div>

          {/* Name */}
          <h2 className="text-lg font-bold text-gray-900 mb-4 capitalize">
            {item.name ?? item.subcategory ?? item.category}
          </h2>

          {/* Classification fields */}
          <div className="mb-6">
            <Row label="Category">
              <span className="capitalize">{item.subcategory ?? item.category}</span>
            </Row>

            {item.primary_color && (
              <Row label="Color">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="capitalize">{item.primary_color}</span>
                  {item.secondary_colors && item.secondary_colors.length > 0 && (
                    <span className="text-gray-400 text-xs capitalize">+ {item.secondary_colors.join(', ')}</span>
                  )}
                </div>
              </Row>
            )}

            {pattern && pattern !== 'none' && (
              <Row label="Pattern">
                <span className="capitalize">{pattern}</span>
              </Row>
            )}

            {silhouette && (
              <Row label="Silhouette">
                <span className="capitalize">{silhouette}</span>
              </Row>
            )}

            {item.style_tags && item.style_tags.length > 0 && (
              <Row label="Style">
                <TagList tags={item.style_tags} />
              </Row>
            )}

            {occasionTags && occasionTags.length > 0 && (
              <Row label="Occasions">
                <TagList tags={occasionTags} />
              </Row>
            )}

            {item.season_tags && item.season_tags.length > 0 && (
              <Row label="Seasons">
                <TagList tags={item.season_tags} />
              </Row>
            )}

            {tempRange && (
              <Row label="Temperature">
                <span>{tempRange.min}–{tempRange.max}°C</span>
              </Row>
            )}

            {item.warmth_level != null && (
              <Row label="Warmth">
                <div className="flex items-center gap-1.5">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <div
                      key={n}
                      className={`w-3 h-3 rounded-full ${n <= item.warmth_level! ? 'bg-brand-500' : 'bg-gray-200'}`}
                    />
                  ))}
                  <span className="text-xs text-gray-400 ml-1">{warmthLabel[item.warmth_level]}</span>
                </div>
              </Row>
            )}

            {confidence != null && (
              <Row label="Confidence">
                <span>{Math.round(confidence * 100)}%</span>
              </Row>
            )}

            {item.brand && (
              <Row label="Brand">
                <span>{item.brand}</span>
              </Row>
            )}

            {item.notes && (
              <Row label="Notes">
                <span>{item.notes}</span>
              </Row>
            )}
          </div>

          {onArchive && (
            <button
              onClick={handleArchive}
              className="w-full py-3 rounded-2xl border border-red-200 text-red-500 text-sm font-medium active:bg-red-50"
            >
              Archive Item
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
