import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiEye, FiEyeOff, FiArrowRight, FiCheck } from 'react-icons/fi'
import { MdGraphicEq, MdAutoAwesome } from 'react-icons/md'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const [form, setForm] = useState({ username: '', password: '' })
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const { login } = useAuthStore()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    const username = form.username.trim()
    const password = form.password

    if (!username || !password) {
      toast.error('Vui lòng nhập đầy đủ tên đăng nhập (hoặc email) và mật khẩu.')
      return
    }

    setLoading(true)
    try {
      await login(username, password)
      toast.success('Chào mừng bạn trở lại với Sonavia! 🎵')
      navigate('/')
    } catch (err) {
      if (!err.response) {
        toast.error('Không thể kết nối đến máy chủ backend (Port 8000). Vui lòng đảm bảo server đang chạy!')
        return
      }
      if (err.response.status >= 500) {
        toast.error(`Máy chủ gặp sự cố (HTTP ${err.response.status}). Vui lòng thử lại sau!`)
        return
      }
      const data = err.response?.data
      const msg = data?.non_field_errors?.[0]
        || (typeof data === 'string' ? data : null)
        || (data && typeof data === 'object' ? Object.values(data).flat()[0] : null)
        || 'Sai tên đăng nhập hoặc mật khẩu'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-[#060713]">
      {/* Left: Form Area */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Subtle Ambient Background Light */}
        <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-indigo-600/10 rounded-full blur-[100px] pointer-events-none" />

        <div className="w-full max-w-sm relative z-10 animate-slide-up">
          {/* Sonavia Logo */}
          <Link to="/" className="flex items-center gap-3.5 mb-8 group">
            <div className="relative shrink-0">
              <div
                className="absolute -inset-1 rounded-2xl blur-md opacity-70 group-hover:opacity-100 transition-opacity"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}
              />
              <div
                className="relative w-11 h-11 rounded-2xl flex items-center justify-center border border-white/20 shadow-lg"
                style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #0891b2 100%)' }}>
                <svg className="w-6 h-6 text-cyan-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
                  <path d="M4 10v4" />
                  <path d="M8 6v12" />
                  <path d="M12 2v20" />
                  <path d="M16 8v8" />
                  <path d="M20 11v2" />
                </svg>
              </div>
            </div>
            <div>
              <p className="font-extrabold text-xl text-white tracking-tight leading-none">
                Sonavia
              </p>
              <p className="text-[11px] text-white/40 mt-1 font-medium leading-none">
                AI Music & Sound Lab
              </p>
            </div>
          </Link>

          <h1 className="text-2xl sm:text-3xl font-black text-white mb-2 tracking-tight">
            Đăng nhập
          </h1>
          <p className="text-white/45 text-sm mb-7">
            Chào mừng bạn trở lại với không gian âm nhạc Sonavia 👋
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                Tên đăng nhập hoặc Email
              </label>
              <input
                type="text"
                className="input-field"
                placeholder="Nhập username hoặc email của bạn"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                Mật khẩu
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  className="input-field pr-11"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPass(!showPass)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-white/35 hover:text-white transition-colors">
                  {showPass ? <FiEyeOff size={16} /> : <FiEye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="sonavia-btn-primary w-full py-3.5 flex items-center justify-center gap-2 mt-6 text-sm">
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang đăng nhập...</span>
                </>
              ) : (
                <>
                  <span>Đăng nhập Sonavia</span>
                  <FiArrowRight size={15} />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-white/40 text-sm mt-6">
            Chưa có tài khoản Sonavia?{' '}
            <Link
              to="/register"
              className="font-bold text-cyan-300 hover:text-cyan-200 transition-colors">
              Đăng ký ngay
            </Link>
          </p>
        </div>
      </div>

      {/* Right: Sonavia Studio Showcase Banner */}
      <div
        className="hidden lg:flex flex-1 items-center justify-center relative overflow-hidden border-l border-white/[0.06]"
        style={{
          background: 'linear-gradient(135deg, rgba(79,70,229,0.12) 0%, rgba(6,182,212,0.08) 100%)',
        }}>
        <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-indigo-600/20 rounded-full blur-[100px]" />
        <div className="absolute bottom-1/3 right-1/4 w-72 h-72 bg-cyan-600/15 rounded-full blur-[90px]" />

        <div className="relative text-center px-12 max-w-md z-10">
          <div className="w-16 h-16 rounded-3xl mx-auto mb-6 flex items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-cyan-400 shadow-[0_0_30px_rgba(99,102,241,0.5)] border border-white/20">
            <MdGraphicEq size={32} className="text-white" />
          </div>

          <h2 className="text-3xl font-black text-white mb-3">
            Sonavia AI Studio
          </h2>
          <p className="text-white/60 text-sm leading-relaxed mb-6 font-normal">
            Nền tảng sáng tác nhạc trí tuệ nhân tạo đột phá. Biến ý tưởng của bạn thành âm thanh chân thực chỉ trong vài khoảnh khắc.
          </p>

          <div className="space-y-2.5 text-left bg-white/[0.03] p-4 rounded-2xl border border-white/[0.06] backdrop-blur-md">
            {[
              'Sáng tác bài hát đầy đủ ca từ và giọng hát',
              'Chất lượng âm thanh phòng thu Hi-Fi',
              'Mạng xã hội chia sẻ và giao lưu cùng nghệ sĩ',
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2.5 text-xs text-white/70">
                <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-300 flex items-center justify-center shrink-0">
                  <FiCheck size={10} />
                </span>
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
