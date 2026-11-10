import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FiPlay, FiPause, FiHeart, FiShare2, FiClock, FiMessageCircle, FiTrendingUp } from 'react-icons/fi'
import { MdMusicNote, MdAutoAwesome } from 'react-icons/md'
import api from '../api/axios'
import usePlayerStore from '../store/playerStore'
import useAuthStore from '../store/authStore'
import SongCard from '../components/music/SongCard'
import ShareModal from '../components/common/ShareModal'
import ExtendModal from '../components/common/ExtendModal'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600', 'from-cyan-600 to-blue-600',
]

function fmtDur(s) {
  if (!s) return '0:00'
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

function StatPill({ icon: Icon, value, label, color }) {
  return (
    <div className="flex flex-col items-center gap-1 px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06]">
      <Icon size={14} className={color || 'text-white/40'} />
      <p className="text-base font-bold text-white">{value}</p>
      <p className="text-[10px] text-white/30">{label}</p>
    </div>
  )
}

export default function SongDetailPage() {
  const { id } = useParams()
  const [song, setSong] = useState(null)
  const [comments, setComments] = useState([])
  const [similar, setSimilar] = useState([])
  const [newComment, setNewComment] = useState('')
  const [liked, setLiked] = useState(false)
  const [likesCount, setLikesCount] = useState(0)
  const [lyricsExpanded, setLyricsExpanded] = useState(false)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [showShare, setShowShare] = useState(false)
  const [showExtend, setShowExtend] = useState(false)
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated, user: currentUser } = useAuthStore()

  useEffect(() => {
    window.scrollTo(0, 0)
    setLoading(true)
    setNotFound(false)
    const loadAll = async () => {
      try {
        const [songRes, commentsRes] = await Promise.all([
          api.get(`/music/songs/${id}/`),
          api.get(`/social/songs/${id}/comments/`),
        ])
        setSong(songRes.data)
        setLiked(songRes.data.is_liked)
        setLikesCount(songRes.data.likes_count ?? 0)
        const rawComments = commentsRes.data?.results || commentsRes.data
        setComments(Array.isArray(rawComments) ? rawComments : [])
      } catch (err) {
        if (err.response?.status === 404) {
          setNotFound(true)
        } else if (!err.response) {
          toast.error('Không thể kết nối đến máy chủ backend (Port 8000)')
        } else {
          toast.error('Không thể tải bài hát')
        }
      } finally {
        setLoading(false)
      }
      try {
        const simRes = await api.get(`/ai/recommend/song/${id}/`)
        const simList = simRes.data?.recommendations
        setSimilar(Array.isArray(simList) ? simList : [])
      } catch { }
    }
    loadAll()
  }, [id])

  if (loading) return (
    <div className="animate-pulse p-6 space-y-4 max-w-screen-xl mx-auto">
      <div className="h-72 rounded-3xl skeleton" />
      <div className="grid grid-cols-3 gap-4">
        <div className="h-20 skeleton rounded-2xl" />
        <div className="h-20 skeleton rounded-2xl" />
        <div className="h-20 skeleton rounded-2xl" />
      </div>
    </div>
  )

  if (notFound || !song) return (
    <div className="p-12 text-center max-w-md mx-auto my-12 glass-card rounded-3xl animate-fade-in">
      <div className="w-16 h-16 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-3xl mb-4">
        🎵
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Không tìm thấy bài hát</h2>
      <p className="text-white/40 text-sm mb-6">
        Bài hát này không tồn tại hoặc đã được gỡ bỏ khỏi Sonavia.
      </p>
      <Link to="/" className="btn-primary inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold">
        Khám phá bài hát khác
      </Link>
    </div>
  )

  const isActive = currentSong?.id === song.id
  const grad = COVER_GRADIENTS[song.id % COVER_GRADIENTS.length]

  const handlePlay = () => {
    if (isActive) togglePlay()
    else playSong(song, similar.length ? [song, ...similar] : [song])
  }

  const handleLike = async () => {
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
      toast.success(data.liked ? '❤️ Đã thích' : 'Đã bỏ thích')
    } catch { toast.error('Lỗi') }
  }

  const handleComment = async (e) => {
    e.preventDefault(); if (!newComment.trim()) return
    try {
      const { data } = await api.post(`/social/songs/${id}/comments/`, { content: newComment })
      setComments(p => [data, ...p]); setNewComment('')
    } catch { toast.error('Lỗi khi bình luận') }
  }

  return (
    <div className="animate-fade-in max-w-screen-xl mx-auto">
      {/* ── Share & Extend Modals ── */}
      {showShare && (
        <ShareModal
          isOpen={showShare}
          onClose={() => setShowShare(false)}
          song={song}
        />
      )}
      {showExtend && (
        <ExtendModal
          isOpen={showExtend}
          onClose={() => setShowExtend(false)}
          song={song}
          onExtended={(newSong) => {
            setSong(newSong)
          }}
        />
      )}

      {/* ── Hero banner ── */}
      <div className="relative overflow-hidden">
        {/* Blurred cover background */}
        <div className="absolute inset-0 z-0">
          {song.cover_image_url
            ? <img src={song.cover_image_url} className="w-full h-full object-cover scale-110 blur-xl opacity-20" alt="" />
            : <div className={`w-full h-full bg-gradient-to-br ${grad} opacity-20`} />
          }
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#070711]/70 to-[#070711]" />
        </div>

        <div className="relative z-10 px-6 pt-8 pb-6 flex gap-8 flex-wrap">
          {/* Cover art */}
          <div className="relative shrink-0">
            <div className={`absolute inset-0 bg-gradient-to-br ${grad} rounded-3xl blur-xl opacity-60 scale-95`} />
            <div className="relative w-52 h-52 rounded-3xl overflow-hidden shadow-2xl">
              {song.cover_image_url
                ? <img src={song.cover_image_url} alt={song.title} className="w-full h-full object-cover" />
                : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center`}>
                  <MdMusicNote size={64} className="text-white/60" />
                </div>
              }
              {isActive && isPlaying && (
                <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                  <div className="eq-bars scale-150"><div className="eq-bar" /><div className="eq-bar" /><div className="eq-bar" /></div>
                </div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0 flex flex-col justify-end pb-2">
            <div className="flex items-center gap-2 mb-3">
              {song.genre && <span className="badge badge-purple">{song.genre.toUpperCase()}</span>}
              {song.mood && <span className="badge badge-pink">{song.mood}</span>}
              {song.is_published && <span className="badge badge-green">Public</span>}
            </div>

            <h1 className="text-4xl font-black text-white mb-2 leading-tight">{song.title}</h1>
            <Link to={`/profile/${song.artist?.username}`}
              className="text-lg text-white/60 hover:text-indigo-300 transition-colors font-medium mb-4 inline-block">
              {song.artist?.first_name && song.artist?.last_name
                ? `${song.artist.first_name} ${song.artist.last_name}` : song.artist?.username}
            </Link>

            {song.description && (
              <p className="text-sm text-white/40 mb-5 max-w-lg leading-relaxed">{song.description}</p>
            )}

            {/* Action buttons */}
            <div className="flex items-center gap-3 flex-wrap">
              <button onClick={handlePlay}
                className="flex items-center gap-2.5 px-6 py-3 bg-white text-black font-bold rounded-full hover:scale-105 active:scale-95 transition-all shadow-lg text-sm">
                {isActive && isPlaying ? <><FiPause size={18} /> Dừng</> : <><FiPlay size={18} className="ml-0.5" /> Phát</>}
              </button>
              <button onClick={handleLike}
                className={clsx('flex items-center gap-2 px-5 py-3 rounded-full border font-semibold text-sm transition-all',
                  liked ? 'bg-pink-500/20 border-pink-500/50 text-pink-400' : 'bg-white/5 border-white/15 text-white/60 hover:border-white/30 hover:text-white')}>
                <FiHeart size={16} className={liked ? 'fill-current' : ''} />
                {likesCount.toLocaleString()}
              </button>
              <button
                onClick={() => setShowShare(true)}
                title="Chia sẻ bài hát"
                className="btn-icon w-11 h-11 rounded-full text-white/70 hover:text-white">
                <FiShare2 size={16} />
              </button>

              {/* Nút Mở rộng bài hát (AI Extend Track / Inpainting) */}
              {isAuthenticated && (
                <button
                  onClick={() => setShowExtend(true)}
                  className="flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-cyan-500/20 via-indigo-500/20 to-purple-500/20 hover:from-cyan-500/30 hover:to-indigo-500/30 border border-cyan-400/40 text-cyan-300 font-bold text-sm shadow-[0_0_15px_rgba(34,211,238,0.25)] hover:scale-105 active:scale-95 transition-all">
                  <MdAutoAwesome size={16} className="text-cyan-400" />
                  <span>Mở rộng AI (+60s)</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Stats row ── */}
      <div className="px-6 mb-6">
        <div className="flex gap-3 flex-wrap">
          <StatPill icon={FiTrendingUp} value={(song.play_count ?? 0).toLocaleString()} label="lượt nghe" color="text-indigo-400" />
          <StatPill icon={FiHeart} value={likesCount} label="lượt thích" color="text-pink-400" />
          <StatPill icon={FiClock} value={fmtDur(song.duration)} label="thời lượng" color="text-blue-400" />
          {song.tempo && <StatPill icon={MdMusicNote} value={`${song.tempo}`} label="BPM" color="text-emerald-400" />}
          <StatPill icon={FiMessageCircle} value={comments.length} label="bình luận" color="text-amber-400" />
        </div>
      </div>

      {/* ── Main content ── */}
      <div className="px-6 pb-12 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: lyrics + comments */}
        <div className="lg:col-span-2 space-y-6">

          {/* Lyrics */}
          {song.lyrics && (
            <div className="glass-card rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-bold text-white text-base">Lời bài hát</h3>
                <span className="text-xs text-white/40">Sonavia AI Lyrics</span>
              </div>
              <div className={clsx('relative overflow-hidden transition-all duration-300', lyricsExpanded ? 'max-h-none' : 'max-h-48')}>
                <pre className="font-sans text-sm text-white/70 leading-relaxed whitespace-pre-wrap">{song.lyrics}</pre>
                {!lyricsExpanded && (
                  <div className="absolute inset-x-0 bottom-0 h-16 bg-gradient-to-t from-[#0e0e1a] to-transparent pointer-events-none" />
                )}
              </div>
              <div className="mt-4 pt-3 border-t border-white/5 flex justify-end">
                <button onClick={() => setLyricsExpanded(!lyricsExpanded)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors font-medium">
                  {lyricsExpanded ? 'Thu gọn' : 'Xem toàn bộ lời bài hát'}
                </button>
              </div>
            </div>
          )}

          {/* Comments */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="font-bold text-white text-base mb-4">
              Bình luận ({comments.length})
            </h3>

            {/* Comment form */}
            {isAuthenticated ? (
              <form onSubmit={handleComment} className="flex gap-3 mb-6">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center text-xs font-bold shrink-0 text-white">
                  {currentUser?.username?.[0]?.toUpperCase()}
                </div>
                <div className="flex-1 flex gap-2">
                  <input
                    type="text"
                    value={newComment}
                    onChange={e => setNewComment(e.target.value)}
                    placeholder="Viết cảm nghĩ về bài hát..."
                    className="flex-1 input text-sm"
                  />
                  <button type="submit" disabled={!newComment.trim()} className="btn-primary px-4 py-2 text-sm">Gửi</button>
                </div>
              </form>
            ) : (
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center mb-6">
                <p className="text-sm text-white/50">
                  <Link to="/login" className="text-indigo-400 hover:underline">Đăng nhập</Link> để tham gia bình luận
                </p>
              </div>
            )}

            {/* Comment list */}
            {comments.length === 0 ? (
              <p className="text-center text-white/30 text-sm py-8">Chưa có bình luận nào. Hãy là người đầu tiên!</p>
            ) : (
              <div className="space-y-4">
                {comments.map(c => {
                  let timeAgo = ''
                  try {
                    timeAgo = formatDistanceToNow(new Date(c.created_at), { addSuffix: true, locale: vi })
                  } catch { timeAgo = '' }
                  return (
                    <div key={c.id} className="flex gap-3">
                      <Link to={`/profile/${c.user?.username}`}
                        className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-xs font-bold text-white shrink-0 hover:scale-105 transition-transform">
                        {c.user?.username?.[0]?.toUpperCase()}
                      </Link>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-baseline gap-2 mb-1">
                          <Link to={`/profile/${c.user?.username}`} className="text-xs font-bold text-white hover:text-indigo-300 transition-colors">
                            {c.user?.username}
                          </Link>
                          {timeAgo && <span className="text-[10px] text-white/30">{timeAgo}</span>}
                        </div>
                        <p className="text-sm text-white/80 leading-relaxed break-words">{c.content}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right: similar songs */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white text-base">Bài hát tương tự</h3>
            <span className="text-xs text-white/30">AI Recommender</span>
          </div>
          {similar.length === 0 ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="flex items-center gap-3 p-2.5 rounded-xl skeleton h-14" />
              ))}
            </div>
          ) : (
            <div className="space-y-1.5">
              {similar.slice(0, 8).map(s => {
                const g = COVER_GRADIENTS[s.id % COVER_GRADIENTS.length]
                return (
                  <Link key={s.id} to={`/songs/${s.id}`}
                    className="flex items-center gap-3 p-2.5 rounded-xl hover:bg-white/[0.05] transition-all group border border-transparent hover:border-white/[0.06]">
                    <div className="w-10 h-10 rounded-xl overflow-hidden shrink-0">
                      {s.cover_image_url
                        ? <img src={s.cover_image_url} className="w-full h-full object-cover group-hover:scale-105 transition-transform" alt={s.title} />
                        : <div className={`w-full h-full bg-gradient-to-br ${g} flex items-center justify-center`}>🎵</div>
                      }
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm text-white/85 truncate group-hover:text-indigo-300 transition-colors font-medium">{s.title}</p>
                      <p className="text-xs text-white/30 truncate">{s.artist?.username}</p>
                    </div>
                  </Link>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
