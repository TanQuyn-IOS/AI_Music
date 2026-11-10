import { useEffect, useState, useRef } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { FiSearch, FiGrid, FiList, FiPlay, FiPause, FiHeart } from 'react-icons/fi'
import { MdMusicNote } from 'react-icons/md'
import api from '../api/axios'
import usePlayerStore from '../store/playerStore'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

// ─── Constants ────────────────────────────────────────────────────────────────

const GENRES = [
  { key: '', label: 'Tất cả' },
  { key: 'vpop', label: '🇻🇳 V-Pop' },
  { key: 'ballad', label: '🎼 Ballad' },
  { key: 'lofi', label: '☕ Lo-fi' },
  { key: 'acoustic', label: '🎸 Acoustic' },
  { key: 'bolero', label: '📻 Bolero' },
  { key: 'kpop', label: '🇰🇷 K-Pop' },
  { key: 'jpop', label: '🇯🇵 J-Pop' },
  { key: 'cpop', label: '🇨🇳 C-Pop' },
  { key: 'pop', label: '🎤 Pop' },
  { key: 'rock', label: '🎸 Rock' },
  { key: 'jazz', label: '🎷 Jazz' },
  { key: 'classical', label: '🎻 Classic' },
  { key: 'hip_hop', label: '🎧 Hip-Hop' },
  { key: 'electronic', label: '🎹 EDM' },
  { key: 'r&b', label: '🎵 R&B' },
  { key: 'folk', label: '🪕 Folk' },
  { key: 'indie', label: '🌿 Indie' },
]

const MOODS = [
  { key: '', label: 'Tất cả' },
  { key: 'happy', label: '😄 Vui' },
  { key: 'sad', label: '😢 Buồn' },
  { key: 'energetic', label: '⚡ Sôi động' },
  { key: 'calm', label: '🌿 Bình yên' },
  { key: 'romantic', label: '💕 Lãng mạn' },
  { key: 'melancholic', label: '🌙 Hoài niệm' },
  { key: 'uplifting', label: '🌟 Phấn khởi' },
]

const GRADS = [
  ['#7c3aed', '#a855f7'], ['#db2777', '#ec4899'], ['#0284c7', '#38bdf8'],
  ['#059669', '#34d399'], ['#d97706', '#f59e0b'], ['#dc2626', '#f87171'],
  ['#7c3aed', '#ec4899'], ['#0891b2', '#a855f7'],
]
const songGrad = (id) => {
  const [a, b] = GRADS[id % GRADS.length]
  return `linear-gradient(135deg, ${a}, ${b})`
}

// ─── Song Card Grid (Suno-style) ──────────────────────────────────────────────

function SongCardGrid({ song, queue = [] }) {
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const [liked, setLiked] = useState(song.is_liked)
  const [likesCount, setLikesCount] = useState(song.likes_count || 0)
  const [hovered, setHovered] = useState(false)
  const isActive = currentSong?.id === song.id

  const handlePlay = (e) => {
    e.preventDefault()
    if (isActive) togglePlay()
    else playSong(song, queue.length ? queue : [song])
  }

  const handleLike = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <Link to={`/songs/${song.id}`}
      className={clsx(
        'group block rounded-2xl overflow-hidden transition-all duration-300 sonavia-glass-card',
        isActive
          ? 'ring-2 ring-cyan-400/50 shadow-lg shadow-indigo-500/15'
          : 'hover:-translate-y-1 hover:shadow-xl hover:shadow-black/40'
      )}
      style={{ background: 'rgba(16,19,44,0.65)', border: `1px solid ${isActive ? 'rgba(34,211,238,0.45)' : 'rgba(255,255,255,0.08)'}` }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Cover art */}
      <div className="relative aspect-square overflow-hidden">
        {song.cover_image_url
          ? <img src={song.cover_image_url} alt={song.title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
          : <div className="w-full h-full flex items-center justify-center" style={{ background: songGrad(song.id) }}>
            <MdMusicNote size={40} className="text-white/40" />
          </div>
        }

        {/* Dark overlay on hover */}
        <div className={clsx(
          'absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent transition-opacity duration-200',
          hovered || isActive ? 'opacity-100' : 'opacity-0'
        )} />

        {/* Play button */}
        <button onClick={handlePlay}
          className={clsx(
            'absolute bottom-3 right-3 w-11 h-11 rounded-full bg-white flex items-center justify-center shadow-xl transition-all duration-200',
            hovered || isActive ? 'opacity-100 translate-y-0 scale-100' : 'opacity-0 translate-y-2 scale-90'
          )}>
          {isActive && isPlaying
            ? <FiPause size={18} className="text-black" />
            : <FiPlay size={18} className="text-black ml-0.5" />
          }
        </button>

        {/* Active indicator */}
        {isActive && isPlaying && (
          <div className="absolute top-3 left-3">
            <div className="flex items-end gap-0.5 h-4 bg-black/50 px-2 py-1 rounded-full">
              <div className="eq-bars scale-75"><div className="eq-bar" /><div className="eq-bar" /><div className="eq-bar" /></div>
            </div>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-3.5">
        <p className={clsx(
          'font-semibold text-sm truncate mb-0.5 transition-colors',
          isActive ? 'text-indigo-300' : 'text-white group-hover:text-indigo-200'
        )}>{song.title}</p>
        <p className="text-[11px] text-white/40 truncate mb-2.5">{song.artist?.username}</p>

        <div className="flex items-center justify-between">
          <div className="flex gap-1.5">
            {song.genre && (
              <span className="text-[9px] font-semibold px-2 py-0.5 rounded-full"
                style={{ background: 'rgba(139,92,246,0.15)', color: '#c4b5fd', border: '1px solid rgba(139,92,246,0.2)' }}>
                {song.genre}
              </span>
            )}
          </div>
          <button onClick={handleLike}
            className={clsx(
              'flex items-center gap-1 text-[11px] transition-all px-1.5 py-0.5 rounded-lg',
              liked ? 'text-pink-400' : 'text-white/25 hover:text-pink-400'
            )}>
            <FiHeart size={11} className={liked ? 'fill-current' : ''} />
            <span>{likesCount}</span>
          </button>
        </div>
      </div>
    </Link>
  )
}

// ─── Song Row (list view) ─────────────────────────────────────────────────────

function SongRow({ song, index, queue = [] }) {
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const [liked, setLiked] = useState(song.is_liked)
  const [likesCount, setLikesCount] = useState(song.likes_count || 0)
  const isActive = currentSong?.id === song.id

  const handlePlay = () => { if (isActive) togglePlay(); else playSong(song, queue) }
  const handleLike = async (e) => {
    e.stopPropagation()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <div onClick={handlePlay}
      className={clsx(
        'flex items-center gap-3.5 px-4 py-3 cursor-pointer transition-all duration-150 group rounded-xl',
        isActive ? 'bg-indigo-500/10 border border-indigo-500/20' : 'hover:bg-white/[0.04] border border-transparent'
      )}>
      <div className="w-6 text-center shrink-0">
        <span className={clsx('text-xs group-hover:hidden', isActive ? 'text-indigo-400' : 'text-white/25')}>
          {isActive && isPlaying
            ? <span className="flex justify-center"><div className="eq-bars scale-75"><div className="eq-bar" /><div className="eq-bar" /><div className="eq-bar" /></div></span>
            : index + 1
          }
        </span>
        <div className="hidden group-hover:flex justify-center items-center">
          {isActive && isPlaying ? <FiPause size={13} className="text-indigo-400" /> : <FiPlay size={13} className="text-white" />}
        </div>
      </div>
      <div className="w-10 h-10 rounded-xl overflow-hidden shrink-0">
        {song.cover_image_url
          ? <img src={song.cover_image_url} className="w-full h-full object-cover" alt="" />
          : <div className="w-full h-full" style={{ background: songGrad(song.id) }} />
        }
      </div>
      <div className="flex-1 min-w-0">
        <p className={clsx('text-sm font-medium truncate transition-colors', isActive ? 'text-indigo-300' : 'text-white/85 group-hover:text-white')}>
          {song.title}
        </p>
        <p className="text-[11px] text-white/35 truncate">{song.artist?.username}</p>
      </div>
      {song.genre && <span className="hidden sm:block text-[9px] text-white/25 uppercase">{song.genre}</span>}
      <button onClick={handleLike}
        className={clsx('flex items-center gap-1 text-[11px] px-1.5 py-1 rounded-lg transition-all',
          liked ? 'text-pink-400' : 'text-white/20 hover:text-pink-400')}>
        <FiHeart size={11} className={liked ? 'fill-current' : ''} />
        <span className="hidden sm:inline">{likesCount}</span>
      </button>
      <span className="text-[11px] text-white/20 tabular-nums hidden sm:block">
        {song.duration ? `${Math.floor(song.duration / 60)}:${String(song.duration % 60).padStart(2, '0')}` : ''}
      </span>
    </div>
  )
}

// ─── Skeletons ────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="rounded-2xl overflow-hidden animate-pulse" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}>
      <div className="aspect-square skeleton" />
      <div className="p-3.5 space-y-2">
        <div className="h-3 skeleton rounded w-3/4" />
        <div className="h-2.5 skeleton rounded w-1/2" />
      </div>
    </div>
  )
}

// ─── ExplorePage ──────────────────────────────────────────────────────────────

export default function ExplorePage() {
  const [searchParams] = useSearchParams()
  const [songs, setSongs] = useState([])
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState(searchParams.get('search') || '')
  const [genre, setGenre] = useState(searchParams.get('genre') || '')
  const [mood, setMood] = useState('')
  const [ordering, setOrdering] = useState('-play_count')
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)
  const [viewGrid, setViewGrid] = useState(true)
  const pageRef = useRef(1)
  const searchTimerRef = useRef()

  const fetchSongs = async (reset = false) => {
    setLoading(true)
    const p = reset ? 1 : pageRef.current
    try {
      const params = new URLSearchParams()
      if (search) params.set('search', search)
      if (genre) params.set('genre', genre)
      if (mood) params.set('mood', mood)
      params.set('ordering', ordering)
      params.set('page', p)
      const { data } = await api.get(`/music/songs/?${params}`)
      const rawResults = data?.results || data
      const results = Array.isArray(rawResults) ? rawResults : []
      if (reset) { setSongs(results); pageRef.current = 2 }
      else { setSongs(prev => [...prev, ...results]); pageRef.current = p + 1 }
      setTotal(data?.count ?? results.length)
      setHasMore(!!data?.next)
    } catch { }
    setLoading(false)
  }

  // Debounce search
  useEffect(() => {
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => fetchSongs(true), search ? 400 : 0)
    return () => clearTimeout(searchTimerRef.current)
  }, [search, genre, mood, ordering])

  return (
    <div className="animate-fade-in min-h-full">
      {/* ── Header ── */}
      <div className="px-6 pt-7 pb-5 border-b border-white/[0.04]">
        <div className="max-w-screen-xl mx-auto">
          {/* Search */}
          <div className="flex gap-3 mb-5">
            <div className="relative flex-1 max-w-lg">
              <FiSearch size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/25" />
              <input
                value={search}
                onChange={e => setSearch(e.target.value)}
                placeholder="Tìm bài hát, nghệ sĩ..."
                className="input-field pl-9 text-sm w-full"
              />
              {search && (
                <button onClick={() => setSearch('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/25 hover:text-white/60 transition-colors text-xs">✕</button>
              )}
            </div>

            <select value={ordering} onChange={e => setOrdering(e.target.value)}
              className="input-field w-auto text-sm cursor-pointer shrink-0">
              <option value="-play_count">Phổ biến nhất</option>
              <option value="-created_at">Mới nhất</option>
              <option value="title">Tên A-Z</option>
            </select>

            <div className="flex items-center gap-1 p-1 rounded-xl shrink-0"
              style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' }}>
              <button onClick={() => setViewGrid(true)}
                className={clsx('p-2 rounded-lg transition-all', viewGrid ? 'bg-indigo-600 text-white' : 'text-white/30 hover:text-white')}>
                <FiGrid size={14} />
              </button>
              <button onClick={() => setViewGrid(false)}
                className={clsx('p-2 rounded-lg transition-all', !viewGrid ? 'bg-indigo-600 text-white' : 'text-white/30 hover:text-white')}>
                <FiList size={14} />
              </button>
            </div>
          </div>

          {/* Genre pills */}
          <div className="flex gap-2 flex-wrap mb-3">
            {GENRES.map(g => (
              <button key={g.key} onClick={() => setGenre(g.key)}
                className={clsx(
                  'px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all',
                  genre === g.key
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                    : 'text-white/40 hover:text-white hover:bg-white/[0.07]'
                )}
                style={genre !== g.key ? { background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.06)' } : {}}>
                {g.label}
              </button>
            ))}
          </div>

          {/* Mood pills */}
          <div className="flex gap-2 flex-wrap">
            {MOODS.map(m => (
              <button key={m.key} onClick={() => setMood(m.key)}
                className={clsx(
                  'px-3 py-1 rounded-full text-[11px] font-semibold transition-all',
                  mood === m.key
                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-500/20'
                    : 'text-white/35 hover:text-white/70'
                )}
                style={mood !== m.key ? { background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' } : {}}>
                {m.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Results ── */}
      <div className="max-w-screen-xl mx-auto px-6 py-6">
        {total > 0 && (
          <p className="text-xs text-white/25 mb-5 font-medium">
            {total.toLocaleString()} bài hát
            {(genre || mood || search) && <span className="text-white/15"> · đã lọc</span>}
          </p>
        )}

        {loading && songs.length === 0 ? (
          viewGrid
            ? <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {[...Array(10)].map((_, i) => <SkeletonCard key={i} />)}
            </div>
            : <div className="space-y-1">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="flex items-center gap-3.5 px-4 py-3 animate-pulse">
                  <div className="w-6 h-4 skeleton rounded shrink-0" />
                  <div className="w-10 h-10 skeleton rounded-xl shrink-0" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3 skeleton rounded w-2/3" />
                    <div className="h-2.5 skeleton rounded w-1/3" />
                  </div>
                </div>
              ))}
            </div>
        ) : songs.length === 0 ? (
          <div className="text-center py-24">
            <div className="text-5xl mb-4">🔍</div>
            <p className="text-white/40 text-lg font-semibold mb-1">Không tìm thấy</p>
            <p className="text-white/20 text-sm">Thử tìm với từ khoá khác</p>
          </div>
        ) : viewGrid ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {songs.map(s => <SongCardGrid key={s.id} song={s} queue={songs} />)}
          </div>
        ) : (
          <div className="rounded-2xl overflow-hidden"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)' }}>
            {songs.map((s, i) => <SongRow key={s.id} song={s} index={i} queue={songs} />)}
          </div>
        )}

        {/* Load more */}
        {hasMore && (
          <div className="text-center mt-8">
            <button onClick={() => fetchSongs(false)} disabled={loading}
              className="px-8 py-2.5 rounded-xl text-sm font-semibold text-white/50 hover:text-white transition-all"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
              {loading ? 'Đang tải...' : 'Xem thêm'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
