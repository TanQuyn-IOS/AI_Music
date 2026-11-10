import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FiPlay, FiPause, FiHeart } from 'react-icons/fi'
import usePlayerStore from '../../store/playerStore'
import useAuthStore from '../../store/authStore'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const MOOD_PILL = {
  happy: 'bg-amber-400/15 text-amber-300 border border-amber-400/20',
  sad: 'bg-blue-400/15 text-blue-300 border border-blue-400/20',
  energetic: 'bg-orange-400/15 text-orange-300 border border-orange-400/20',
  calm: 'bg-emerald-400/15 text-emerald-300 border border-emerald-400/20',
  romantic: 'bg-pink-400/15 text-pink-300 border border-pink-400/20',
  angry: 'bg-red-400/15 text-red-300 border border-red-400/20',
  melancholic: 'bg-purple-400/15 text-purple-300 border border-purple-400/20',
  uplifting: 'bg-cyan-400/15 text-cyan-300 border border-cyan-400/20',
}
const MOOD_LABEL = {
  happy: 'Vui', sad: 'Buồn', energetic: 'Năng động', calm: 'Thư giãn',
  romantic: 'Lãng mạn', angry: 'Mạnh mẽ', melancholic: 'Hoài niệm', uplifting: 'Phấn khởi',
}
const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600',
  'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500',
  'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600',
  'from-cyan-600 to-blue-600',
]

export default function SongCard({ song, queue = [] }) {
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const [liked, setLiked] = useState(song.is_liked)
  const [likesCount, setLikesCount] = useState(song.likes_count || 0)
  const [hovered, setHovered] = useState(false)

  const isActive = currentSong?.id === song.id
  const gradient = COVER_GRADIENTS[song.id % COVER_GRADIENTS.length]

  const handlePlay = (e) => {
    e.preventDefault()
    if (isActive) togglePlay()
    else playSong(song, queue.length ? queue : [song])
  }

  const handleLike = async (e) => {
    e.preventDefault(); e.stopPropagation()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <Link to={`/songs/${song.id}`}
      className={clsx(
        'group relative flex flex-col rounded-2xl overflow-hidden transition-all duration-300 cursor-pointer sonavia-glass-card glass-sheen',
        'hover:shadow-card-hover hover:-translate-y-1',
        isActive ? 'border-cyan-400/50 bg-indigo-500/15 shadow-[0_0_28px_rgba(99,102,241,0.35)]' : 'border-white/[0.08] hover:border-indigo-500/35 hover:bg-white/[0.06]',
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Cover art container */}
      <div className="relative aspect-square overflow-hidden p-2 flex items-center justify-center">
        <div className={clsx(
          "w-full h-full relative overflow-hidden transition-all duration-700",
          isActive && isPlaying ? "rounded-full animate-spin-slow shadow-[0_0_24px_rgba(34,211,238,0.4)] vinyl-ring" : "rounded-xl"
        )}>
          {song.cover_image_url ? (
            <img
              src={song.cover_image_url}
              alt={song.title}
              className={clsx(
                "w-full h-full object-cover transition-transform duration-500",
                !(isActive && isPlaying) && "group-hover:scale-105"
              )}
            />
          ) : (
            <div className={`w-full h-full bg-gradient-to-br ${gradient} flex items-center justify-center`}>
              <span className="text-4xl opacity-80">🎵</span>
            </div>
          )}

          {/* Lỗ tâm đĩa than khi đang quay phát nhạc */}
          {isActive && isPlaying && <div className="vinyl-center-hole" />}
        </div>

        {/* Overlay gradient hover */}
        <div className={`absolute inset-0 bg-gradient-to-t from-black/70 via-black/0 to-black/0 transition-opacity duration-200 pointer-events-none ${hovered ? 'opacity-100' : 'opacity-0'}`} />

        {/* Play / Pause button với Shimmer Glow */}
        <button
          onClick={handlePlay}
          className={clsx(
            'absolute bottom-3.5 right-3.5 w-11 h-11 rounded-full flex items-center justify-center z-20',
            'bg-white text-dark-950 shadow-[0_0_20px_rgba(255,255,255,0.6)] transition-all duration-300 active:scale-90 hover:scale-110 btn-shimmer',
            hovered || isActive ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
          )}
        >
          {isActive && isPlaying
            ? <FiPause size={17} className="fill-current text-indigo-950" />
            : <FiPlay className="text-indigo-950 ml-0.5 fill-current" size={17} />
          }
        </button>

        {/* Active dancing Equalizer indicator */}
        {isActive && (
          <div className="absolute top-3.5 left-3.5 z-20">
            <div className="flex items-center gap-1 bg-black/75 backdrop-blur-md rounded-full px-2.5 py-1 border border-cyan-400/40 shadow-lg">
              <div className="eq-bars">
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Song Info */}
      <div className="p-3.5 pt-1">
        <p className={clsx('font-bold text-sm truncate mb-0.5 transition-colors', isActive ? 'text-cyan-300' : 'text-white group-hover:text-cyan-200')}>
          {song.title}
        </p>
        <p className="text-xs text-white/45 truncate">{song.artist?.username || 'Sonavia AI'}</p>

        <div className="flex items-center justify-between mt-2.5">
          <div className="flex items-center gap-1.5">
            {song.mood && (
              <span className={clsx('text-[10px] font-semibold px-2 py-0.5 rounded-md backdrop-blur-sm', MOOD_PILL[song.mood] || 'bg-white/10 text-white/50')}>
                {MOOD_LABEL[song.mood] || song.mood}
              </span>
            )}
          </div>
          <button
            onClick={handleLike}
            className={clsx('flex items-center gap-1 text-[11px] font-medium transition-all px-2 py-1 rounded-lg',
              liked ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' : 'text-white/30 hover:text-rose-400 hover:bg-rose-500/10'
            )}
          >
            <FiHeart size={12} className={liked ? 'fill-current' : ''} />
            <span>{likesCount}</span>
          </button>
        </div>
      </div>
    </Link>
  )
}
