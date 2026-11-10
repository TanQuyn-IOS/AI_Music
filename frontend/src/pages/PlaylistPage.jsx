import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FiPlay, FiLock, FiGlobe, FiClock } from 'react-icons/fi'
import { MdMusicNote } from 'react-icons/md'
import api from '../api/axios'
import usePlayerStore from '../store/playerStore'
import SongRow from '../components/music/SongRow'

function fmtDur(s) {
  if (!s) return '0:00'
  const m = Math.floor(s / 60); const sec = s % 60
  return `${m}:${String(sec).padStart(2, '0')}`
}

export default function PlaylistPage() {
  const { id } = useParams()
  const [playlist, setPlaylist] = useState(null)
  const { playSong } = usePlayerStore()

  useEffect(() => {
    api.get(`/music/playlists/${id}/`).then(r => setPlaylist(r.data)).catch(() => { })
  }, [id])

  if (!playlist) return (
    <div className="p-6 max-w-3xl mx-auto animate-pulse space-y-4">
      <div className="flex gap-6">
        <div className="w-48 h-48 skeleton rounded-3xl shrink-0" />
        <div className="flex-1 space-y-3 pt-4">
          <div className="h-8 skeleton rounded w-2/3" />
          <div className="h-4 skeleton rounded w-1/3" />
          <div className="h-4 skeleton rounded w-1/4" />
        </div>
      </div>
    </div>
  )

  const totalDuration = playlist.songs?.reduce((a, s) => a + (s.duration || 0), 0) || 0

  return (
    <div className="animate-fade-in max-w-3xl mx-auto">
      {/* Header */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/30 to-violet-900/20" />
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#070711]" />

        <div className="relative px-6 pt-8 pb-6 flex gap-7 items-end flex-wrap">
          {/* Cover */}
          <div className="relative shrink-0">
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-3xl blur-xl opacity-50 scale-90" />
            <div className="relative w-44 h-44 rounded-3xl bg-gradient-to-br from-indigo-700 to-violet-700 flex items-center justify-center shadow-2xl overflow-hidden">
              {playlist.cover_image_url
                ? <img src={playlist.cover_image_url} className="w-full h-full object-cover" alt={playlist.name} />
                : <MdMusicNote size={60} className="text-white/40" />
              }
            </div>
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0 pb-1">
            <p className="text-xs text-white/40 font-semibold uppercase tracking-widest mb-2">Playlist</p>
            <h1 className="text-3xl font-black text-white mb-2 leading-tight">{playlist.name}</h1>
            <Link to={`/profile/${playlist.owner?.username}`}
              className="text-sm text-white/50 hover:text-indigo-300 transition-colors">
              by {playlist.owner?.username}
            </Link>
            {playlist.description && (
              <p className="text-sm text-white/35 mt-2 leading-relaxed">{playlist.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3 text-xs text-white/30">
              <span className="flex items-center gap-1">
                <MdMusicNote size={12} /> {playlist.songs_count} bài
              </span>
              <span className="flex items-center gap-1">
                <FiClock size={11} /> {fmtDur(totalDuration)}
              </span>
              <span className="flex items-center gap-1">
                {playlist.is_public ? <><FiGlobe size={11} /> Công khai</> : <><FiLock size={11} /> Riêng tư</>}
              </span>
            </div>

            {playlist.songs?.length > 0 && (
              <button
                onClick={() => playSong(playlist.songs[0], playlist.songs)}
                className="mt-4 flex items-center gap-2.5 px-6 py-3 bg-white text-black font-bold rounded-full hover:scale-105 active:scale-95 transition-all shadow-lg text-sm">
                <FiPlay size={16} className="ml-0.5" /> Phát tất cả
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Song list */}
      <div className="px-6 pb-12 mt-2">
        {playlist.songs?.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-4xl mb-3">🎵</p>
            <p className="text-white/40 font-semibold mb-3">Playlist chưa có bài hát nào</p>
            <Link to="/explore" className="btn-primary text-xs px-4 py-2 inline-flex items-center gap-1.5">
              Khám phá bài hát để thêm vào
            </Link>
          </div>
        ) : (
          <div className="space-y-0.5">
            {playlist.songs?.map((song, i) => (
              <SongRow key={song.id} song={song} index={i} queue={playlist.songs} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
