import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiSearch, FiX, FiMusic, FiUser, FiTrendingUp } from 'react-icons/fi'
import api from '../../api/axios'
import usePlayerStore from '../../store/playerStore'
import clsx from 'clsx'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
]

export default function SearchModal({ onClose }) {
  const [query, setQuery] = useState('')
  const [songs, setSongs] = useState([])
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(0)
  const inputRef = useRef()
  const navigate = useNavigate()
  const { playSong } = usePlayerStore()

  useEffect(() => {
    inputRef.current?.focus()
    // Keyboard shortcuts
    const handler = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowDown') setSelected(s => Math.min(s + 1, songs.length + users.length - 1))
      if (e.key === 'ArrowUp') setSelected(s => Math.max(s - 1, 0))
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [songs, users])

  useEffect(() => {
    if (!query.trim()) { setSongs([]); setUsers([]); setSelected(0); return }
    setSelected(0)
    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const [sRes, uRes] = await Promise.all([
          api.get(`/music/songs/?search=${encodeURIComponent(query)}&page_size=5`),
          api.get(`/auth/users/?search=${encodeURIComponent(query)}`),
        ])
        let fetchedSongs = (sRes.data.results || sRes.data || []).slice(0, 5)
        // Nếu kết quả tìm kiếm theo từ khóa ít, kết hợp tìm kiếm ngữ nghĩa Neural Semantic Search AI
        if (fetchedSongs.length < 2) {
          try {
            const semRes = await api.get(`/music/songs/semantic-search/?q=${encodeURIComponent(query)}&limit=5`)
            const semSongs = semRes.data.results || []
            if (semSongs.length > 0) {
              const existingIds = new Set(fetchedSongs.map(s => s.id))
              for (const s of semSongs) {
                if (!existingIds.has(s.id)) {
                  fetchedSongs.push({ ...s, isSemantic: true })
                  existingIds.add(s.id)
                }
              }
            }
          } catch {}
        }
        setSongs(fetchedSongs.slice(0, 5))
        setUsers((uRes.data.results || uRes.data || []).slice(0, 3))
      } catch { }
      setLoading(false)
    }, 300)
    return () => clearTimeout(timer)
  }, [query])

  const handleSongClick = (song) => {
    playSong(song, songs)
    navigate(`/songs/${song.id}`)
    onClose()
  }

  const handleUserClick = (user) => {
    navigate(`/profile/${user.username}`)
    onClose()
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(`/explore?search=${encodeURIComponent(query)}`)
      onClose()
    }
  }

  const totalResults = songs.length + users.length

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[10vh] px-4"
      style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="w-full max-w-xl animate-slide-up">
        {/* Search input */}
        <form onSubmit={handleSubmit}
          className="flex items-center gap-3 px-4 py-3 bg-dark-700/90 border border-white/10 rounded-2xl mb-2 backdrop-blur-sm">
          <FiSearch className="text-white/40 shrink-0 text-lg" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Tìm bài hát, nghệ sĩ..."
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="flex-1 bg-transparent text-white placeholder-white/30 outline-none text-base"
          />
          {loading && <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin shrink-0" />}
          <button type="button" onClick={onClose} className="text-white/30 hover:text-white shrink-0 transition-colors">
            <FiX size={18} />
          </button>
        </form>

        {/* Results */}
        {(songs.length > 0 || users.length > 0) && (
          <div className="bg-dark-700/95 border border-white/[0.08] rounded-2xl overflow-hidden backdrop-blur-sm">
            {/* Songs */}
            {songs.length > 0 && (
              <div>
                <div className="px-4 pt-3 pb-1.5 flex items-center gap-2 text-[10px] font-bold text-white/30 uppercase tracking-widest">
                  <FiMusic size={10} /> Bài hát
                </div>
                {songs.map((song, i) => {
                  const grad = COVER_GRADIENTS[song.id % COVER_GRADIENTS.length]
                  return (
                    <button key={song.id} onClick={() => handleSongClick(song)}
                      className={clsx(
                        'w-full flex items-center gap-3 px-4 py-2.5 transition-all text-left group',
                        selected === i ? 'bg-indigo-500/15' : 'hover:bg-white/[0.04]'
                      )}>
                      <div className="w-9 h-9 rounded-lg overflow-hidden shrink-0">
                        {song.cover_image_url
                          ? <img src={song.cover_image_url} className="w-full h-full object-cover" alt={song.title} />
                          : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-sm`}>🎵</div>
                        }
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">{song.title}</p>
                        <p className="text-xs text-white/35 truncate">{song.artist?.username}</p>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {song.isSemantic && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium border border-indigo-500/30">
                            AI Match
                          </span>
                        )}
                        <span className="text-[10px] text-white/20 uppercase">{song.genre}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}

            {/* Users */}
            {users.length > 0 && (
              <div className={songs.length > 0 ? 'border-t border-white/[0.05]' : ''}>
                <div className="px-4 pt-3 pb-1.5 flex items-center gap-2 text-[10px] font-bold text-white/30 uppercase tracking-widest">
                  <FiUser size={10} /> Người dùng
                </div>
                {users.map((user, i) => (
                  <button key={user.id} onClick={() => handleUserClick(user)}
                    className={clsx(
                      'w-full flex items-center gap-3 px-4 py-2.5 transition-all text-left',
                      selected === songs.length + i ? 'bg-indigo-500/15' : 'hover:bg-white/[0.04]'
                    )}>
                    <div className="w-9 h-9 rounded-full overflow-hidden shrink-0">
                      {user.avatar_url
                        ? <img src={user.avatar_url} className="w-full h-full object-cover" alt={user.username} />
                        : <div className="w-full h-full bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-sm font-bold text-white">
                          {user.username?.[0]?.toUpperCase()}
                        </div>
                      }
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">{user.username}</p>
                      <p className="text-xs text-white/35">{user.is_artist ? '🎤 Nghệ sĩ' : '🎧 Người nghe'}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* View all */}
            {query.trim() && (
              <button onClick={handleSubmit}
                className="w-full py-3 text-xs text-center transition-all border-t border-white/[0.05] flex items-center justify-center gap-1.5"
                style={{ color: '#818cf8' }}
                onMouseEnter={e => { e.currentTarget.style.color = '#a5b4fc'; e.currentTarget.style.background = 'rgba(99,102,241,0.08)' }}
                onMouseLeave={e => { e.currentTarget.style.color = '#818cf8'; e.currentTarget.style.background = 'transparent' }}>
                <FiTrendingUp size={12} />
                Xem tất cả kết quả cho "<span className="font-bold">{query}</span>"
              </button>
            )}
          </div>
        )}

        {/* Empty state */}
        {query && !loading && songs.length === 0 && users.length === 0 && (
          <div className="bg-dark-700/95 border border-white/[0.08] rounded-2xl p-8 text-center backdrop-blur-sm">
            <p className="text-3xl mb-2">🔍</p>
            <p className="text-white/40 text-sm">Không tìm thấy kết quả cho "<span className="text-white/70">{query}</span>"</p>
          </div>
        )}

        {/* Shortcuts hint */}
        {!query && (
          <div className="text-center text-[11px] text-white/20 mt-3 flex items-center justify-center gap-4">
            <span><kbd className="bg-white/10 px-1.5 py-0.5 rounded text-[10px]">↑↓</kbd> Điều hướng</span>
            <span><kbd className="bg-white/10 px-1.5 py-0.5 rounded text-[10px]">Enter</kbd> Tìm kiếm</span>
            <span><kbd className="bg-white/10 px-1.5 py-0.5 rounded text-[10px]">Esc</kbd> Đóng</span>
          </div>
        )}
      </div>
    </div>
  )
}
