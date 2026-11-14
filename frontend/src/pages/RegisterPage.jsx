import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiArrowRight } from 'react-icons/fi'
import { MdGraphicEq, MdAutoAwesome } from 'react-icons/md'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'

export default function RegisterPage() {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    is_artist: false,
  })
  const [loading, setLoading] = useState(false)
  const { register } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    const payload = {
      ...form,
      username: form.username.trim(),
      email: form.email.trim(),
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
    }

    if (!payload.username || !payload.email || !payload.password || !payload.password2) {
      toast.error('Vui lòng điền đầy đủ thông tin bắt buộc.')
      return
    }

    if (payload.password.length < 6) {
      toast.error('Mật khẩu phải có ít nhất 6 ký tự.')
      return
    }

    if (payload.password !== payload.password2) {
      toast.error('Mật khẩu xác nhận không khớp!')
      return
    }

    setLoading(true)
    try {
      await register(payload)
      toast.success('Chào mừng bạn gia nhập Sonavia! 🎉')
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
      const errors = err.response?.data
      const msg = errors ? Object.values(errors).flat()[0] : 'Đăng ký tài khoản thất bại'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const f = (k) => ({
    value: form[k],
    onChange: e => setForm({ ...form, [k]: e.target.value }),
  })

  return (
    <div className="min-h-screen flex items-center justify-center p-6 bg-[#060713] relative overflow-hidden">
      {/* Aurora Ambient Background Light */}
      <div className="absolute -top-24 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-r from-indigo-600/15 via-purple-600/15 to-cyan-500/15 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-lg relative z-10 animate-slide-up my-8">
        {/* Header with Sonavia Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-3.5 mb-5 group">
            <div className="relative shrink-0">
              <div
                className="absolute -inset-1 rounded-2xl blur-md opacity-70 group-hover:opacity-100 transition-opacity"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}
              />
              <div
                className="relative w-12 h-12 rounded-2xl flex items-center justify-center border border-white/20 shadow-lg"
                style={{ background: 'linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #0891b2 100%)' }}>
                <svg className="w-7 h-7 text-cyan-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
                  <path d="M4 10v4" />
                  <path d="M8 6v12" />
                  <path d="M12 2v20" />
                  <path d="M16 8v8" />
                  <path d="M20 11v2" />
                </svg>
              </div>
            </div>
            <div className="text-left">
              <p className="font-black text-2xl text-white tracking-tight leading-none">
                Sonavia
              </p>
              <p className="text-[11px] text-white/40 mt-1 font-medium leading-none">
                AI Music & Sound Lab
              </p>
            </div>
          </Link>

          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
            Tạo tài khoản Sonavia
          </h1>
          <p className="text-white/45 text-sm mt-1.5">
            Tham gia cộng đồng sáng tác và thưởng thức âm nhạc AI
          </p>
        </div>

        {/* Card Form */}
        <div className="sonavia-glass p-7 sm:p-8 rounded-3xl border border-white/10 shadow-2xl">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="text-xs font-semibold text-white/60 mb-1.5 block">Họ</label>
                <input className="input-field text-sm" placeholder="Nguyễn" {...f('last_name')} />
              </div>
              <div>
                <label className="text-xs font-semibold text-white/60 mb-1.5 block">Tên</label>
                <input className="input-field text-sm" placeholder="Văn A" {...f('first_name')} />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                Tên đăng nhập (Username) *
              </label>
              <input
                className="input-field text-sm"
                placeholder="sonavia_user"
                {...f('username')}
                required
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                Email *
              </label>
              <input
                type="email"
                className="input-field text-sm"
                placeholder="user@example.com"
                {...f('email')}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-3.5">
              <div>
                <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                  Mật khẩu *
                </label>
                <input
                  type="password"
                  className="input-field text-sm"
                  placeholder="≥ 6 ký tự"
                  {...f('password')}
                  required
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-white/60 mb-1.5 block">
                  Xác nhận lại *
                </label>
                <input
                  type="password"
                  className="input-field text-sm"
                  placeholder="Nhập lại mật khẩu"
                  {...f('password2')}
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="sonavia-btn-primary w-full py-3.5 flex items-center justify-center gap-2 mt-4 text-sm font-bold">
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang khởi tạo tài khoản...</span>
                </>
              ) : (
                <>
                  <span>Đăng ký ngay</span>
                  <FiArrowRight size={15} />
                </>
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-white/40 text-sm mt-6">
          Đã có tài khoản Sonavia?{' '}
          <Link
            to="/login"
            className="font-bold text-cyan-300 hover:text-cyan-200 transition-colors">
            Đăng nhập ngay
          </Link>
        </p>
      </div>
    </div>
  )
}
