import { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FiSearch, FiBell, FiSettings, FiX, FiMenu, FiMessageSquare } from 'react-icons/fi'
import { MdGraphicEq, MdAutoAwesome } from 'react-icons/md'
import useAuthStore from '../../store/authStore'
import SearchModal from '../search/SearchModal'
import MessagesDrawer from '../social/MessagesDrawer'
import api from '../../api/axios'
import clsx from 'clsx'

const PAGE_TITLES = {
  '/': { title: 'Sonavia Home', sub: 'Khám phá không gian âm nhạc AI thế hệ mới' },
  '/create': { title: 'Sonavia Studio', sub: 'Sáng tác nhạc & cất giọng hát AI chân thực' },
  '/explore': { title: 'Khám phá Sonavia', sub: 'Bảng xếp hạng & kho nhạc đa thể loại' },
  '/compose': { title: 'AI Sound Lab', sub: 'Phòng hòa âm & tinh chỉnh tham số MusicGen' },
  '/community': { title: 'Cộng đồng Sonavia', sub: 'Chia sẻ giai điệu & kết nối đam mê' },
  '/people': { title: 'Mạng lưới Nghệ sĩ', sub: 'Theo dõi & hợp tác cùng các nhà sáng tạo' },
  '/feed': { title: 'Bảng tin Âm nhạc', sub: 'Giai điệu mới từ người bạn theo dõi' },
  '/upload': { title: 'Phát hành Âm nhạc', sub: 'Đăng tải sản phẩm âm thanh chất lượng cao' },
  '/settings': { title: 'Cài đặt Tài khoản', sub: 'Hồ sơ cá nhân & tùy biến giao diện' },
}

function formatNotifTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffSec = Math.floor((now - d) / 1000)
  if (diffSec < 60) return 'Vừa xong'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} phút trước`
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} giờ trước`
  return `${d.getDate()}/${d.getMonth() + 1}`
}

export default function Topbar({ onToggleMobileSidebar }) {
  const [showSearch, setShowSearch] = useState(false)
  const [unread, setUnread] = useState(0)
  const [unreadMessages, setUnreadMessages] = useState(0)
  const [showNotif, setShowNotif] = useState(false)
  const [showMessages, setShowMessages] = useState(false)
  const [notifications, setNotifications] = useState([])
  const { user, isAuthenticated } = useAuthStore()
  const location = useLocation()
  const navigate = useNavigate()

  const pageInfo = (() => {
    if (PAGE_TITLES[location.pathname]) return PAGE_TITLES[location.pathname]
    if (location.pathname.startsWith('/profile/')) return { title: 'Hồ sơ Nghệ sĩ', sub: 'Thông tin cá nhân & kho bài hát sáng tác' }
    if (location.pathname.startsWith('/songs/')) return { title: 'Chi tiết Bài hát', sub: 'Nghe nhạc, lời bài hát & thảo luận' }
    if (location.pathname.startsWith('/playlists/')) return { title: 'Danh sách Phát', sub: 'Bộ sưu tập giai điệu chọn lọc' }
    return { title: 'Sonavia', sub: 'AI Music & Sound Lab' }
  })()

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setShowSearch(prev => !prev)
      }
      if (e.key === 'Escape') {
        setShowNotif(false)
        setShowMessages(false)
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])

  // Fetch real notifications and message count
  useEffect(() => {
    if (!isAuthenticated || !user?.username) {
      setUnread(0)
      setUnreadMessages(0)
      setNotifications([])
      return
    }

    const fetchAll = async () => {
      try {
        const notifRes = await api.get('/social/notifications/')
        const list = notifRes.data?.results || notifRes.data || []
        setNotifications(Array.isArray(list) ? list : [])
        setUnread(Array.isArray(list) ? list.filter(n => !n.is_read).length : 0)
      } catch { }

      try {
        const convRes = await api.get('/social/messages/conversations/')
        if (Array.isArray(convRes.data)) {
          const totalUnread = convRes.data.reduce((acc, c) => acc + (c.unread_count || 0), 0)
          setUnreadMessages(totalUnread)
        }
      } catch { }
    }

    fetchAll()
    const timer = setInterval(fetchAll, 10000)
    return () => clearInterval(timer)
  }, [isAuthenticated, user?.username])

  const markAllRead = async () => {
    try {
      await api.post('/social/notifications/read/')
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })))
      setUnread(0)
    } catch { }
  }

  const handleNotificationClick = async (notif) => {
    setShowNotif(false)
    if (!notif.is_read) {
      api.post('/social/notifications/read/', { id: notif.id }).catch(() => {})
      setNotifications(prev => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n))
      setUnread(prev => Math.max(0, prev - 1))
    }

    if (notif.verb === 'message') {
      setShowMessages(true)
    } else if (notif.target_type === 'song' && notif.target_id) {
      navigate(`/songs/${notif.target_id}`)
    } else if (notif.target_type === 'post') {
      navigate('/community')
    } else if (notif.actor?.username) {
      navigate(`/profile/${notif.actor.username}`)
    }
  }

  return (
    <>
      {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}
      {showMessages && <MessagesDrawer isOpen={showMessages} onClose={() => setShowMessages(false)} />}
      {showNotif && <div className="fixed inset-0 z-20" onClick={() => setShowNotif(false)} />}

      <header className="h-16 flex items-center justify-between gap-4 px-6 shrink-0 sticky top-0 z-20 border-b border-white/[0.06] bg-[#070814]/80 backdrop-blur-2xl">
        {/* Page Title & Breadcrumb + Mobile Menu Button */}
        <div className="flex items-center gap-2.5 sm:gap-3 min-w-0">
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            className="md:hidden p-2 rounded-xl text-white/70 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.08] transition-colors shrink-0"
            title="Mở menu Sonavia">
            <FiMenu size={18} />
          </button>

          <div className="hidden sm:block">
            <div className="flex items-center gap-2">
              <h1 className="text-sm sm:text-base font-bold text-white leading-none tracking-tight truncate">
                {pageInfo.title}
              </h1>
              {location.pathname === '/create' && (
                <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded-full bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 flex items-center gap-1 shadow-[0_0_8px_rgba(34,211,238,0.2)]">
                  <MdAutoAwesome size={10} /> Pro
                </span>
              )}
            </div>
            <p className="text-[11px] mt-1 text-white/40 leading-none truncate max-w-sm">
              {pageInfo.sub}
            </p>
          </div>
        </div>

        {/* Global Search Bar (Sonavia Quick Find) */}
        <div className="flex-1 max-w-md mx-2">
          <button
            onClick={() => setShowSearch(true)}
            className="w-full flex items-center gap-3 px-4 py-2 rounded-2xl bg-white/[0.04] hover:bg-white/[0.07] border border-white/[0.08] hover:border-indigo-500/40 transition-all duration-200 group text-left shadow-sm">
            <FiSearch size={15} className="text-white/40 group-hover:text-cyan-400 transition-colors" />
            <span className="text-sm text-white/35 group-hover:text-white/70 flex-1 truncate">
              Tìm bài hát, nghệ sĩ hoặc thể loại...
            </span>
            <kbd className="hidden sm:inline-flex text-[10px] font-mono px-2 py-0.5 rounded-md bg-white/[0.06] text-white/50 border border-white/10 group-hover:border-indigo-400/30">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right Actions & Profile */}
        <div className="flex items-center gap-2.5 shrink-0">
          {/* Studio Quick Link */}
          <Link
            to="/create"
            className="hidden xl:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-cyan-300 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/20 transition-all">
            <MdGraphicEq size={14} className="text-cyan-400" />
            <span>Studio</span>
          </Link>

          {/* Direct Messaging Icon */}
          {isAuthenticated && (
            <button
              onClick={() => setShowMessages(true)}
              className="relative w-9 h-9 flex items-center justify-center rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-white/60 hover:text-white border border-white/[0.06] transition-all"
              title="Tin nhắn trực tiếp">
              <FiMessageSquare size={16} />
              {unreadMessages > 0 && (
                <span className="absolute -top-1 -right-1 min-w-[16px] h-[16px] rounded-full text-[9px] font-extrabold text-white flex items-center justify-center px-1 bg-gradient-to-r from-cyan-500 to-indigo-600 shadow-[0_0_8px_rgba(6,182,212,0.6)] animate-pulse">
                  {unreadMessages > 9 ? '9+' : unreadMessages}
                </span>
              )}
            </button>
          )}

          {/* Notifications Dropdown */}
          {isAuthenticated && (
            <div className="relative">
              <button
                onClick={() => setShowNotif(!showNotif)}
                className="relative w-9 h-9 flex items-center justify-center rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-white/60 hover:text-white border border-white/[0.06] transition-all"
                title="Thông báo">
                <FiBell size={16} />
                {unread > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-[16px] h-[16px] rounded-full text-[9px] font-extrabold text-white flex items-center justify-center px-1 bg-gradient-to-r from-rose-500 to-indigo-500 shadow-[0_0_8px_rgba(244,63,94,0.6)] animate-pulse">
                    {unread > 9 ? '9+' : unread}
                  </span>
                )}
              </button>

              {/* Dropdown Notifications Body */}
              {showNotif && (
                <div
                  className="absolute right-0 top-12 z-30 w-80 sm:w-96 rounded-3xl overflow-hidden sonavia-glass border border-white/10 shadow-2xl animate-scale-in"
                  style={{
                    background: 'linear-gradient(180deg, rgba(16, 17, 38, 0.98) 0%, rgba(9, 10, 24, 0.98) 100%)',
                  }}
                >
                  <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08] bg-white/[0.02]">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">Thông báo</span>
                      {unread > 0 && (
                        <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                          {unread} mới
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {unread > 0 && (
                        <button
                          onClick={markAllRead}
                          className="text-[11px] text-cyan-400 hover:text-cyan-300 transition-colors">
                          Đã đọc tất cả
                        </button>
                      )}
                      <button
                        onClick={() => setShowNotif(false)}
                        className="text-white/40 hover:text-white transition-colors p-1">
                        <FiX size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="max-h-[360px] overflow-y-auto divide-y divide-white/[0.04] scrollbar-thin scrollbar-thumb-white/10">
                    {notifications.length > 0 ? (
                      notifications.map((n) => {
                        const actorName = n.actor?.username || 'Hệ thống'
                        return (
                          <div
                            key={n.id}
                            onClick={() => handleNotificationClick(n)}
                            className={clsx(
                              "px-4 py-3 flex items-start gap-3 hover:bg-white/[0.04] cursor-pointer transition-colors relative",
                              !n.is_read && "bg-cyan-500/[0.05]"
                            )}
                          >
                            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-cyan-500 flex items-center justify-center text-xs font-bold text-white shrink-0 overflow-hidden shadow-sm">
                              {n.actor?.avatar ? (
                                <img src={n.actor.avatar} alt={actorName} className="w-full h-full object-cover" />
                              ) : (
                                actorName.slice(0, 1).toUpperCase()
                              )}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-xs text-white/90 leading-snug">
                                <span className="font-bold text-white">{actorName} </span>
                                <span className="text-white/70">{n.text || n.verb}</span>
                              </p>
                              <span className="text-[10px] text-white/35 mt-1 block">
                                {formatNotifTime(n.created_at)}
                              </span>
                            </div>
                            {!n.is_read && (
                              <span className="w-2 h-2 rounded-full bg-cyan-400 shrink-0 mt-1.5 shadow-[0_0_6px_#22d3ee]" />
                            )}
                          </div>
                        )
                      })
                    ) : (
                      <div className="py-8 text-center">
                        <p className="text-2xl mb-1.5">🎶</p>
                        <p className="text-xs text-white/50">Chưa có thông báo nào</p>
                        <p className="text-[11px] text-white/30 mt-0.5">Tất cả hoạt động đều đã cập nhật</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Settings Icon */}
          {isAuthenticated && (
            <Link
              to="/settings"
              className="w-9 h-9 flex items-center justify-center rounded-xl bg-white/[0.03] hover:bg-white/[0.08] text-white/60 hover:text-white border border-white/[0.06] transition-all"
              title="Cài đặt Sonavia">
              <FiSettings size={16} />
            </Link>
          )}

          {/* User Profile or Guest Actions */}
          {isAuthenticated && user ? (
            <Link
              to={`/profile/${user.username}`}
              className="flex items-center gap-2 pl-1 pr-3 py-1 rounded-xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/[0.06] transition-all group">
              <div className="w-7 h-7 rounded-lg overflow-hidden shrink-0 ring-1 ring-indigo-400/50">
                {user.avatar_url ? (
                  <img src={user.avatar_url} className="w-full h-full object-cover" alt={user.username} />
                ) : (
                  <div
                    className="w-full h-full flex items-center justify-center text-[10px] font-black text-white"
                    style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}>
                    {user.username?.[0]?.toUpperCase()}
                  </div>
                )}
              </div>
              <span className="text-xs font-semibold text-white/80 group-hover:text-white max-w-[90px] truncate">
                {user.username}
              </span>
            </Link>
          ) : (
            <div className="flex items-center gap-2">
              <Link
                to="/login"
                className="text-xs font-medium px-3 py-2 rounded-xl text-white/70 hover:text-white hover:bg-white/[0.05] transition-all">
                Đăng nhập
              </Link>
              <Link
                to="/register"
                className="text-xs font-bold px-4 py-2 rounded-xl text-white bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-500 hover:brightness-110 shadow-[0_2px_12px_rgba(99,102,241,0.35)] transition-all">
                Đăng ký
              </Link>
            </div>
          )}
        </div>
      </header>
    </>
  )
}
