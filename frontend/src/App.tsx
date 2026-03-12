import { useEffect } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/Layout/AppShell'
import { useAuthStore } from './stores/authStore'
import { useThemeStore } from './stores/themeStore'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import WardrobePage from './pages/WardrobePage'
import OutfitPage from './pages/OutfitPage'
import ProfilePage from './pages/ProfilePage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore()
  if (!accessToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { theme } = useThemeStore()
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
  }, [theme])

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={<Navigate to="/wardrobe" replace />} />
        <Route path="wardrobe" element={<WardrobePage />} />
        <Route path="outfit" element={<OutfitPage />} />
        <Route path="profile" element={<ProfilePage />} />
      </Route>
    </Routes>
  )
}
