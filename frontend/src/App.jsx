import { useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'
import ErrorBoundary from './components/common/ErrorBoundary'

// Pages
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ExplorePage from './pages/ExplorePage'
import ProfilePage from './pages/ProfilePage'
import SongDetailPage from './pages/SongDetailPage'
import PlaylistPage from './pages/PlaylistPage'
import UploadPage from './pages/UploadPage'
import FeedPage from './pages/FeedPage'
import CommunityPage from './pages/CommunityPage'
import PeoplePage from './pages/PeoplePage'
import ComposePage from './pages/ComposePage'
import CreatePage from './pages/CreatePage'
import NotFoundPage from './pages/NotFoundPage'
import SettingsPage from './pages/SettingsPage'

// Layout
import MainLayout from './components/layout/MainLayout'
import Player from './components/player/Player'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuthStore()
  if (loading) return (
    <div className="flex items-center justify-center h-screen">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
  return isAuthenticated ? children : <Navigate to="/login" />
}

export default function App() {
  const { fetchProfile } = useAuthStore()

  useEffect(() => {
    if (localStorage.getItem('access_token')) {
      fetchProfile()
    } else {
      useAuthStore.setState({ loading: false })
    }
  }, [fetchProfile])

  return (
    <ErrorBoundary>
      <>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(12,12,28,0.98)',
              color: '#fff',
              border: '1px solid rgba(99,102,241,0.25)',
              backdropFilter: 'blur(16px)',
              borderRadius: '12px',
              fontSize: '13px',
              padding: '12px 16px',
              boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            },
            success: { iconTheme: { primary: '#6366f1', secondary: '#fff' } },
            error: { iconTheme: { primary: '#f43f5e', secondary: '#fff' } },
          }}
        />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<MainLayout />}>
            <Route index element={<HomePage />} />
            <Route path="explore" element={<ExplorePage />} />
            <Route path="feed" element={<PrivateRoute><FeedPage /></PrivateRoute>} />
            <Route path="community" element={<CommunityPage />} />
            <Route path="people" element={<PeoplePage />} />
            <Route path="upload" element={<PrivateRoute><UploadPage /></PrivateRoute>} />
            <Route path="compose" element={<Navigate to="/create" replace />} />
            <Route path="create" element={<CreatePage />} />
            <Route path="settings" element={<PrivateRoute><SettingsPage /></PrivateRoute>} />
            <Route path="profile/:username" element={<ProfilePage />} />
            <Route path="songs/:id" element={<SongDetailPage />} />
            <Route path="playlists/:id" element={<PlaylistPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
        <Player />
      </>
    </ErrorBoundary>
  )
}
