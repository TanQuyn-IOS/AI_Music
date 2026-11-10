import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  FiUser, FiLock, FiCamera, FiSave,
  FiLogOut, FiTrash2, FiCheck, FiAlertTriangle
} from 'react-icons/fi'
import { MdMusicNote } from 'react-icons/md'
import useAuthStore from '../store/authStore'
import api from '../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const TABS = [
  { key: 'profile', label: 'Hồ sơ', icon: FiUser },
  { key: 'password', label: 'Mật khẩu', icon: FiLock },
  { key: 'music', label: 'Sở thích nhạc', icon: MdMusicNote },
]

const GENRES = [
  { key: 'vpop', label: 'V-Pop', emoji: '🇻🇳' },
  { key: 'kpop', label: 'K-Pop', emoji: '🇰🇷' },
  { key: 'pop', label: 'Pop', emoji: '🎤' },
  { key: 'rock', label: 'Rock', emoji: '🎸' },
  { key: 'jazz', label: 'Jazz', emoji: '🎷' },
  { key: 'classical', label: 'Classical', emoji: '🎻' },
  { key: 'hip_hop', label: 'Hip Hop', emoji: '🎧' },
  { key: 'r&b', label: 'R&B', emoji: '🎵' },
  { key: 'electronic', label: 'Electronic', emoji: '🎹' },
  { key: 'indie', label: 'Indie', emoji: '🌿' },
  { key: 'folk', label: 'Folk', emoji: '🪕' },
  { key: 'blues', label: 'Blues', emoji: '🎼' },
]

export default function SettingsPage() {
  const { user, updateProfile, logout } = useAuthStore()
  const navigate = useNavigate()
  const [tab, setTab] = useState('profile')

  // Profile form
  const [profile, setProfile] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    bio: user?.bio || '',
    is_artist: user?.is_artist || false,
  })
  const [avatar, setAvatar] = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar_url || null)
  const [cover, setCover] = useState(null)
  const [savingProfile, setSavingProfile] = useState(false)

  // Password form
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' })
  const [savingPwd, setSavingPwd] = useState(false)

  // Music preferences
  const [favoriteGenres, setFavoriteGenres] = useState(user?.favorite_genres || [])
  const [savingMusic, setSavingMusic] = useState(false)

  const handleAvatarChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAvatar(file)
    setAvatarPreview(URL.createObjectURL(file))
  }

  const handleCoverChange = (e) => {
    const file = e.target.files[0]
    if (file) setCover(file)
  }

  const handleSaveProfile = async (e) => {
    e.preventDefault()
    setSavingProfile(true)
    try {
      const fd = new FormData()
      Object.entries(profile).forEach(([k, v]) => fd.append(k, v))
      if (avatar) fd.append('avatar', avatar)
      if (cover) fd.append('cover_image', cover)
      await updateProfile(fd)
      toast.success('✅ Đã cập nhật hồ sơ!')
    } catch {
      toast.error('Lỗi khi cập nhật hồ sơ')
    }
    setSavingProfile(false)
  }

  const handleSavePassword = async (e) => {
    e.preventDefault()
    if (passwords.new !== passwords.confirm) return toast.error('Mật khẩu mới không khớp')
    if (passwords.new.length < 6) return toast.error('Mật khẩu phải ít nhất 6 ký tự')
    setSavingPwd(true)
    try {
      await api.post('/auth/change-password/', {
        old_password: passwords.current,
        new_password: passwords.new,
      })
      toast.success('✅ Đã đổi mật khẩu!')
      setPasswords({ current: '', new: '', confirm: '' })
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.old_password?.[0] || 'Lỗi khi đổi mật khẩu'
      toast.error(msg)
    }
    setSavingPwd(false)
  }

  const handleSaveMusic = async () => {
    setSavingMusic(true)
    try {
      // Bug fix #13: send as JSON body, not FormData string
      await api.patch('/auth/profile/', { favorite_genres: favoriteGenres })
      toast.success('✅ Đã lưu sở thích âm nhạc!')
    } catch {
      toast.error('Lỗi khi lưu')
    }
    setSavingMusic(false)
  }

  const toggleGenre = (genre) => {
    setFavoriteGenres(prev =>
      prev.includes(genre)
        ? prev.filter(g => g !== genre)
        : [...prev, genre]
    )
  }

  const handleLogout = async () => {
    await logout()
    toast.success('Đã đăng xuất')
    navigate('/login')
  }

  return (
    <div className="p-6 max-w-3xl mx-auto animate-fade-in">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-black text-white">Cài đặt</h1>
        <p className="text-white/35 text-sm mt-1">Quản lý tài khoản và sở thích của bạn</p>
      </div>

      <div className="flex gap-6 flex-col sm:flex-row">
        {/* Sidebar tabs */}
        <div className="sm:w-44 shrink-0">
          <nav className="space-y-0.5">
            {TABS.map(t => (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={clsx(
                  'w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium transition-all text-left',
                  tab === t.key
                    ? 'bg-indigo-600/20 border border-indigo-500/30 text-indigo-300'
                    : 'text-white/45 hover:text-white hover:bg-white/[0.04]'
                )}>
                <t.icon size={14} className={tab === t.key ? 'text-indigo-400' : ''} />
                {t.label}
              </button>
            ))}

            <div className="pt-3 border-t border-white/[0.06] mt-3 space-y-0.5">
              <button onClick={handleLogout}
                className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl text-sm font-medium text-white/30 hover:text-red-400 hover:bg-red-500/10 transition-all">
                <FiLogOut size={14} /> Đăng xuất
              </button>
            </div>
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* ── Profile tab ── */}
          {tab === 'profile' && (
            <form onSubmit={handleSaveProfile} className="space-y-5 animate-fade-in">
              {/* Cover image */}
              <div className="glass-card overflow-hidden">
                <div className="relative h-32">
                  {cover
                    ? <img src={URL.createObjectURL(cover)} className="w-full h-full object-cover" alt="cover" />
                    : user?.cover_image_url
                      ? <img src={user.cover_image_url} className="w-full h-full object-cover" alt="cover" />
                      : <div className="w-full h-full bg-gradient-to-br from-indigo-900/40 to-violet-900/30" />
                  }
                  <label className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 hover:opacity-100 transition-opacity cursor-pointer group">
                    <div className="flex flex-col items-center gap-1.5 text-white">
                      <FiCamera size={20} />
                      <span className="text-xs font-medium">Đổi ảnh bìa</span>
                    </div>
                    <input type="file" accept="image/*" onChange={handleCoverChange} className="hidden" />
                  </label>
                </div>

                {/* Avatar */}
                <div className="px-5 pb-5">
                  <div className="flex items-end gap-4 -mt-10 mb-4">
                    <label className="cursor-pointer relative group shrink-0">
                      <div className="w-20 h-20 rounded-2xl overflow-hidden ring-4 ring-[#070711]">
                        {avatarPreview
                          ? <img src={avatarPreview} className="w-full h-full object-cover" alt="avatar" />
                          : <div className="w-full h-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-2xl font-black text-white">
                            {user?.username?.[0]?.toUpperCase() || '?'}
                          </div>
                        }
                      </div>
                      <div className="absolute inset-0 bg-black/50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                        <FiCamera size={16} className="text-white" />
                      </div>
                      <input type="file" accept="image/*" onChange={handleAvatarChange} className="hidden" />
                    </label>
                    <div className="pb-1">
                      <p className="text-sm font-bold text-white">@{user?.username}</p>
                      <p className="text-xs text-white/30 mt-0.5">Nhấn ảnh để thay đổi</p>
                    </div>
                  </div>

                  {/* Name fields */}
                  <div className="grid grid-cols-2 gap-3 mb-3">
                    <div>
                      <label className="text-xs text-white/40 mb-1 block">Họ</label>
                      <input className="input-field text-sm" placeholder="Họ"
                        value={profile.last_name} onChange={e => setProfile({ ...profile, last_name: e.target.value })} />
                    </div>
                    <div>
                      <label className="text-xs text-white/40 mb-1 block">Tên</label>
                      <input className="input-field text-sm" placeholder="Tên"
                        value={profile.first_name} onChange={e => setProfile({ ...profile, first_name: e.target.value })} />
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-white/40 mb-1 block">Giới thiệu</label>
                    <textarea className="input-field text-sm resize-none" rows={3}
                      placeholder="Viết gì đó về bản thân..."
                      value={profile.bio} onChange={e => setProfile({ ...profile, bio: e.target.value })} />
                  </div>
                </div>
              </div>

              <button type="submit" disabled={savingProfile} className="btn-primary w-full py-3 flex items-center justify-center gap-2">
                {savingProfile
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang lưu...</>
                  : <><FiSave size={14} />Lưu thay đổi</>
                }
              </button>
            </form>
          )}

          {/* ── Password tab ── */}
          {tab === 'password' && (
            <form onSubmit={handleSavePassword} className="space-y-4 animate-fade-in">
              <div className="glass-card p-5 space-y-4">
                <h3 className="font-bold text-white text-sm flex items-center gap-2">
                  <FiLock className="text-indigo-400" /> Đổi mật khẩu
                </h3>
                {[
                  { key: 'current', label: 'Mật khẩu hiện tại', placeholder: '••••••••' },
                  { key: 'new', label: 'Mật khẩu mới', placeholder: 'Ít nhất 6 ký tự' },
                  { key: 'confirm', label: 'Xác nhận mật khẩu mới', placeholder: 'Nhập lại mật khẩu mới' },
                ].map(f => (
                  <div key={f.key}>
                    <label className="text-xs text-white/40 mb-1 block">{f.label}</label>
                    <input type="password" className="input-field text-sm" placeholder={f.placeholder}
                      value={passwords[f.key]} onChange={e => setPasswords({ ...passwords, [f.key]: e.target.value })} />
                  </div>
                ))}
              </div>

              {/* Strength indicator */}
              {passwords.new && (
                <div className="glass-card p-3">
                  <p className="text-xs text-white/40 mb-2">Độ mạnh mật khẩu</p>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4].map(i => {
                      const strength = Math.min(Math.floor(passwords.new.length / 3), 4)
                      return (
                        <div key={i} className={clsx('h-1.5 flex-1 rounded-full transition-all',
                          i <= strength
                            ? strength <= 1 ? 'bg-red-500' : strength <= 2 ? 'bg-amber-500' : strength <= 3 ? 'bg-blue-500' : 'bg-emerald-500'
                            : 'bg-white/10'
                        )} />
                      )
                    })}
                  </div>
                </div>
              )}

              <button type="submit" disabled={savingPwd || !passwords.current || !passwords.new}
                className="btn-primary w-full py-3 flex items-center justify-center gap-2">
                {savingPwd
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang đổi...</>
                  : <><FiLock size={14} />Đổi mật khẩu</>
                }
              </button>
            </form>
          )}

          {/* ── Music preferences tab ── */}
          {tab === 'music' && (
            <div className="space-y-5 animate-fade-in">
              <div className="glass-card p-5">
                <h3 className="font-bold text-white text-sm mb-1 flex items-center gap-2">
                  <MdMusicNote className="text-indigo-400" /> Thể loại yêu thích
                </h3>
                <p className="text-xs text-white/35 mb-4">Chọn để AI hiểu sở thích và đề xuất nhạc tốt hơn</p>
                <div className="grid grid-cols-3 gap-2">
                  {GENRES.map(g => (
                    <button key={g.key} onClick={() => toggleGenre(g.key)}
                      className={clsx(
                        'flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-medium transition-all',
                        favoriteGenres.includes(g.key)
                          ? 'bg-indigo-600/20 border-indigo-500/40 text-indigo-300'
                          : 'border-white/[0.07] text-white/45 hover:border-white/15 hover:text-white'
                      )}>
                      <span>{g.emoji}</span>
                      <span className="truncate">{g.label}</span>
                      {favoriteGenres.includes(g.key) && (
                        <FiCheck size={12} className="ml-auto shrink-0 text-indigo-400" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Selected count */}
              {favoriteGenres.length > 0 && (
                <div className="glass-card p-4 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center font-black text-sm"
                    style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
                    {favoriteGenres.length}
                  </div>
                  <div>
                    <p className="text-sm text-white font-semibold">Thể loại đã chọn</p>
                    <p className="text-xs text-white/35">{favoriteGenres.join(', ')}</p>
                  </div>
                </div>
              )}

              <button onClick={handleSaveMusic} disabled={savingMusic}
                className="btn-primary w-full py-3 flex items-center justify-center gap-2">
                {savingMusic
                  ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang lưu...</>
                  : <><FiSave size={14} />Lưu sở thích</>
                }
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
