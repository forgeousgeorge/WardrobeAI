import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../api/auth'
import { useAuthStore } from '../stores/authStore'

export default function ProfilePage() {
  const navigate = useNavigate()
  const { user, refreshToken, setUser, clearAuth } = useAuthStore()
  const [form, setForm] = useState({
    display_name: user?.display_name || '',
    city: user?.city || '',
    country_code: user?.country_code || '',
  })
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  function update(field: string, value: string) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const { data } = await authApi.updateMe(form)
      setUser(data)
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } finally {
      setSaving(false)
    }
  }

  async function handleLogout() {
    if (refreshToken) {
      try { await authApi.logout(refreshToken) } catch { /* ignore */ }
    }
    clearAuth()
    navigate('/login')
  }

  return (
    <div>
      <div className="px-4 pt-[calc(1rem+env(safe-area-inset-top))] pb-4 bg-white border-b border-gray-100">
        <h1 className="text-xl font-bold text-gray-900">Profile</h1>
        <p className="text-sm text-gray-500">{user?.email}</p>
      </div>

      <div className="p-4">
        <form onSubmit={handleSave} className="bg-white rounded-2xl p-4 shadow-sm space-y-4">
          <h2 className="font-semibold text-gray-800">Account Settings</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
            <input
              type="text"
              value={form.display_name}
              onChange={(e) => update('display_name', e.target.value)}
              className="w-full rounded-xl border-gray-300 shadow-sm focus:ring-brand-500 focus:border-brand-500"
              placeholder="Your name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">City</label>
            <input
              type="text"
              value={form.city}
              onChange={(e) => update('city', e.target.value)}
              className="w-full rounded-xl border-gray-300 shadow-sm focus:ring-brand-500 focus:border-brand-500"
              placeholder="e.g. New York"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Country Code</label>
            <input
              type="text"
              maxLength={2}
              value={form.country_code}
              onChange={(e) => update('country_code', e.target.value.toUpperCase())}
              className="w-full rounded-xl border-gray-300 shadow-sm focus:ring-brand-500 focus:border-brand-500"
              placeholder="US"
            />
          </div>

          <button
            type="submit"
            disabled={saving}
            className="w-full py-3 rounded-xl bg-brand-600 text-white font-semibold text-sm active:bg-brand-700 disabled:opacity-60"
          >
            {saved ? 'Saved!' : saving ? 'Saving…' : 'Save Changes'}
          </button>
        </form>

        <button
          onClick={handleLogout}
          className="w-full mt-4 py-3 rounded-xl bg-red-50 text-red-600 font-semibold text-sm active:bg-red-100"
        >
          Sign Out
        </button>
      </div>
    </div>
  )
}
