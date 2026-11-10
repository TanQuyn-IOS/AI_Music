import { useState } from 'react'
import { FiX, FiCamera } from 'react-icons/fi'
import useAuthStore from '../../store/authStore'
import toast from 'react-hot-toast'

export default function EditProfileModal({ onClose, onUpdated }) {
  const { user, updateProfile } = useAuthStore()
  const [form, setForm] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    bio: user?.bio || '',
    is_artist: user?.is_artist || false,
  })
  const [avatar, setAvatar] = useState(null)
  const [avatarPreview, setAvatarPreview] = useState(user?.avatar_url || null)
  const [loading, setLoading] = useState(false)

  const handleAvatar = (e) => {
    const file = e.target.files[0]
    if (!file) return
    setAvatar(file)
    setAvatarPreview(URL.createObjectURL(file))
  }

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true)
    try {
      const fd = new FormData()
      Object.entries(form).forEach(([k, v]) => fd.append(k, v))
      if (avatar) fd.append('avatar', avatar)
      const updated = await updateProfile(fd)
      toast.success('Đã cập nhật hồ sơ!')
      if (onUpdated) onUpdated(updated)
      onClose()
    } catch { toast.error('Lỗi khi cập nhật') }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
      <div className="glass-card p-6 w-full max-w-md animate-slide-up border border-white/10">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-black text-white">Chỉnh sửa hồ sơ</h2>
          <button onClick={onClose} className="btn-icon w-8 h-8 text-white/40">
            <FiX size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Avatar */}
          <div className="flex items-center gap-4 p-4 bg-white/[0.03] rounded-2xl border border-white/[0.06]">
            <label className="cursor-pointer relative group shrink-0">
              <div className="w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-white/10">
                {avatarPreview
                  ? <img src={avatarPreview} className="w-full h-full object-cover" alt="avatar" />
                  : <div className="w-full h-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-2xl font-black text-white">
                    {user?.username?.[0]?.toUpperCase()}
                  </div>
                }
              </div>
              <div className="absolute inset-0 bg-black/50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <FiCamera size={18} className="text-white" />
              </div>
              <input type="file" accept="image/*" onChange={handleAvatar} className="hidden" />
            </label>
            <div>
              <p className="text-sm font-bold text-white">@{user?.username}</p>
              <p className="text-xs text-white/30 mt-0.5">Nhấn vào ảnh để thay đổi</p>
            </div>
          </div>

          {/* Name */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/35 mb-1 block">Họ</label>
              <input className="input-field text-sm" placeholder="Họ"
                value={form.last_name} onChange={e => setForm({ ...form, last_name: e.target.value })} />
            </div>
            <div>
              <label className="text-xs text-white/35 mb-1 block">Tên</label>
              <input className="input-field text-sm" placeholder="Tên"
                value={form.first_name} onChange={e => setForm({ ...form, first_name: e.target.value })} />
            </div>
          </div>

          {/* Bio */}
          <div>
            <label className="text-xs text-white/35 mb-1 block">Giới thiệu</label>
            <textarea className="input-field text-sm resize-none" rows={3}
              placeholder="Viết gì đó về bản thân..."
              value={form.bio} onChange={e => setForm({ ...form, bio: e.target.value })} />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-ghost flex-1 border border-white/10">Hủy</button>
            <button type="submit" disabled={loading} className="btn-primary flex-1">
              {loading ? 'Đang lưu...' : 'Lưu thay đổi'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
