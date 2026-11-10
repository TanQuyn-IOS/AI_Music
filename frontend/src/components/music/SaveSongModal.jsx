import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import {
  FiX, FiSave, FiMusic, FiCheck,
  FiGlobe, FiLock, FiTag,
} from 'react-icons/fi'
import { MdGraphicEq, MdMusicNote } from 'react-icons/md'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const GENRES = [
  { key: 'vpop',       label: '🇻🇳 V-Pop'     },
  { key: 'kpop',       label: '🇰🇷 K-Pop'     },
  { key: 'jpop',       label: '🇯🇵 J-Pop'     },
  { key: 'cpop',       label: '🇨🇳 C-Pop'     },
  { key: 'pop',        label: '🎤 Pop'         },
  { key: 'rock',       label: '🎸 Rock'        },
  { key: 'jazz',       label: '🎷 Jazz'        },
  { key: 'lofi',       label: '☕ Lo-fi'       },
  { key: 'classical',  label: '🎻 Classical'   },
  { key: 'hip_hop',    label: '🎧 Hip-Hop'    },
  { key: 'electronic', label: '🎹 Electronic' },
  { key: 'r&b',        label: '🎵 R&B'        },
  { key: 'folk',       label: '🪕 Folk'        },
  { key: 'indie',      label: '🌿 Indie'       },
  { key: 'other',      label: '🎼 Khác'        },
]


const MOODS = [
  { key: 'happy',       emoji: '😄', label: 'Vui vẻ'    },
  { key: 'sad',         emoji: '😢', label: 'Buồn'       },
  { key: 'energetic',   emoji: '⚡', label: 'Sôi động'   },
  { key: 'calm',        emoji: '🌿', label: 'Bình yên'   },
  { key: 'romantic',    emoji: '💕', label: 'Lãng mạn'   },
  { key: 'melancholic', emoji: '🌙', label: 'Hoài niệm'  },
  { key: 'uplifting',   emoji: '🌟', label: 'Phấn khởi'  },
  { key: 'angry',       emoji: '🔥', label: 'Mạnh mẽ'    },
]

/**
 * Modal lưu bài nhạc AI vào thư viện.
 *
 * Props:
 *   track      — { audioUrl, prompt, duration, genre, mood, title, lyrics }
 *   onClose    — fn() đóng modal
 *   onSaved    — fn(savedSong) callback khi lưu thành công
 */
export default function SaveSongModal({ track, onClose, onSaved }) {
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [])
  const [title, setTitle]           = useState(track?.title || '')
  const [genre, setGenre]           = useState(track?.genre || 'other')
  const [mood, setMood]             = useState(track?.mood || '')
  const [isPublished, setPublished] = useState(true)
  const [saving, setSaving]         = useState(false)
  const [saved, setSaved]           = useState(false)
  const titleInputRef = useRef()

  const handleSave = async () => {
    if (!title.trim()) {
      titleInputRef.current?.focus()
      toast.error('Vui lòng nhập tên bài hát')
      return
    }
    if (!track?.audioUrl) {
      toast.error('Không có file audio')
      return
    }

    setSaving(true)
    try {
      const targetUrl = track.audio_url || track.audioUrl || track.serverAudioUrl || ''
      const fd = new FormData()
      fd.append('title',        title.trim())
      fd.append('genre',        genre)
      fd.append('mood',         mood)
      fd.append('duration',     track.duration || 0)
      fd.append('lyrics',       track.lyrics || '')
      fd.append('description',  `🤖 Sonavia AI Studio\nPrompt: ${track.prompt || ''}`)
      fd.append('is_published', isPublished ? 'true' : 'false')
      if (track?.cover_image_url) {
        fd.append('cover_image_url', track.cover_image_url)
      }

      if (targetUrl.startsWith('/media/') || targetUrl.startsWith('http')) {
        fd.append('audio_url', targetUrl)
      } else if (targetUrl) {
        try {
          const response = await fetch(targetUrl)
          const blob = await response.blob()
          const isMp3 = blob.type?.includes('mpeg') || blob.type?.includes('mp3') || track?.engine?.includes('Sonavia') || track?.engine === 'ACE-Step'
          const ext = isMp3 ? 'mp3' : 'wav'
          const audioFile = new File([blob], `${title.trim()}.${ext}`, { type: isMp3 ? 'audio/mpeg' : 'audio/wav' })
          fd.append('audio_file', audioFile)
        } catch (e) {
          fd.append('audio_url', targetUrl)
        }
      }

      const { data } = await api.post('/music/songs/save-ai/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 60000,
      })

      setSaved(true)
      toast.success(`✅ Đã lưu "${title.trim()}" vào thư viện!`)
      onSaved?.(data)

      // Đóng modal sau 1.5s
      setTimeout(() => onClose(), 1500)
    } catch (err) {
      const msg = err.response?.data?.error
        || err.response?.data?.detail
        || 'Lỗi khi lưu bài hát'
      toast.error(msg)
    }
    setSaving(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') onClose()
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSave()
  }

  const moodInfo = MOODS.find(m => m.key === mood)

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(12px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}
      onKeyDown={handleKeyDown}>

      <div
        className="w-full max-w-md animate-scale-in overflow-hidden rounded-3xl shadow-2xl"
        style={{
          background: 'rgba(10,10,24,0.98)',
          border: '1px solid rgba(99,102,241,0.25)',
          boxShadow: '0 24px 80px rgba(0,0,0,0.6), 0 0 0 1px rgba(99,102,241,0.1)',
        }}>

        {/* ── Header ── */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              {saved
                ? <FiCheck size={16} className="text-white" />
                : <FiSave size={16} className="text-white" />
              }
            </div>
            <div>
              <h2 className="text-base font-black text-white leading-none">
                {saved ? 'Đã lưu!' : 'Lưu vào thư viện'}
              </h2>
              <p className="text-[10px] mt-0.5" style={{ color: 'rgba(165,180,252,0.45)' }}>
                {saved ? 'Bài hát đã có trong thư viện của bạn' : 'Đặt tên và lưu bài nhạc AI'}
              </p>
            </div>
          </div>
          <button onClick={onClose}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all"
            style={{ color: 'rgba(165,180,252,0.4)' }}
            onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; e.currentTarget.style.color = 'white' }}
            onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'rgba(165,180,252,0.4)' }}>
            <FiX size={16} />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">

          {/* ── Preview track ── */}
          <div className="flex items-center gap-3 p-3 rounded-2xl border border-white/[0.06]"
            style={{ background: 'rgba(99,102,241,0.07)' }}>
            <div className="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 overflow-hidden"
              style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.3), rgba(34,211,238,0.2))' }}>
              {track?.cover_image_url ? (
                <img src={track.cover_image_url} alt="Cover" className="w-full h-full object-cover" />
              ) : (
                <MdGraphicEq size={22} className="text-indigo-300" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-white truncate">
                {title || 'Chưa có tên...'}
              </p>
              <p className="text-[10px] truncate mt-0.5" style={{ color: 'rgba(165,180,252,0.4)' }}>
                {track?.prompt ? `"${track.prompt.slice(0, 60)}${track.prompt.length > 60 ? '...' : ''}"` : 'AI Generated'}
              </p>
            </div>
            <div className="text-[10px] shrink-0 px-2 py-1 rounded-full font-semibold"
              style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.25)' }}>
              {track?.duration ? `${track.duration}s` : 'AI'}
            </div>
          </div>

          {/* ── Tên bài hát ── */}
          <div>
            <label className="block text-xs font-semibold mb-2 uppercase tracking-wider"
              style={{ color: 'rgba(165,180,252,0.6)' }}>
              Tên bài hát *
            </label>
            <input
              ref={titleInputRef}
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="Nhập tên bài hát..."
              autoFocus
              maxLength={100}
              className="input-field text-sm font-medium"
              style={{
                background: 'rgba(255,255,255,0.06)',
                border: title.trim()
                  ? '1px solid rgba(99,102,241,0.5)'
                  : '1px solid rgba(255,255,255,0.09)',
              }}
            />
            <p className="text-[10px] mt-1 text-right" style={{ color: 'rgba(165,180,252,0.3)' }}>
              {title.length}/100 · ⌘↵ để lưu
            </p>
          </div>

          {/* ── Thể loại ── */}
          <div>
            <label className="block text-xs font-semibold mb-2 uppercase tracking-wider"
              style={{ color: 'rgba(165,180,252,0.6)' }}>
              Thể loại
            </label>
            <div className="flex flex-wrap gap-1.5">
              {GENRES.map(g => (
                <button key={g.key}
                  onClick={() => setGenre(g.key)}
                  className={clsx(
                    'px-2.5 py-1 rounded-full text-[11px] font-semibold border transition-all',
                    genre === g.key
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'border-white/[0.08] text-white/40 hover:text-white hover:border-white/20'
                  )}>
                  {g.label}
                </button>
              ))}
            </div>
          </div>

          {/* ── Tâm trạng ── */}
          <div>
            <label className="block text-xs font-semibold mb-2 uppercase tracking-wider"
              style={{ color: 'rgba(165,180,252,0.6)' }}>
              Tâm trạng
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {MOODS.map(m => (
                <button key={m.key}
                  onClick={() => setMood(prev => prev === m.key ? '' : m.key)}
                  className={clsx(
                    'flex flex-col items-center gap-0.5 py-2 rounded-xl border text-center transition-all',
                    mood === m.key
                      ? 'bg-indigo-500/20 border-indigo-500/40 scale-105'
                      : 'border-white/[0.06] hover:border-white/12'
                  )}>
                  <span className="text-sm leading-none">{m.emoji}</span>
                  <span className={clsx(
                    'text-[9px] font-semibold leading-none mt-0.5',
                    mood === m.key ? 'text-indigo-300' : 'text-white/40'
                  )}>{m.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* ── Công khai / Riêng tư ── */}
          <div className="flex items-center justify-between p-3.5 rounded-2xl border border-white/[0.06]"
            style={{ background: 'rgba(255,255,255,0.03)' }}>
            <div className="flex items-center gap-2.5">
              {isPublished
                ? <FiGlobe size={15} className="text-emerald-400 shrink-0" />
                : <FiLock size={15} className="text-white/40 shrink-0" />
              }
              <div>
                <p className="text-sm font-semibold text-white">
                  {isPublished ? 'Công khai' : 'Riêng tư'}
                </p>
                <p className="text-[10px]" style={{ color: 'rgba(165,180,252,0.35)' }}>
                  {isPublished ? 'Mọi người có thể nghe' : 'Chỉ mình bạn thấy'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setPublished(!isPublished)}
              className="w-11 h-6 rounded-full transition-all relative shrink-0"
              style={{ background: isPublished ? '#4f46e5' : 'rgba(255,255,255,0.12)' }}>
              <div
                className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all"
                style={{ left: isPublished ? '22px' : '2px' }}
              />
            </button>
          </div>
        </div>

        {/* ── Footer buttons ── */}
        <div className="px-6 pb-6 flex gap-3">
          <button onClick={onClose}
            className="flex-1 py-3 rounded-2xl text-sm font-semibold transition-all"
            style={{
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.09)',
              color: 'rgba(255,255,255,0.6)',
            }}
            onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.09)'}
            onMouseLeave={e => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}>
            Hủy
          </button>

          <button
            onClick={handleSave}
            disabled={saving || saved || !title.trim()}
            className="flex-2 flex-1 py-3 rounded-2xl text-sm font-black text-white transition-all flex items-center justify-center gap-2"
            style={{
              background: saved
                ? 'linear-gradient(135deg, #059669, #10b981)'
                : saving || !title.trim()
                  ? 'rgba(99,102,241,0.3)'
                  : 'linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #818cf8 100%)',
              boxShadow: (!saving && !saved && title.trim()) ? '0 6px 20px rgba(99,102,241,0.4)' : 'none',
              cursor: saving || saved ? 'not-allowed' : 'pointer',
            }}>
            {saved ? (
              <><FiCheck size={16} /> Đã lưu!</>
            ) : saving ? (
              <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Đang lưu...</>
            ) : (
              <><FiSave size={16} /> Lưu vào thư viện</>
            )}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
