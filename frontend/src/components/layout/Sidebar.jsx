import { NavLink, useNavigate, Link } from 'react-router-dom'
import {
  FiHome, FiCompass, FiUpload, FiUsers, FiUser,
  FiLogOut, FiSettings, FiRss, FiPlusCircle, FiX,
} from 'react-icons/fi'
import { MdGraphicEq, MdGroup, MdAutoAwesome, MdRadio } from 'react-icons/md'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const MUSIC_NAV = [
  { to: '/explore', icon: FiCompass, label: 'Khám phá nhạc' },
  { to: '/create', icon: MdGraphicEq, label: 'Phòng AI Studio', ai: true },
  { to: '/upload', icon: FiUpload, label: 'Tải nhạc lên' },
]

const SOCIAL_NAV = [
  { to: '/', icon: FiHome, label: 'Trang chủ', exact: true },
  { to: '/community', icon: MdGroup, label: 'Cộng đồng' },
  { to: '/people', icon: FiUsers, label: 'Nghệ sĩ & Bạn bè' },
  { to: '/feed', icon: FiRss, label: 'Bảng tin nghe' },
]

function NavItem({ to, icon: Icon, label, exact, ai, onClick }) {
  return (
    <NavLink
      to={to}
      end={exact}
      onClick={onClick}
      className={({ isActive }) => clsx(
        'group relative flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200',
        isActive
          ? 'bg-gradient-to-r from-indigo-500/15 via-purple-500/10 to-cyan-500/5 text-white font-semibold border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
          : ai
            ? 'text-accent-300/80 hover:text-white hover:bg-cyan-500/10'
            : 'text-white/60 hover:text-white hover:bg-white/[0.06]'
      )}>
      {({ isActive }) => (
        <>
          {/* Active left indicator bar */}
          {isActive && (
            <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-gradient-to-b from-cyan-400 via-indigo-500 to-purple-500 shadow-[0_0_8px_#22d3ee]" />
          )}

          <Icon
            size={18}
            className={clsx(
              'shrink-0 transition-transform duration-200 group-hover:scale-110',
              isActive
                ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]'
                : ai
                  ? 'text-cyan-400/80 group-hover:text-cyan-300'
                  : 'text-white/50 group-hover:text-indigo-300'
            )}
          />

          <span className="flex-1 truncate tracking-tight">{label}</span>

          {ai && (
            <span className="text-[10px] font-black px-1.5 py-0.5 rounded-md flex items-center gap-0.5 tracking-wider uppercase bg-cyan-400/15 text-cyan-300 border border-cyan-400/30 shadow-[0_0_8px_rgba(34,211,238,0.2)]">
              <MdAutoAwesome size={10} className="animate-spin-slow" />
              AI
            </span>
          )}
        </>
      )}
    </NavLink>
  )
}

export default function Sidebar({ mobileOpen = false, onCloseMobile }) {
  const { user, isAuthenticated, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    toast.success('Đã đăng xuất khỏi Sonavia')
    navigate('/login')
  }

  return (
    <>
      {/* Mobile Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 md:hidden animate-fade-in"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={clsx(
          'fixed md:static inset-y-0 left-0 z-50 w-64 md:w-60 shrink-0 flex flex-col h-screen select-none border-r border-white/[0.08] transition-transform duration-300 ease-in-out',
          mobileOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'
        )}
        style={{
          background: 'rgba(7, 9, 22, 0.75)',
          backdropFilter: 'blur(28px)',
          WebkitBackdropFilter: 'blur(28px)',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
        }}>

        {/* ── Brand Logo Sonavia & Mobile Close ── */}
        <div className="flex items-center justify-between px-5 py-4">
          <Link to="/" onClick={onCloseMobile} className="flex items-center gap-3.5 group">
            <div className="relative shrink-0">
              {/* Neon Aurora Glow behind logo */}
              <div
                className="absolute -inset-1 rounded-2xl blur-md opacity-70 group-hover:opacity-100 transition-opacity duration-300"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #7c3aed, #06b6d4)' }}
              />
              <div
                className="relative w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg border border-white/20"
                style={{
                  background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 40%, #0891b2 100%)',
                }}>
                {/* Custom Soundwave Vector Logo */}
                <svg className="w-5 h-5 text-cyan-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
                  <path d="M4 10v4" />
                  <path d="M8 6v12" />
                  <path d="M12 2v20" />
                  <path d="M16 8v8" />
                  <path d="M20 11v2" />
                </svg>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-extrabold text-lg text-white tracking-tight leading-none group-hover:text-cyan-300 transition-colors">
                  Sonavia
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee] animate-pulse" />
              </div>
              <p className="text-[10px] font-medium tracking-wide mt-1 text-white/40 leading-none">
                AI Music & Sound Lab
              </p>
            </div>
          </Link>

          {/* Close button on mobile */}
          <button
            onClick={onCloseMobile}
            className="md:hidden p-1.5 rounded-xl text-white/50 hover:text-white hover:bg-white/[0.08] transition-colors"
            title="Đóng menu">
            <FiX size={18} />
          </button>
        </div>

        {/* ── Nút TẠO NHẠC Sonavia Studio Nổi Bật ── */}
        <div className="px-4 mb-4">
          <NavLink
            to="/create"
            onClick={onCloseMobile}
            className={({ isActive }) => clsx(
              'relative overflow-hidden group flex items-center justify-center gap-2.5 w-full py-3.5 rounded-2xl font-black text-sm text-white transition-all duration-300 active:scale-[0.98] btn-shimmer',
              isActive
                ? 'ring-2 ring-cyan-400/80 shadow-[0_0_30px_rgba(34,211,238,0.55)] brightness-110'
                : 'hover:brightness-110 shadow-[0_8px_25px_rgba(99,102,241,0.45)]'
            )}
            style={{
              background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #06b6d4 100%)',
            }}>
            {/* Background Shimmer Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:animate-shimmer" />
            
            <FiPlusCircle size={18} className="text-cyan-200 group-hover:rotate-90 transition-transform duration-300" />
            <span className="tracking-wide">Tạo nhạc Sonavia</span>
          </NavLink>
        </div>

      {/* ── Music Nav Group ── */}
      <div className="px-3 mb-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] px-2 mb-2 text-indigo-300/50">
          Studio & Âm nhạc
        </p>
        <div className="space-y-1">
          {MUSIC_NAV.map(item => <NavItem key={item.to} {...item} />)}
        </div>
      </div>

      {/* ── Divider ── */}
      <div className="mx-4 my-2 border-t border-white/[0.06]" />

      {/* ── Social Group ── */}
      <div className="px-3 mb-2">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] px-2 mb-2 text-cyan-400/50">
          Cộng đồng Sonavia
        </p>
        <div className="space-y-1">
          {SOCIAL_NAV.map(item => <NavItem key={item.to} {...item} />)}
        </div>
      </div>

      <div className="flex-1" />

      {/* ── Sonavia Engine Card ── */}
      <div className="mx-3.5 mb-3 p-3 rounded-2xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-md hover:border-indigo-500/30 transition-all duration-200">
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-2">
            <span className="p-1 rounded-lg bg-indigo-500/20 text-cyan-300">
              <MdAutoAwesome size={13} />
            </span>
            <p className="text-xs font-bold text-white">Sonavia Engine 3.5</p>
          </div>
          <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399] animate-pulse" />
            Sẵn sàng
          </span>
        </div>
        <p className="text-[11px] text-white/50 leading-relaxed">
          Hệ sinh thái AI tạo nhạc, hòa âm & sinh lời tự động.
        </p>
      </div>

      {/* ── User Section ── */}
      <div className="border-t border-white/[0.08] bg-[#050610]/60 p-2">
        {isAuthenticated && user ? (
          <div className="rounded-2xl bg-white/[0.03] border border-white/[0.05] p-2">
            <Link
              to={`/profile/${user.username}`}
              className="flex items-center gap-3 p-1.5 rounded-xl hover:bg-white/[0.06] transition-colors group">
              <div className="relative shrink-0">
                {user.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    className="w-9 h-9 rounded-full object-cover ring-2 ring-indigo-500/40"
                    alt={user.username}
                  />
                ) : (
                  <div
                    className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-black text-white ring-2 ring-indigo-500/40"
                    style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}>
                    {user.username?.[0]?.toUpperCase()}
                  </div>
                )}
                <div
                  className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#060713] shadow-[0_0_6px_#34d399]"
                  title="Đang hoạt động"
                />
              </div>

              <div className="min-w-0 flex-1">
                <p className="text-sm font-bold text-white truncate leading-none group-hover:text-cyan-300 transition-colors">
                  {user.username}
                </p>
                <p className="text-[11px] mt-1 text-white/40 truncate">
                  {user.is_artist ? '✨ Nghệ sĩ Sonavia' : '🎧 Thành viên Sonavia'}
                </p>
              </div>
            </Link>

            <div className="flex items-center gap-1 mt-1 pt-1 border-t border-white/[0.05]">
              <Link
                to="/settings"
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs text-white/50 hover:text-white hover:bg-white/[0.05] transition-all">
                <FiSettings size={13} /> Cài đặt
              </Link>
              <span className="w-px h-3 bg-white/10" />
              <button
                onClick={handleLogout}
                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg text-xs text-rose-400/80 hover:text-rose-300 hover:bg-rose-500/10 transition-all">
                <FiLogOut size={13} /> Đăng xuất
              </button>
            </div>
          </div>
        ) : (
          <div className="p-2 space-y-2">
            <Link
              to="/login"
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-semibold text-white/70 hover:text-white bg-white/[0.05] hover:bg-white/[0.09] border border-white/[0.08] transition-all">
              <FiUser size={15} /> Đăng nhập
            </Link>
            <Link
              to="/register"
              className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl text-sm font-bold text-white bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-500 hover:brightness-110 shadow-[0_4px_16px_rgba(99,102,241,0.35)] transition-all">
              Tham gia Sonavia
            </Link>
          </div>
        )}
      </div>
    </aside>
    </>
  )
}
