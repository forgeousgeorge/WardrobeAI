import { useRef, useState } from 'react'
import { clothingApi } from '../../api/clothing'
import { useWardrobeStore } from '../../stores/wardrobeStore'

export default function PhotoUploader() {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const prependItem = useWardrobeStore((s) => s.prependItem)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError(null)
  }

  async function handleUpload() {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const { data } = await clothingApi.upload(file)
      prependItem(data)
      setPreview(null)
      setFile(null)
      if (fileInputRef.current) fileInputRef.current.value = ''
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg || 'Upload failed. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  function handleRetake() {
    setPreview(null)
    setFile(null)
    setError(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  return (
    <div className="p-4">
      {!preview ? (
        <label className="flex flex-col items-center justify-center w-full h-40 border-2 border-dashed border-brand-500 rounded-2xl cursor-pointer bg-brand-50 active:bg-brand-100 transition-colors">
          <svg className="w-10 h-10 text-brand-500 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-sm text-brand-600 font-medium">Take photo or choose from library</span>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={handleFileChange}
          />
        </label>
      ) : (
        <div className="space-y-3">
          <div className="aspect-[3/4] w-full max-w-xs mx-auto rounded-2xl overflow-hidden bg-brand-50">
            <img src={preview} alt="Preview" className="w-full h-full object-cover" />
          </div>
          {uploading ? (
            <div className="flex flex-col items-center py-4">
              <div className="w-8 h-8 rounded-full bg-brand-500 animate-pulse mb-2" />
              <p className="text-sm text-gray-600">Analyzing your item with AI…</p>
            </div>
          ) : (
            <div className="flex gap-3">
              <button
                onClick={handleRetake}
                className="flex-1 py-3 rounded-xl border border-brand-300 text-brand-700 font-medium text-sm"
              >
                Retake
              </button>
              <button
                onClick={handleUpload}
                className="flex-1 py-3 rounded-xl bg-brand-600 text-white font-medium text-sm active:bg-brand-700"
              >
                Add to Wardrobe
              </button>
            </div>
          )}
          {error && <p className="text-red-500 text-sm text-center">{error}</p>}
        </div>
      )}
    </div>
  )
}
