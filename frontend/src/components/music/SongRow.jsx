import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FiPlay, FiPause, FiHeart } from 'react-icons/fi'
import usePlayerStore from '../../store/playerStore'
import useAuthStore from '../../store/authStore'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600', 'from-cyan-600 to-blue-600',
]

function fmtDur(s) {
  if (!s) return '--:--'
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
}

export default function SongRow({ song, index, queue = [] }) {
  const { playSong, currentSong, isPlaying, togglePlay } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const [liked, setLiked] = useState(song.is_liked)
  const [likesCount, setLikesCount] = useState(song.likes_count || 0)
  const isActive = currentSong?.id === song.id
  const grad = COVER_GRADIENTS[song.id % COVER_GRADIENTS.length]

  const handlePlay = () => {
    if (isActive) togglePlay()
    else playSong(song, queue.length ? queue : [song])
  }

  const handleLike = async (e) => {
    e.stopPropagation()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/songs/${song.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
    } catch { }
  }

  return (
    <div
      onClick={handlePlay}
      className={clsx(
        'flex items-center gap-3 px-3 py-2 rounded-xl cursor-pointer group transition-all duration-150',
        isActive
          ? 'bg-gradient-to-r from-indigo-500/15 via-purple-500/10 to-cyan-500/5 border border-indigo-500/30 text-white shadow-[0_0_15px_rgba(99,102,241,0.15)]'
          : 'hover:bg-white/[0.05] border border-transparent'
      )}
    >
      {/* Index / play */}
      <div className="w-7 text-center shrink-0">
        <div className={clsx('text-xs group-hover:hidden flex items-center justify-center', isActive ? 'text-indigo-400' : 'text-white/25')}>
          {isActive && isPlaying
            ? <div className="eq-bars"><div className="eq-bar" /><div className="eq-bar" /><div className="eq-bar" /></div>
            : <span>{index + 1}</span>
          }
        </div>
        <div className="hidden group-hover:flex items-center justify-center">
          {isActive && isPlaying
            ? <FiPause size={13} className="text-indigo-400" />
            : <FiPlay size={13} className="text-white" />
          }
        </div>
      </div>

      {/* Cover */}
      <div className="w-9 h-9 rounded-lg overflow-hidden shrink-0">
        {song.cover_image_url
          ? <img src={song.cover_image_url} alt={song.title} className="w-full h-full object-cover" />
          : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-sm`}>🎵</div>
        }
      </div>

      {/* Title */}
      <div className="flex-1 min-w-0">
        <Link to={`/songs/${song.id}`} onClick={e => e.stopPropagation()}
          className={clsx('text-sm font-medium truncate block hover:text-indigo-300 transition-colors',
            isActive ? 'text-indigo-300' : 'text-white/90')}>
          {song.title}
        </Link>
        <Link to={`/profile/${song.artist?.username}`} onClick={e => e.stopPropagation()}
          className="text-xs text-white/35 hover:text-white/60 truncate block transition-colors">
          {song.artist?.username}
        </Link>
      </div>

      {/* Genre tag */}
      <span className="hidden sm:block text-[10px] text-white/25 font-medium uppercase tracking-wide w-16 text-center">
        {song.genre}
      </span>

      {/* Like */}
      <button onClick={handleLike}
        className={clsx('flex items-center gap-1 text-[11px] transition-all px-1.5 py-1 rounded-lg shrink-0',
          liked ? 'text-pink-400' : 'text-white/20 hover:text-pink-400'
        )}
      >
        <FiHeart size={11} className={liked ? 'fill-current' : ''} />
        <span className="hidden sm:inline">{likesCount}</span>
      </button>

      {/* Duration */}
      <span className="text-xs text-white/25 w-9 text-right shrink-0 tabular-nums">{fmtDur(song.duration)}</span>
    </div>
  )
}
