import { Link } from 'react-router-dom'
import { FiHome, FiCompass } from 'react-icons/fi'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center p-6"
      style={{ background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(139,92,246,0.15), transparent)' }}>
      <div className="text-center animate-fade-in">
        <div className="text-8xl font-black gradient-text mb-2">404</div>
        <div className="text-6xl mb-6 animate-float">🎵</div>
        <h1 className="text-2xl font-black text-white mb-2">Trang không tồn tại</h1>
        <p className="text-white/40 text-sm mb-8 max-w-xs mx-auto">
          Giai điệu này có vẻ chưa được viết... Hãy quay về trang chủ!
        </p>
        <div className="flex gap-3 justify-center">
          <Link to="/" className="btn-primary flex items-center gap-2">
            <FiHome size={16} /> Trang chủ
          </Link>
          <Link to="/explore" className="btn-ghost border border-white/10 flex items-center gap-2">
            <FiCompass size={16} /> Khám phá
          </Link>
        </div>
      </div>
    </div>
  )
}
