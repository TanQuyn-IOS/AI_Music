import { useState, useEffect } from 'react'
import { Outlet, useLocation } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  // Tự động đóng sidebar mobile khi chuyển route
  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <div className="flex h-screen overflow-hidden relative bg-[#060713]">
      {/* ── Aurora Mesh Ambient Glowing Orbs (Ánh sáng cực quang nền sâu) ── */}
      <div className="fixed -top-32 -left-32 w-96 h-96 rounded-full bg-indigo-600/18 blur-[130px] pointer-events-none z-0 animate-pulse-slow" />
      <div className="fixed top-1/4 -right-32 w-[28rem] h-[28rem] rounded-full bg-cyan-500/14 blur-[140px] pointer-events-none z-0" />
      <div className="fixed -bottom-32 left-1/3 w-[32rem] h-[32rem] rounded-full bg-purple-600/14 blur-[160px] pointer-events-none z-0" />

      <Sidebar mobileOpen={mobileOpen} onCloseMobile={() => setMobileOpen(false)} />
      
      <div className="flex-1 flex flex-col min-w-0 z-10">
        <Topbar onToggleMobileSidebar={() => setMobileOpen(prev => !prev)} />
        <main className="flex-1 overflow-y-auto pb-36 scrollbar-thin">
          <div key={location.pathname} className="animate-page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
