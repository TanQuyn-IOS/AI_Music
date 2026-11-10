import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  FiArrowRight, FiHeart, FiPlay, FiPause,
  FiMessageCircle, FiShare2, FiZap, FiMusic,
  FiImage,
} from 'react-icons/fi'
import {
  MdGraphicEq, MdMusicNote, MdAutoAwesome,
  MdLocalFireDepartment, MdHeadphones, MdRadio, MdAlbum
} from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import usePlayerStore from '../store/playerStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SONAVIA_GRADIENTS = [
  ['#4f46e5', '#818cf8'],
  ['#0891b2', '#22d3ee'],
  ['#7c3aed', '#c084fc'],
  ['#0d9488', '#2dd4bf'],
  ['#2563eb', '#60a5fa'],
  ['#9333ea', '#e879f9'],
  ['#0284c7', '#38bdf8'],
  ['#4f46e5', '#06b6d4'],
]

function songGrad(id) {
  const [a, b] = SONAVIA_GRADIENTS[(id || 0) % SONAVIA_GRADIENTS.length]
  return `linear-gradient(135deg, ${a}, ${b})`
}

function fmtDur(s) {
  if (!s) return '0:30'
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

// ─── Prompt Box (Sonavia Studio Style) ─────────────────────────────────────────

function CreatePromptBox() {
  const navigate = useNavigate()
  const [prompt, setPrompt] = useState('')
  const [selectedChip, setSelectedChip] = useState(null)
  const [uploadingImg, setUploadingImg] = useState(false)
  const textareaRef = useRef()
  const fileInputRef = useRef()

  const PROMPT_SUGGESTIONS = [
    { label: '🖼️ Sáng tác từ ảnh', isImageMode: true },
    { label: '🌸 V-Pop Buồn', prompt: 'V-Pop ballad buồn da diết về tình yêu tan vỡ, tiếng piano chậm rãi kết hợp violin sâu lắng' },
    { label: '🌃 Synthwave 80s', prompt: 'Cyberpunk Synthwave retro 80s, bassline điện tử dồn dập, giai điệu lái xe trong đêm neon' },
    { label: '☕ Lofi Chill', prompt: 'Lofi hip hop chill beat mùa mưa, tiếng tách cà phê và guitar mộc thư giãn' },
    { label: '🔥 EDM Bùng Nổ', prompt: 'EDM festival drop năng động, synth mạnh mẽ, drop bùng cháy cổ vũ năng lượng' },
    { label: '🎷 Jazz Đêm', prompt: 'Smooth Jazz lãng mạn, saxophone êm dịu, trống brush nhẹ nhàng trong quán bar sang trọng' },
    { label: '🎬 Cinematic Epic', prompt: 'Nhạc phim hành động sử thi Cinematic, dàn nhạc giao hưởng hoành tráng, trống dồn kịch tính' },
  ]

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!prompt.trim()) return
    navigate('/create', { state: { prompt } })
  }

  const handleExample = (item) => {
    if (item.isImageMode) {
      navigate('/create', { state: { mode: 'image' } })
      return
    }
    setSelectedChip(item.label)
    setPrompt(item.prompt)
    textareaRef.current?.focus()
  }

  const handleImageUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Vui lòng chọn file hình ảnh (JPG, PNG, WebP)')
      return
    }

    setUploadingImg(true)
    const previewUrl = URL.createObjectURL(file)

    const getBase64 = (f) => new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => resolve(null)
      reader.readAsDataURL(f)
    })

    try {
      toast.loading('AI đang cảm nhận bức ảnh...', { id: 'home-img-analyze' })
      let res = null
      const fd = new FormData()
      fd.append('image', file)

      try {
        res = await api.post('/ai/analyze-image/', fd, { timeout: 60000 })
      } catch (uploadErr) {
        console.warn('FormData upload error, attempting Base64 fallback...', uploadErr)
        const base64Data = await getBase64(file)
        if (base64Data) {
          res = await api.post('/ai/analyze-image/', { image_base64: base64Data }, { timeout: 60000 })
        } else {
          throw uploadErr
        }
      }

      toast.dismiss('home-img-analyze')

      if (res && res.data && res.data.success) {
        navigate('/create', {
          state: {
            mode: 'image',
            imageAnalysis: res.data,
            imagePreview: previewUrl,
            serverCoverImageUrl: res.data.cover_image_url || '',
          }
        })
      } else {
        toast.error(res?.data?.error || 'Không thể phân tích ảnh')
      }
    } catch (err) {
      toast.dismiss('home-img-analyze')
      console.error('Home image analysis error:', err)
      toast.error('Đang chuyển đến phòng sáng tác nhạc theo ảnh...')
      navigate('/create', { state: { mode: 'image', imagePreview: previewUrl } })
    } finally {
      setUploadingImg(false)
    }
  }

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit}>
        <div
          className="relative rounded-3xl overflow-hidden transition-all duration-300 sonavia-glass border border-white/10 hover:border-indigo-500/40"
          style={{
            boxShadow: prompt.trim()
              ? '0 0 0 2px rgba(34,211,238,0.4), 0 20px 60px rgba(99,102,241,0.2)'
              : '0 12px 40px rgba(0,0,0,0.5)',
          }}>
          {/* Subtle Ambient Glow inside prompt box */}
          <div className="absolute top-0 right-0 w-48 h-20 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={e => {
              setPrompt(e.target.value)
              if (selectedChip && e.target.value !== PROMPT_SUGGESTIONS.find(s => s.label === selectedChip)?.prompt) {
                setSelectedChip(null)
              }
            }}
            placeholder="Mô tả giai điệu hoặc ý tưởng bài hát bạn muốn Sonavia tạo... (VD: V-Pop buồn nhẹ nhàng, piano và giọng nữ trầm ấm)"
            rows={3}
            className="w-full bg-transparent text-white placeholder-white/30 px-5 pt-4 pb-2 text-sm md:text-base resize-none outline-none leading-relaxed"
            onKeyDown={e => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit(e)
            }}
          />

          {/* Bottom Control Bar */}
          <div className="flex items-center justify-between px-4 pb-3 pt-1 border-t border-white/[0.05] flex-wrap gap-2">
            <div className="flex items-center gap-2.5">
              <span className="text-[11px] text-white/35 flex items-center gap-1 font-mono">
                <FiZap size={11} className="text-cyan-400" />
                {prompt.length > 0 ? `${prompt.length} ký tự` : 'Ctrl + Enter'}
              </span>

              {/* Upload image button */}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                className="hidden"
                onChange={handleImageUpload}
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingImg}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-cyan-300 hover:text-white bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 transition-all shadow-sm"
                title="Tải ảnh lên để AI sáng tác nhạc theo bức ảnh">
                {uploadingImg ? (
                  <span className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <FiImage size={13} className="text-cyan-400" />
                )}
                <span>{uploadingImg ? 'Đang phân tích...' : '🖼️ Sáng tác từ ảnh'}</span>
              </button>
            </div>

            <button
              type="submit"
              disabled={!prompt.trim()}
              className={clsx(
                'flex items-center gap-2 px-5 py-2.5 rounded-2xl font-bold text-sm transition-all duration-200 shadow-md',
                prompt.trim()
                  ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 text-white hover:brightness-110 active:scale-95 shadow-[0_0_20px_rgba(99,102,241,0.4)]'
                  : 'bg-white/5 text-white/20 cursor-not-allowed'
              )}>
              <MdGraphicEq size={18} className={prompt.trim() ? 'animate-pulse' : ''} />
              <span>Sáng tác với Sonavia</span>
            </button>
          </div>
        </div>
      </form>

      {/* Suggestion Chips */}
      <div className="flex flex-wrap gap-2 mt-3.5 justify-center">
        {PROMPT_SUGGESTIONS.map((item) => {
          const isSelected = selectedChip === item.label
          return (
            <button
              key={item.label}
              type="button"
              onClick={() => handleExample(item)}
              className={clsx(
                'text-xs px-3.5 py-1.5 rounded-full border transition-all duration-200 active:scale-95 flex items-center gap-1.5',
                isSelected
                  ? 'bg-cyan-500/20 text-cyan-200 border-cyan-400/60 shadow-[0_0_12px_rgba(34,211,238,0.25)] font-semibold'
                  : 'text-white/60 hover:text-white bg-white/[0.03] hover:bg-white/[0.08] border-white/[0.08] hover:border-cyan-400/40 shadow-sm'
              )}>
              {item.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

// ─── Song Card (Sonavia Modern Visual Card) ───────────────────────────────────

function SongCard({ song }) {
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const [liked, setLiked] = useState(song.is_liked)
  const [likesCount, setLikesCount] = useState(song.likes_count || 0)
  const isActive = currentSong?.id === song.id

  const handlePlay = (e) => {
    e.preventDefault()
    if (isActive) togglePlay()
    else playSong(song, [song])
  }

  const handleLike = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập để yêu thích')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked)
      setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <Link
      to={`/songs/${song.id}`}
      className={clsx(
        'group flex items-center gap-3.5 p-3 rounded-2xl transition-all duration-200 border',
        isActive
          ? 'bg-indigo-500/10 border-indigo-500/30 shadow-[0_0_20px_rgba(99,102,241,0.15)]'
          : 'bg-white/[0.02] hover:bg-white/[0.05] border-white/[0.05] hover:border-white/[0.1]'
      )}>

      {/* Cover Image / Gradient */}
      <div className="relative w-12 h-12 rounded-xl overflow-hidden shrink-0 shadow-md">
        {song.cover_image_url ? (
          <img
            src={song.cover_image_url}
            alt={song.title}
            className={clsx(
              'w-full h-full object-cover transition-transform duration-300',
              isActive && isPlaying ? 'scale-105' : 'group-hover:scale-105'
            )}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center text-white/70"
            style={{ background: songGrad(song.id) }}>
            <MdMusicNote size={20} />
          </div>
        )}

        {/* Play Overlay Button */}
        <button
          onClick={handlePlay}
          className={clsx(
            'absolute inset-0 flex items-center justify-center transition-all duration-200',
            isActive
              ? 'bg-black/40 backdrop-blur-[2px]'
              : 'bg-black/0 group-hover:bg-black/40'
          )}>
          {isActive && isPlaying ? (
            <div className="eq-bars scale-110">
              <div className="eq-bar" />
              <div className="eq-bar" />
              <div className="eq-bar" />
            </div>
          ) : (
            <div className={clsx(
              'w-8 h-8 rounded-full bg-white/90 text-black flex items-center justify-center shadow-lg transition-all transform',
              isActive ? 'opacity-100 scale-100' : 'opacity-0 scale-75 group-hover:opacity-100 group-hover:scale-100'
            )}>
              <FiPlay size={14} className="ml-0.5 fill-black" />
            </div>
          )}
        </button>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={clsx(
            'text-sm font-bold truncate transition-colors',
            isActive ? 'text-cyan-300' : 'text-white group-hover:text-indigo-200'
          )}>
            {song.title}
          </p>
          {song.genre && (
            <span className="hidden sm:inline-block text-[9px] px-2 py-0.5 rounded-full bg-white/[0.06] text-white/50 uppercase font-semibold">
              {song.genre}
            </span>
          )}
        </div>
        <p className="text-xs text-white/40 truncate mt-0.5 flex items-center gap-1.5">
          <span>{song.artist?.username || 'Sonavia AI'}</span>
          <span className="text-white/20">·</span>
          <span className="text-[10px] text-white/30">{fmtDur(song.duration)}</span>
        </p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={handleLike}
          className={clsx(
            'flex items-center gap-1 text-xs px-2.5 py-1 rounded-lg transition-all',
            liked
              ? 'text-rose-400 bg-rose-500/10'
              : 'text-white/30 hover:text-rose-400 hover:bg-rose-500/10 opacity-75 group-hover:opacity-100'
          )}>
          <FiHeart size={13} className={liked ? 'fill-current' : ''} />
          <span>{likesCount}</span>
        </button>
      </div>
    </Link>
  )
}

// ─── Community Post Card ──────────────────────────────────────────────────────

function PostMini({ post }) {
  const [liked, setLiked] = useState(post.is_liked)
  const [likesCount, setLikesCount] = useState(post.likes_count || 0)
  const { isAuthenticated } = useAuthStore()

  const handleLike = async () => {
    if (!isAuthenticated) return toast.error('Đăng nhập để thích')
    try {
      const { data } = await api.post(`/social/posts/${post.id}/like/`)
      setLiked(data.liked)
      setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <div className="p-3.5 rounded-2xl bg-white/[0.025] hover:bg-white/[0.045] border border-white/[0.05] transition-all duration-200">
      <div className="flex items-center gap-2.5 mb-2">
        <div className="w-7 h-7 rounded-full bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-xs font-bold text-white shadow-sm">
          {post.author?.username?.[0]?.toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-bold text-white truncate leading-none">{post.author?.username}</p>
          <p className="text-[10px] text-white/30 mt-0.5 leading-none">
            {post.created_at ? formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: vi }) : ''}
          </p>
        </div>
      </div>

      <p className="text-xs text-white/70 leading-relaxed line-clamp-2 mb-2.5">
        {post.content}
      </p>

      <div className="flex items-center gap-3 pt-2 border-t border-white/[0.04]">
        <button
          onClick={handleLike}
          className={clsx(
            'flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md transition-all',
            liked ? 'text-rose-400 bg-rose-500/10' : 'text-white/40 hover:text-rose-400'
          )}>
          <FiHeart size={11} className={liked ? 'fill-current' : ''} />
          <span>{likesCount}</span>
        </button>
        <Link
          to="/community"
          className="flex items-center gap-1 text-[11px] text-white/40 hover:text-cyan-300 transition-colors">
          <FiMessageCircle size={11} />
          <span>{post.comments_count || 0}</span>
        </Link>
      </div>
    </div>
  )
}

// ─── Skeleton Row ─────────────────────────────────────────────────────────────

function SkeletonRow() {
  return (
    <div className="flex items-center gap-3.5 p-3 animate-pulse">
      <div className="w-12 h-12 rounded-xl skeleton shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-3 skeleton rounded w-2/3" />
        <div className="h-2 skeleton rounded w-1/3" />
      </div>
    </div>
  )
}

// ─── HomePage Component ───────────────────────────────────────────────────────

export default function HomePage() {
  const { user, isAuthenticated } = useAuthStore()
  const [trending, setTrending] = useState([])
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [postsLoading, setPostsLoading] = useState(true)
  const [tab, setTab] = useState('trending') // 'trending' | 'new'

  useEffect(() => {
    Promise.all([
      api.get('/music/songs/trending/').then(r => {
        const list = r.data?.results || r.data
        setTrending(Array.isArray(list) ? list : [])
      }),
      api.get('/social/posts/?page=1').then(r => {
        const list = r.data?.results || r.data
        setPosts(Array.isArray(list) ? list.slice(0, 6) : [])
      }),
    ]).catch(() => { }).finally(() => { setLoading(false); setPostsLoading(false) })
  }, [])

  const safeTrending = Array.isArray(trending) ? trending : []
  const displaySongs = tab === 'trending'
    ? safeTrending.slice(0, 10)
    : [...safeTrending].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 10)

  return (
    <div className="animate-fade-in min-h-full pb-10">

      {/* ── Hero Banner Sonavia ── */}
      <div className="relative px-6 pt-10 pb-12 overflow-hidden">
        {/* Glowing Aurora Lights Background */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div
            className="absolute -top-10 left-1/3 w-[500px] h-[300px] rounded-full blur-[120px] opacity-40 animate-pulse"
            style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}
          />
          <div
            className="absolute top-20 right-1/4 w-[350px] h-[250px] rounded-full blur-[100px] opacity-30"
            style={{ background: 'linear-gradient(135deg, #7c3aed, #ec4899)' }}
          />
        </div>

        <div className="relative max-w-4xl mx-auto text-center">
          {/* Badge Sonavia Version */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold mb-6 bg-cyan-500/10 border border-cyan-400/30 text-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.15)] backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_8px_#22d3ee] animate-pulse" />
            <span>Sonavia AI Studio · Sáng tác & Kết nối Âm thanh</span>
          </div>

          {/* Heading */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-black text-white leading-[1.18] mb-5 tracking-tight">
            Khởi nguồn giai điệu từ Trí tuệ{' '}
            <span className="sonavia-gradient-text bg-gradient-to-r from-cyan-400 via-indigo-400 to-purple-400">
              Nhân tạo
            </span>
          </h1>

          <p className="text-white/70 text-sm sm:text-base lg:text-lg mb-8 max-w-2xl mx-auto font-normal leading-relaxed">
            {isAuthenticated
              ? `Chào mừng ${user?.first_name || user?.username}, hôm nay bạn muốn cùng Sonavia sáng tác điều gì?`
              : 'Chỉ cần một mô tả ý tưởng — Sonavia sẽ hòa âm phối khí, tạo giai điệu và mang giọng hát đến cho bạn.'}
          </p>

          {/* Prompt Studio Input */}
          <CreatePromptBox />

          {/* Action CTAs for non-authenticated */}
          {!isAuthenticated && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <Link
                to="/register"
                className="sonavia-btn-primary flex items-center gap-2 text-sm px-6 py-3">
                Bắt đầu miễn phí <FiArrowRight size={15} />
              </Link>
              <Link
                to="/explore"
                className="btn-ghost text-sm px-5 py-3">
                Khám phá kho nhạc
              </Link>
            </div>
          )}

          {/* Platform Highlights Banner */}
          <div className="grid grid-cols-3 gap-3 max-w-xl mx-auto mt-10 pt-8 border-t border-white/[0.06]">
            <div>
              <p className="text-lg sm:text-2xl font-black text-white">50K+</p>
              <p className="text-[11px] text-white/40 mt-0.5">Giai điệu đã tạo</p>
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-black text-cyan-400">Hi-Res</p>
              <p className="text-[11px] text-white/40 mt-0.5">Chất lượng Studio</p>
            </div>
            <div>
              <p className="text-lg sm:text-2xl font-black text-indigo-400">100%</p>
              <p className="text-[11px] text-white/40 mt-0.5">Quyền sáng tác tự do</p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Main Dashboard Layout ── */}
      <div className="max-w-screen-xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

          {/* ── LEFT: Songs Section (2/3) ── */}
          <div className="lg:col-span-2 space-y-6">

            {/* Header & Tabs */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 p-1 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
                {[
                  { key: 'trending', icon: MdLocalFireDepartment, label: 'Thịnh hành' },
                  { key: 'new', icon: MdMusicNote, label: 'Mới nhất' },
                ].map(({ key, icon: Icon, label }) => (
                  <button
                    key={key}
                    onClick={() => setTab(key)}
                    className={clsx(
                      'flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all duration-200',
                      tab === key
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                        : 'text-white/40 hover:text-white'
                    )}>
                    <Icon size={14} className={tab === key ? 'text-cyan-300' : ''} />
                    <span>{label}</span>
                  </button>
                ))}
              </div>

              <Link
                to="/explore"
                className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 transition-colors">
                Xem tất cả kho nhạc <FiArrowRight size={12} />
              </Link>
            </div>

            {/* Song List */}
            <div className="rounded-3xl p-3 bg-white/[0.015] border border-white/[0.05] space-y-2">
              {loading ? (
                [...Array(6)].map((_, i) => <SkeletonRow key={i} />)
              ) : displaySongs.length === 0 ? (
                <div className="text-center py-12 text-white/40">
                  <MdAlbum size={40} className="mx-auto mb-2 text-white/20" />
                  <p className="text-sm">Chưa có bài hát nào được tải lên.</p>
                  <Link to="/create" className="text-xs text-cyan-400 hover:underline mt-2 inline-block">
                    Hãy là người đầu tiên sáng tác với Sonavia →
                  </Link>
                </div>
              ) : (
                displaySongs.map(s => <SongCard key={s.id} song={s} />)
              )}
            </div>

            {/* Feature Cards Showcase */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <Link
                to="/create"
                className="p-5 rounded-3xl bg-gradient-to-br from-indigo-950/40 via-purple-950/20 to-slate-900/40 border border-indigo-500/20 hover:border-cyan-400/40 transition-all duration-300 group shadow-lg">
                <div className="w-10 h-10 rounded-2xl bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-cyan-300 mb-3 group-hover:scale-110 transition-transform">
                  <MdGraphicEq size={22} />
                </div>
                <h3 className="font-bold text-white text-base mb-1 group-hover:text-cyan-300 transition-colors">
                  Sonavia Studio
                </h3>
                <p className="text-xs text-white/50 leading-relaxed mb-3">
                  Sáng tác bài hát hoàn chỉnh với đầy đủ giọng hát chân thực và phong cách đa dạng.
                </p>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-cyan-400">
                  <span>Mở phòng Studio</span>
                  <FiArrowRight size={12} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>

              <Link
                to="/community"
                className="p-5 rounded-3xl bg-gradient-to-br from-cyan-950/40 via-blue-950/20 to-slate-900/40 border border-cyan-500/20 hover:border-indigo-400/40 transition-all duration-300 group shadow-lg">
                <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-indigo-300 mb-3 group-hover:scale-110 transition-transform">
                  <MdHeadphones size={22} />
                </div>
                <h3 className="font-bold text-white text-base mb-1 group-hover:text-indigo-300 transition-colors">
                  Cộng đồng Âm nhạc
                </h3>
                <p className="text-xs text-white/50 leading-relaxed mb-3">
                  Chia sẻ tác phẩm, giao lưu cùng cộng đồng nghệ sĩ đam mê âm nhạc trí tuệ nhân tạo.
                </p>
                <div className="flex items-center gap-1.5 text-xs font-semibold text-indigo-300">
                  <span>Khám phá cộng đồng</span>
                  <FiArrowRight size={12} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </Link>
            </div>
          </div>

          {/* ── RIGHT: Sonavia Community Feed (1/3) ── */}
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_8px_#22d3ee]" />
                Nhịp đập Sonavia
              </h2>
              <Link
                to="/community"
                className="text-xs font-semibold text-white/40 hover:text-cyan-300 transition-colors">
                Xem thêm
              </Link>
            </div>

            {/* Feed items */}
            <div className="space-y-3">
              {postsLoading ? (
                [...Array(3)].map((_, i) => (
                  <div key={i} className="p-4 rounded-2xl skeleton h-28" />
                ))
              ) : posts.length === 0 ? (
                <div className="text-center py-10 rounded-3xl bg-white/[0.02] border border-white/[0.04]">
                  <p className="text-3xl mb-2">🎶</p>
                  <p className="text-xs text-white/40">Chưa có bài viết mới</p>
                  <Link to="/community" className="text-xs text-cyan-400 hover:underline mt-2 inline-block">
                    Đăng bài viết đầu tiên →
                  </Link>
                </div>
              ) : (
                posts.map(p => <PostMini key={p.id} post={p} />)
              )}
            </div>

            {/* Platform Banner Card */}
            <div className="p-5 rounded-3xl bg-gradient-to-br from-indigo-900/30 via-slate-900/40 to-cyan-900/30 border border-white/[0.08] relative overflow-hidden">
              <div className="relative z-10">
                <div className="flex items-center gap-2 mb-2">
                  <span className="p-1 rounded-lg bg-indigo-500/20 text-cyan-300">
                    <MdAutoAwesome size={16} />
                  </span>
                  <h4 className="text-sm font-bold text-white">Âm nhạc không giới hạn</h4>
                </div>
                <p className="text-xs text-white/60 leading-relaxed mb-4">
                  Sonavia cung cấp công nghệ chuyển hóa ngôn ngữ thành tác phẩm âm nhạc đa kênh với tốc độ cao.
                </p>
                <Link
                  to="/create"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold text-white bg-white/10 hover:bg-white/20 border border-white/10 transition-all">
                  <span>Trải nghiệm Sonavia Studio</span>
                  <FiArrowRight size={11} />
                </Link>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
