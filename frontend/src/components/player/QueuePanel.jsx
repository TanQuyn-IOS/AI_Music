import { FiX, FiList } from 'react-icons/fi'
import { Link } from 'react-router-dom'
import usePlayerStore from '../../store/playerStore'
import clsx from 'clsx'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600', 'from-cyan-600 to-blue-600',
]

function fmtDur(s) {
  if (!s) return ''
  const sec = Math.floor(s)
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, '0')}`
}

export default function QueuePanel({ onClose }) {
  // Dùng jumpToSong thay vì playSong để tránh re-shuffle queue
  const { queue, currentSong, jumpToSong, isPlaying } = usePlayerStore()

  if (!queue.length) return null

  return (
    <div className="fixed bottom-20 right-4 z-40 w-80 animate-slide-up"
      style={{ background: 'rgba(16,16,32,0.97)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '16px', backdropFilter: 'blur(20px)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
        <div className="flex items-center gap-2">
          <FiList size={14} className="text-indigo-400" />
          <span className="text-sm font-bold text-white">Hàng chờ</span>
          <span className="text-xs text-white/30">({queue.length} bài)</span>
        </div>
        <button onClick={onClose} className="text-white/30 hover:text-white transition-colors">
          <FiX size={16} />
        </button>
      </div>

      {/* Queue list */}
      <div className="overflow-y-auto max-h-72 p-2">
        {queue.map((song, i) => {
          const isActive = currentSong?.id === song.id
          const grad = COVER_GRADIENTS[song.id % COVER_GRADIENTS.length]
          return (
            <button key={`${song.id}-${i}`}
              onClick={() => jumpToSong(song)}
              className={clsx(
                'w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl transition-all text-left group',
                isActive ? 'bg-indigo-500/15 border border-indigo-500/20' : 'hover:bg-white/[0.04]'
              )}>
              {/* Number */}
              <span className={clsx('text-xs w-5 text-center shrink-0 tabular-nums', isActive ? 'text-indigo-400' : 'text-white/25')}>
                {isActive ? '▶' : i + 1}
              </span>

              {/* Cover */}
              <div className="w-8 h-8 rounded-lg overflow-hidden shrink-0">
                {song.cover_image_url
                  ? <img src={song.cover_image_url} className="w-full h-full object-cover" alt={song.title} />
                  : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-xs`}>🎵</div>
                }
              </div>

              {/* Info */}
              <div className="min-w-0 flex-1">
                <p className={clsx('text-xs font-semibold truncate', isActive ? 'text-indigo-300' : 'text-white/80 group-hover:text-white')}>
                  {song.title}
                </p>
                <p className="text-[10px] text-white/30 truncate">{song.artist?.username}</p>
              </div>

              {/* Duration */}
              <span className="text-[10px] text-white/20 shrink-0 tabular-nums">{fmtDur(song.duration)}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
