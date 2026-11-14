import { useState, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { Link, useLocation } from 'react-router-dom'
import {
  FiPlay, FiPause, FiDownload, FiSave, FiX,
  FiRefreshCw, FiCheck, FiMic, FiZap, FiShare2,
  FiCopy, FiVolume2, FiTrash2, FiPlus, FiSliders,
  FiLayers, FiMusic, FiSend, FiExternalLink,
  FiImage, FiUploadCloud, FiEye, FiAlertCircle,
} from 'react-icons/fi'
import {
  MdGraphicEq, MdMusicNote, MdAutoAwesome,
  MdLyrics, MdTune, MdQueueMusic, MdCameraAlt,
  MdColorLens,
} from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import usePlayerStore from '../store/playerStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import SaveSongModal from '../components/music/SaveSongModal'
import { saveTrackAudioBlob, getTrackAudioBlob, deleteTrackAudioBlob } from '../utils/audioStorage'


// ─── Gợi ý prompt mẫu phong phú tiếng Việt ──────────────────────────────────
const PROMPT_EXAMPLES = [
  'Bài V-Pop ballad buồn về tình yêu trong mưa, giọng nữ da diết, tiếng piano và đàn dây sâu lắng',
  'Nhạc trẻ sôi động bùng nổ năng lượng tuổi thanh xuân, beat hiện đại, giọng nam mạnh mẽ',
  'Acoustic mộc mạc về nỗi nhớ quê hương, guitar gỗ ấm áp, giọng hát mộc truyền cảm',
  'Lo-fi chill học bài đêm khuya, tiếng mưa tí tách ngoài ô cửa sổ, giai điệu thư giãn',
  'R&B nhẹ nhàng quyến rũ, bass 808 trầm ấm, giọng nữ lãng mạn thì thầm',
  'K-Pop tươi vui ngọt ngào, điệp khúc bắt tai, synthesizer hiện đại, năng lượng tích cực',
  'Rock nhiệt huyết thôi thúc ước mơ, tiếng guitar điện overdrive và trống bốc lửa',
  'Pop Ballad hoài niệm về mối tình đầu thời áo trắng dưới mái trường xưa',
]

// ─── Tags phong cách nhanh ──────────────────────────────────────────────────
const STYLE_TAGS = [
  { label: 'V-Pop Ballad', prompt: 'Vietnamese pop ballad, emotional piano, strings' },
  { label: 'Acoustic Mộc', prompt: 'acoustic guitar, warm intimate vocals, folk' },
  { label: 'Lo-Fi Chill', prompt: 'lo-fi chill, relaxing beat, soft piano, mellow rain' },
  { label: 'R&B Soul', prompt: 'contemporary R&B, smooth groove, expressive vocals, 808 bass' },
  { label: 'Rap / Trap', prompt: 'Vietnamese hip-hop, trap beat, rhythmic flow, punchy 808' },
  { label: 'EDM Sôi động', prompt: 'EDM, energetic synth lead, build-up, heavy bass drop' },
  { label: 'K-Pop Vui tươi', prompt: 'K-Pop, catchy synth, upbeat modern beat, bright' },
  { label: 'Rock Mạnh mẽ', prompt: 'rock, electric guitar overdrive, driving drums' },
  { label: 'Buồn da diết', prompt: 'sad, melancholic, tearful emotion, slow tempo' },
  { label: 'Lãng mạn ngọt', prompt: 'romantic, sweet melody, tender, heartfelt' },
]

// ─── Tùy chọn ngôn ngữ bài hát & ca từ ──────────────────────────────────────
const LANGUAGE_OPTIONS = [
  { key: 'auto', flag: '🌐', label: 'Tự động',    note: 'AI nhận diện' },
  { key: 'vi',   flag: '🇻🇳', label: 'Tiếng Việt', note: 'V-Pop' },
  { key: 'ko',   flag: '🇰🇷', label: '한국어',      note: 'K-Pop' },
  { key: 'ja',   flag: '🇯🇵', label: '日本語',      note: 'J-Pop' },
  { key: 'zh',   flag: '🇨🇳', label: '中文',        note: 'C-Pop' },
  { key: 'en',   flag: '🇺🇸', label: 'English',     note: 'Pop / US-UK' },
]

// ─── Preset chất giọng ───────────────────────────────────────────────────────
const VOCAL_OPTIONS = [
  { key: 'female', label: 'Giọng Nữ', icon: '👩', desc: 'Trong trẻo, da diết' },
  { key: 'male', label: 'Giọng Nam', icon: '👨', desc: 'Trầm ấm, truyền cảm' },
  { key: 'duet', label: 'Song ca', icon: '👥', desc: 'Hòa quyện nam nữ' },
  { key: 'instrumental', label: 'Không lời', icon: '🎹', desc: 'Nhạc nền thuần túy' },
]

// ─── Lựa chọn thời lượng ────────────────────────────────────────────────────
const DURATION_OPTIONS = [
  { s: 30, label: '30s', note: 'Đoạn ngắn' },
  { s: 60, label: '1 phút', note: 'Đoạn vừa' },
  { s: 120, label: '2 phút', note: 'Bản rút gọn' },
  { s: 180, label: '3 phút', note: 'Bản tiêu chuẩn' },
  { s: 240, label: '4 phút', note: 'Bản đầy đủ' },
]

// ─── Modal xem lời bài hát (Suno style) ──────────────────────────────────────
function LyricsModal({ track, onClose }) {
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = prevOverflow
    }
  }, [])

  const copyLyrics = () => {
    navigator.clipboard.writeText(track.lyrics || '')
    setCopied(true)
    toast.success('Đã sao chép lời bài hát!')
    setTimeout(() => setCopied(false), 2000)
  }

  // Tách lời thành các block đẹp
  const lines = (track.lyrics || '').split('\n')

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(16px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="w-full max-w-lg max-h-[85vh] flex flex-col rounded-3xl overflow-hidden shadow-2xl animate-scale-in"
        style={{
          background: 'rgba(12,12,28,0.98)',
          border: '1px solid rgba(99,102,241,0.3)',
          boxShadow: '0 24px 80px rgba(0,0,0,0.7)',
        }}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              <MdLyrics size={20} className="text-white" />
            </div>
            <div>
              <h3 className="font-black text-white text-base leading-tight truncate max-w-xs">{track.title}</h3>
              <p className="text-xs text-white/40 mt-0.5">Lời bài hát đầy đủ · {track.engine}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={copyLyrics}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all text-white/60 hover:text-white"
              style={{ background: 'rgba(255,255,255,0.06)' }}>
              {copied ? <FiCheck size={13} className="text-emerald-400" /> : <FiCopy size={13} />}
              {copied ? 'Đã sao chép' : 'Sao chép'}
            </button>
            <button onClick={onClose}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-white/40 hover:text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.06)' }}>
              <FiX size={17} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-3 font-sans leading-relaxed">
          {lines.map((line, i) => {
            const isHeader = line.trim().startsWith('[') && line.trim().endsWith(']')
            if (isHeader) {
              return (
                <div key={i} className="pt-2">
                  <span className="inline-block text-[11px] font-black uppercase tracking-wider px-2.5 py-1 rounded-lg"
                    style={{ background: 'rgba(99,102,241,0.18)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)' }}>
                    {line.trim()}
                  </span>
                </div>
              )
            }
            if (!line.trim()) return <div key={i} className="h-2" />
            return (
              <p key={i} className="text-sm text-white/80 font-medium pl-1">
                {line}
              </p>
            )
          })}
        </div>
      </div>
    </div>,
    document.body
  )
}

// ─── Modal Đăng bài lên Bảng tin Cộng đồng ──────────────────────────────────
function SharePostModal({ track, onClose }) {
  const [content, setContent] = useState(`🎵 Vừa sáng tác bài hát mới với AI: "${track.title}"! Mọi người cùng nghe thử và góp ý nhé!`)
  const [posting, setPosting] = useState(false)
  const { user } = useAuthStore()

  const handlePost = async () => {
    if (!content.trim() || posting) return
    setPosting(true)
    try {
      // Trước tiên kiểm tra xem track đã có trong database chưa
      let songId = track.savedSongId

      // Nếu chưa lưu vào DB, tự động lưu trước
      if (!songId) {
        toast.loading('Đang chuẩn bị bài hát...', { id: 'posting-song' })
        const response = await fetch(track.audioUrl)
        const blob = await response.blob()
        const isMp3 = blob.type?.includes('mpeg') || track.engine === 'ACE-Step'
        const ext = isMp3 ? 'mp3' : 'wav'
        const audioFile = new File([blob], `${track.title}.${ext}`, { type: isMp3 ? 'audio/mpeg' : 'audio/wav' })

        const fd = new FormData()
        fd.append('title', track.title)
        fd.append('genre', track.genre || 'other')
        fd.append('mood', track.mood || '')
        fd.append('duration', track.duration || 0)
        fd.append('lyrics', track.lyrics || '')
        fd.append('description', `🤖 AI Song (${track.engine})\n${track.prompt || ''}`)
        fd.append('is_published', 'true')
        fd.append('audio_file', audioFile)
        if (track.cover_image_url) {
          fd.append('cover_image_url', track.cover_image_url)
        }

        const saveRes = await api.post('/music/songs/save-ai/', fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000,
        })
        songId = saveRes.data?.id
        track.savedSongId = songId
      }

      // Đăng bài viết lên /api/social/posts/
      await api.post('/social/posts/', {
        content: content.trim(),
        song_id: songId,
      })

      toast.dismiss('posting-song')
      toast.success('🎉 Đã chia sẻ bài hát lên bảng tin cộng đồng!')
      onClose()
    } catch (err) {
      toast.dismiss('posting-song')
      toast.error(err.response?.data?.error || 'Lỗi khi đăng bài')
    }
    setPosting(false)
  }

  return createPortal(
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(16px)' }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div className="w-full max-w-md rounded-3xl overflow-hidden shadow-2xl animate-scale-in"
        style={{
          background: 'rgba(12,12,28,0.98)',
          border: '1px solid rgba(99,102,241,0.3)',
        }}>
        <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <FiShare2 size={18} className="text-indigo-400" />
            <h3 className="font-black text-white text-base">Chia sẻ lên Bảng tin</h3>
          </div>
          <button onClick={onClose} className="text-white/40 hover:text-white">
            <FiX size={18} />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div className="flex items-center gap-3 p-3 rounded-2xl" style={{ background: 'rgba(255,255,255,0.04)' }}>
            <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              <MdGraphicEq size={22} className="text-white" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-black text-white truncate">{track.title}</p>
              <p className="text-xs text-white/40 truncate">{track.prompt}</p>
            </div>
          </div>

          <textarea
            value={content}
            onChange={e => setContent(e.target.value)}
            rows={4}
            placeholder="Viết cảm nghĩ hoặc lời giới thiệu bài hát..."
            className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-indigo-500 rounded-2xl p-4 text-sm text-white resize-none outline-none leading-relaxed"
          />

          <div className="flex gap-3 pt-2">
            <button onClick={onClose}
              className="flex-1 py-3 rounded-2xl text-sm font-semibold text-white/60 hover:text-white"
              style={{ background: 'rgba(255,255,255,0.05)' }}>
              Hủy
            </button>
            <button onClick={handlePost} disabled={posting || !content.trim()}
              className="flex-1 py-3 rounded-2xl text-sm font-black text-white flex items-center justify-center gap-2"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              {posting ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <FiSend size={15} />}
              {posting ? 'Đang chia sẻ...' : 'Đăng ngay'}
            </button>
          </div>
        </div>
      </div>
    </div>,
    document.body
  )
}

// ─── Track Card chuẩn phong cách Suno ────────────────────────────────────────
function SunoTrackCard({ track, onDelete, onSave, onRemix, onViewLyrics, onShare }) {
  const [playing, setPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)
  const { playSong } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()

  useEffect(() => {
    console.log("SONAVIA AUDIO DEBUG", {
      songId: track.id,
      title: track.title,
      audioUrl: track.audioUrl,
      audioType: track.engine,
      serverAudioUrl: track.serverAudioUrl,
    })
  }, [track.id, track.audioUrl])


  const handleAudioError = (e) => {
    setPlaying(false)
    const a = audioRef.current
    const errCode = a?.error?.code
    console.error('[Sonavia Audio Error]', {
      songId: track.id,
      audioUrl: a?.src || track.audio_url || track.audioUrl,
      error: a?.error ? { code: a.error.code, message: a.error.message } : e,
      networkState: a?.networkState,
      readyState: a?.readyState,
    })
    if (errCode === 4) {
      toast.error('Định dạng audio không được hỗ trợ.', { id: 'playback-error' })
    } else if (errCode === 2 || errCode === 3) {
      toast.error('Không thể tải audio.', { id: 'playback-error' })
    }
  }

  const toggle = async () => {
    const a = audioRef.current
    if (!a) return
    if (playing) {
      a.pause()
      setPlaying(false)
    } else {
      const targetUrl = track.audio_url || track.audioUrl || track.serverAudioUrl
      if (!targetUrl) {
        toast.error('Audio chưa sẵn sàng.', { id: 'playback-error' })
        return
      }

      // Đảm bảo a.src được gán URL hợp lệ
      if (!a.src || (!a.src.endsWith(targetUrl) && a.src !== targetUrl)) {
        a.src = targetUrl
      }

      try {
        await a.play()
        setPlaying(true)
      } catch (err) {
        console.warn('Playback error lần 1, đang tự động phục hồi nguồn phát:', err)

        // 1. Thử phục hồi bằng serverAudioUrl nếu hiện tại a.src đang dùng blob cũ
        if (track.serverAudioUrl && a.src !== track.serverAudioUrl) {
          try {
            track.audioUrl = track.serverAudioUrl
            a.src = track.serverAudioUrl
            await a.play()
            setPlaying(true)
            return
          } catch (srvErr) {
            console.warn('Server URL playback failed:', srvErr)
          }
        }

        // 2. Thử phục hồi từ IndexedDB (trường hợp blob URL cũ từ phiên trước bị hết hạn)
        try {
          const blob = await getTrackAudioBlob(track.id)
          if (blob && blob.size > 0) {
            const freshUrl = URL.createObjectURL(blob)
            track.audioUrl = freshUrl
            a.src = freshUrl
            await a.play()
            setPlaying(true)
            toast.success('Đã phục hồi file audio và đang phát!', { id: 'recovered-audio' })
            return
          }
        } catch (idbErr) {
          console.warn('IndexedDB recover failed:', idbErr)
        }

        // 3. Thử phục hồi trực tiếp từ server bằng seed
        if (track.seed) {
          try {
            const res = await api.get('/ai/acestep/recover/', { params: { seed: track.seed } })
            if (res.data?.found && res.data?.audio_url) {
              track.audio_url = res.data.audio_url
              track.audioUrl = res.data.audio_url
              track.serverAudioUrl = res.data.audio_url
              a.src = res.data.audio_url
              await a.play()
              setPlaying(true)
              toast.success('Đã tìm thấy bài hát trên server và đang phát!', { id: 'recovered-audio' })
              return
            }
          } catch (seedErr) {
            console.warn('Seed recover failed:', seedErr)
          }
        }

        setPlaying(false)
        if (a.error?.code === 4) {
          toast.error('Định dạng audio không được hỗ trợ.', { id: 'playback-error' })
        } else {
          toast.error('Không thể tải audio.', { id: 'playback-error' })
        }
      }
    }
  }



  // Phát trực tiếp vào global bottom player của Sonavia
  const handlePlayGlobal = () => {
    playSong({
      id: track.id,
      title: track.title,
      artist: { username: track.artistName || 'Sonavia AI' },
      audio_url: track.serverAudioUrl || track.audioUrl,
      audio_file_url: track.serverAudioUrl || track.audioUrl,
      duration: Math.round(track.duration || 30),
      genre: track.genre || 'vpop',
      lyrics: track.lyrics || '',
      cover_image_url: track.cover_image_url || track.coverImage || null,
      cover_image: track.cover_image_url || track.coverImage || null,
    })
    toast.success(`Đang phát: "${track.title}" ở thanh phát nhạc dưới`)
  }

  const download = async () => {
    const url = track.serverAudioUrl || track.audioUrl
    if (!url) {
      toast.error('Không tìm thấy tệp âm thanh!')
      return
    }
    const rawFmt = track.format || (url.toLowerCase().includes('.mp3') ? 'mp3' : (url.toLowerCase().includes('.wav') ? 'wav' : 'mp3'))
    const ext = rawFmt.replace('.', '').toLowerCase()
    const cleanTitle = (track.title || 'sonavia_song')
      .replace(/[^\w\s\u00C0-\u024F\u1EA0-\u1EF9-]/gi, '')
      .trim()
      .replace(/\s+/g, '_')
    const fileName = `${cleanTitle || 'sonavia_song'}.${ext}`

    try {
      const res = await fetch(url)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const blob = await res.blob()
      const blobUrl = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = fileName
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(blobUrl)
      toast.success(`Đã tải về file .${ext}!`)
    } catch {
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      toast.success(`Đã tải về file .${ext}!`)
    }
  }

  const fmt = (s) => {
    if (!s || isNaN(s)) return '0:00'
    return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
  }

  const GRADIENTS = [
    'from-indigo-600 via-purple-600 to-pink-600',
    'from-blue-600 via-cyan-500 to-teal-500',
    'from-violet-600 via-fuchsia-500 to-rose-500',
    'from-amber-500 via-orange-600 to-rose-600',
    'from-emerald-500 via-teal-600 to-cyan-600',
  ]
  const grad = GRADIENTS[(track.index || 0) % GRADIENTS.length]

  return (
    <div className={clsx(
      'rounded-3xl p-5 transition-all duration-300 group relative sonavia-glass glass-sheen',
      playing
        ? 'border-cyan-400/80 shadow-[0_16px_50px_rgba(0,0,0,0.7),0_0_35px_rgba(34,211,238,0.35)]'
        : 'border-white/10 hover:border-indigo-400/40 hover:shadow-[0_16px_40px_rgba(0,0,0,0.5),0_0_25px_rgba(99,102,241,0.2)]'
    )}>

      <div className="flex items-start gap-4">
        {/* Album Art với đĩa than Vinyl xoay tròn thật sự khi phát nhạc */}
        <div className="relative shrink-0 cursor-pointer group/art" onClick={toggle}>
          <div className={clsx(
            "w-20 h-20 rounded-full relative overflow-hidden transition-all duration-700 vinyl-ring flex items-center justify-center",
            playing
              ? "animate-spin-slow shadow-[0_0_28px_rgba(34,211,238,0.55)]"
              : "animate-spin-slow-paused hover:scale-105 shadow-lg"
          )}>
            {track.cover_image_url || track.coverImage ? (
              <img
                src={track.cover_image_url || track.coverImage}
                alt={track.title}
                className="w-full h-full object-cover rounded-full"
              />
            ) : (
              <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-xl rounded-full`}>
                🎵
              </div>
            )}

            {/* Lỗ tâm đĩa than */}
            <div className="vinyl-center-hole" />

            {/* Play/Pause overlay */}
            <div className="absolute inset-0 rounded-full bg-black/45 flex items-center justify-center opacity-0 group-hover/art:opacity-100 transition-opacity backdrop-blur-[2px] z-30">
              {playing ? <FiPause size={22} className="text-white drop-shadow-md" /> : <FiPlay size={22} className="text-white ml-0.5 drop-shadow-md" />}
            </div>
          </div>

          {/* Equalizer mini badge khi đang phát */}
          {playing && (
            <div className="absolute -bottom-1 -right-1 z-30 flex items-center justify-center bg-black/90 backdrop-blur-md border border-cyan-400/50 rounded-full px-2 py-0.5 shadow-lg">
              <div className="eq-bars scale-75">
                <div className="eq-bar" />
                <div className="eq-bar" />
                <div className="eq-bar" />
              </div>
            </div>
          )}

          {/* Badge biến thể (Variation 1 hoặc 2) */}
          {track.variation && (
            <span className="absolute -top-1 -right-1 text-[9px] font-black px-1.5 py-0.5 rounded-full shadow-md text-white z-30"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #06b6d4)' }}>
              #{track.variation}
            </span>
          )}
        </div>

        {/* Info & Badges */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <h3 className="text-base font-black text-white truncate group-hover:text-indigo-300 transition-colors">
              {track.title}
            </h3>
            <span className="text-[11px] text-white/30 shrink-0 tabular-nums">
              {fmt(duration || track.duration)}
            </span>
          </div>

          <p className="text-xs text-white/45 line-clamp-1 mb-2.5">
            {track.prompt || 'Không có mô tả'}
          </p>

          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
              style={{ background: 'rgba(99,102,241,0.18)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)' }}>
              🎵 {track.engine || 'Sonavia AI'}
            </span>


            {/* Language badge */}
            {track.language && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                style={{ background: 'rgba(234,179,8,0.15)', color: '#fde68a', border: '1px solid rgba(234,179,8,0.25)' }}>
                {track.language === 'vi' ? '🇻🇳 Việt' : track.language === 'ko' ? '🇰🇷 한국어' : track.language === 'ja' ? '🇯🇵 日本語' : track.language === 'zh' ? '🇨🇳 中文' : '🇺🇸 English'}
              </span>
            )}

            {track.withVocal ? (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
                style={{ background: 'rgba(34,211,238,0.12)', color: '#67e8f9', border: '1px solid rgba(34,211,238,0.25)' }}>
                {track.vocalGender === 'female' ? '👩 Giọng Nữ' : track.vocalGender === 'male' ? '👨 Giọng Nam' : track.vocalGender === 'duet' ? '👥 Song ca' : '🎤 Có giọng hát'}
              </span>
            ) : (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.4)' }}>
                🎹 Không lời
              </span>
            )}

            {/* Genre badge */}
            {track.genre && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-medium"
                style={{ background: 'rgba(16,185,129,0.12)', color: '#6ee7b7', border: '1px solid rgba(16,185,129,0.2)' }}>
                {track.genre}
              </span>
            )}

            {/* BPM + Key badge */}
            {track.bpm && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-mono font-medium"
                style={{ background: 'rgba(139,92,246,0.12)', color: '#c4b5fd', border: '1px solid rgba(139,92,246,0.2)' }}>
                ♩ {track.bpm} BPM {track.musicalKey ? `· ${track.musicalKey}` : ''}
              </span>
            )}

            {/* Atmosphere from image analysis */}
            {track.atmosphere && (
              <span className="text-[10px] px-2 py-0.5 rounded-full font-medium truncate max-w-[180px]"
                title={track.atmosphere}
                style={{ background: 'rgba(244,63,94,0.14)', color: '#fda4af', border: '1px solid rgba(244,63,94,0.25)' }}>
                🖼️ {track.atmosphere}
              </span>
            )}

            {track.seed && (
              <span className="text-[9px] text-white/20 tabular-nums font-mono">
                seed:{track.seed.slice(-4)}
              </span>
            )}
          </div>
        </div>
      </div>


      {/* Audio player hidden element */}
      <audio
        ref={audioRef}
        src={track.serverAudioUrl || track.audioUrl || undefined}
        preload="metadata"
        onPlay={() => setPlaying(true)}
        onPause={() => setPlaying(false)}
        onEnded={() => setPlaying(false)}
        onError={handleAudioError}
        onTimeUpdate={() => setCurrent(audioRef.current?.currentTime || 0)}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration || track.duration || 0)}
      />


      {/* Waveform Seeker bar */}
      <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center gap-3">
        <button
          onClick={toggle}
          className="w-9 h-9 rounded-full bg-white flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-[0_0_18px_rgba(255,255,255,0.6)] shrink-0 btn-shimmer">
          {playing
            ? <FiPause size={15} className="text-black fill-current" />
            : <FiPlay size={15} className="text-black ml-0.5 fill-current" />
          }
        </button>

        <span className="text-[10px] text-white/30 tabular-nums w-7 text-right shrink-0">{fmt(current)}</span>

        {/* Interactive progress track */}
        <div
          className="flex-1 h-2 rounded-full cursor-pointer relative group/track"
          style={{ background: 'rgba(255,255,255,0.08)' }}
          onClick={e => {
            const rect = e.currentTarget.getBoundingClientRect()
            const pct = (e.clientX - rect.left) / rect.width
            if (audioRef.current?.duration) audioRef.current.currentTime = pct * audioRef.current.duration
          }}>
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${duration ? (current / duration) * 100 : 0}%`,
              background: 'linear-gradient(to right, #6366f1, #22d3ee)',
            }}
          />
          <div
            className="absolute top-1/2 -translate-y-1/2 w-3.5 h-3.5 bg-white rounded-full shadow-lg opacity-0 group-hover/track:opacity-100 transition-opacity"
            style={{ left: `calc(${duration ? (current / duration) * 100 : 0}% - 7px)` }}
          />
        </div>

        <span className="text-[10px] text-white/30 tabular-nums w-7 shrink-0">{fmt(duration || track.duration)}</span>
      </div>

      {/* Action Buttons Toolbar (Suno-style) */}
      <div className="mt-3.5 flex items-center justify-between gap-1 flex-wrap">
        <div className="flex items-center gap-1.5">
          {/* Xem lời bài hát */}
          {track.lyrics && (
            <button onClick={() => onViewLyrics(track)}
              className="px-2.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all text-white/50 hover:text-white hover:bg-white/[0.08]"
              style={{ background: 'rgba(255,255,255,0.04)' }}
              title="Xem lời bài hát">
              <MdLyrics size={14} className="text-cyan-400" />
              <span>Xem lời</span>
            </button>
          )}

          {/* Nghe trên player chính */}
          <button onClick={handlePlayGlobal}
            className="px-2.5 py-1.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all text-white/50 hover:text-white hover:bg-white/[0.08]"
            style={{ background: 'rgba(255,255,255,0.04)' }}
            title="Phát ở thanh nghe nhạc dưới cùng">
            <FiVolume2 size={13} className="text-indigo-400" />
            <span>Phát toàn trang</span>
          </button>
        </div>

        <div className="flex items-center gap-1">
          {/* Tái sử dụng / Remix */}
          <button onClick={() => onRemix(track)}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all text-white/40 hover:text-white"
            style={{ background: 'rgba(255,255,255,0.04)' }}
            title="Nạp lại vào form để tạo biến thể mới">
            <FiRefreshCw size={13} />
          </button>

          {/* Đăng lên Bảng tin */}
          {isAuthenticated && (
            <button onClick={() => onShare(track)}
              className="w-8 h-8 rounded-xl flex items-center justify-center transition-all text-white/40 hover:text-cyan-300"
              style={{ background: 'rgba(255,255,255,0.04)' }}
              title="Chia sẻ lên Bảng tin cộng đồng">
              <FiShare2 size={13} />
            </button>
          )}

          {/* Tải về */}
          <button onClick={download}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all text-white/40 hover:text-white"
            style={{ background: 'rgba(255,255,255,0.04)' }}
            title="Tải audio về máy">
            <FiDownload size={13} />
          </button>

          {/* Lưu vào thư viện */}
          {isAuthenticated && (
            <button onClick={() => onSave(track)}
              className="w-8 h-8 rounded-xl flex items-center justify-center transition-all text-white/40 hover:text-indigo-300"
              style={{ background: 'rgba(255,255,255,0.04)' }}
              title="Lưu vào Thư viện cá nhân">
              <FiSave size={13} />
            </button>
          )}

          {/* Xóa */}
          <button onClick={() => onDelete(track.id)}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all text-white/20 hover:text-rose-400"
            style={{ background: 'rgba(255,255,255,0.04)' }}
            title="Xóa bài này">
            <FiTrash2 size={13} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Animation khi đang sáng tác (Loading Card) ──────────────────────────────
function SunoGeneratingCard({ prompt, duration = 30, variationNumber = 1, engine = 'acestep' }) {
  const STEPS = [
    '🧠 Phân tích ngữ nghĩa & cấu trúc bài hát...',
    '✍️ Tự động sáng tác ca từ đa ngôn ngữ...',
    '🎼 Phối khí, hòa âm & tổng hợp giai điệu...',
    '🎤 Thu âm ca sĩ AI & trau chuốt giọng hát...',
    '🎚️ Hoàn tất mastering & xuất audio 320kbps...',
  ]
  const [step, setStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const t1 = setInterval(() => setStep(s => (s + 1) % STEPS.length), 3500)
    const t2 = setInterval(() => setElapsed(e => e + 1), 1000)
    return () => { clearInterval(t1); clearInterval(t2) }
  }, [])

  return (
    <div className="rounded-3xl p-6 relative overflow-hidden animate-pulse-subtle"
      style={{
        background: 'linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(34,211,238,0.05) 100%)',
        border: '1px solid rgba(99,102,241,0.3)',
      }}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
            <MdGraphicEq size={18} className="text-white animate-spin" style={{ animationDuration: '3s' }} />
          </div>
          <div>
            <p className="text-sm font-black text-white flex items-center gap-2">
              Đang sáng tác Bản #{variationNumber}...
              <span className="text-[10px] text-cyan-300 font-mono">({elapsed}s)</span>
            </p>
            <p className="text-xs text-white/50">{STEPS[step]}</p>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold"
          style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc' }}>
          Sonavia Studio AI
        </span>
      </div>


      {prompt && (
        <p className="text-xs text-white/40 italic line-clamp-1 mb-4">
          "{prompt}"
        </p>
      )}

      {/* Sóng âm thanh động */}
      <div className="flex items-center justify-center gap-1.5 py-3">
        {[40, 75, 55, 95, 60, 85, 45, 100, 70, 50, 80, 60, 90, 45].map((h, i) => (
          <div
            key={i}
            className="w-1.5 rounded-full bg-gradient-to-t from-indigo-500 to-cyan-400 animate-pulse"
            style={{
              height: `${h * 0.35}px`,
              animationDuration: `${0.6 + (i % 5) * 0.2}s`,
              animationDelay: `${i * 0.08}s`,
            }}
          />
        ))}
      </div>
      <p className="text-center text-[10px] text-white/30 mt-2">
        Thời lượng: {duration >= 60 ? `${Math.floor(duration / 60)} phút${duration % 60 ? ` ${duration % 60}s` : ''}` : `${duration}s`} · Dự kiến hoàn tất trong {duration >= 180 ? '1-2.5 phút' : duration >= 60 ? '45-90s' : '20-40s'}
      </p>
    </div>
  )
}

// ─── MAIN CreatePage ──────────────────────────────────────────────────────────
export default function CreatePage() {
  const { user, isAuthenticated } = useAuthStore()
  const location = useLocation()

  // Chế độ: 'simple' (Đơn giản) | 'custom' (Tùy chỉnh chi tiết như Suno)
  const [mode, setMode] = useState('simple')

  // Simple Mode State - nhận prompt truyền từ HomePage Composer nếu có
  const [simplePrompt, setSimplePrompt] = useState(location.state?.prompt || '')
  const [simpleInstrumental, setSimpleInstrumental] = useState(false)
  const [simpleLanguage, setSimpleLanguage] = useState('auto') // 'auto'|'vi'|'ko'|'ja'|'zh'|'en'
  const [simpleVocal, setSimpleVocal] = useState('auto')       // 'auto'|'female'|'male'|'duet'|'instrumental'

  // Image-to-Music Mode State (Sáng tác nhạc từ hình ảnh)
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(location.state?.imagePreview || null)
  const [imageAnalyzing, setImageAnalyzing] = useState(false)
  const [imageAnalysis, setImageAnalysis] = useState(location.state?.imageAnalysis || null)
  const [imagePrompt, setImagePrompt] = useState(location.state?.imageAnalysis?.prompt || '')
  const [imageTitle, setImageTitle] = useState(location.state?.imageAnalysis?.title || '')
  const [imageLyrics, setImageLyrics] = useState(location.state?.imageAnalysis?.lyrics || '')
  const [imageVocal, setImageVocal] = useState(location.state?.imageAnalysis?.vocal || 'female')
  const [imageLanguage, setImageLanguage] = useState('auto')
  const [imageInstrumental, setImageInstrumental] = useState(false)
  const [serverCoverImageUrl, setServerCoverImageUrl] = useState(location.state?.serverCoverImageUrl || location.state?.imageAnalysis?.cover_image_url || '')
  const [useImageAsCover, setUseImageAsCover] = useState(true)
  const [isDragOver, setIsDragOver] = useState(false)
  const [showLyricsEditor, setShowLyricsEditor] = useState(false)
  const fileInputRef = useRef(null)

  useEffect(() => {
    if (location.state?.mode) {
      setMode(location.state.mode)
    }
    if (location.state?.prompt) {
      setSimplePrompt(location.state.prompt)
    }
    if (location.state?.imageAnalysis) {
      const a = location.state.imageAnalysis
      setImageAnalysis(a)
      if (a.prompt) setImagePrompt(a.prompt)
      if (a.title) setImageTitle(a.title)
      if (a.lyrics) setImageLyrics(a.lyrics)
      if (a.vocal) setImageVocal(a.vocal)
      if (a.cover_image_url) setServerCoverImageUrl(a.cover_image_url)
    }
    if (location.state?.imagePreview) {
      setImagePreview(location.state.imagePreview)
    }
    if (location.state?.serverCoverImageUrl) {
      setServerCoverImageUrl(location.state.serverCoverImageUrl)
    }
  }, [location.state])


  // Custom Mode State
  const [customLyrics, setCustomLyrics] = useState('')
  const [customStyle, setCustomStyle] = useState('Vietnamese pop ballad, emotional piano, strings')
  const [customTitle, setCustomTitle] = useState('')
  const [vocalGender, setVocalGender] = useState('female') // 'female', 'male', 'duet', 'instrumental'
  const [customLanguage, setCustomLanguage] = useState('auto') // 'auto'|'vi'|'ko'|'ja'|'zh'|'en'

  // AI Lyrics Generator Modal
  const [showAiLyricsModal, setShowAiLyricsModal] = useState(false)
  const [aiTopic, setAiTopic] = useState('')
  const [aiLyricsLanguage, setAiLyricsLanguage] = useState('auto')
  const [aiLyricsLoading, setAiLyricsLoading] = useState(false)
  const [enhancingPrompt, setEnhancingPrompt] = useState(false)

  // Cấu hình chung
  const [engine, setEngine] = useState('acestep') // 'acestep' (Cloud có giọng hát) | 'musicgen' (Local GPU)
  const [duration, setDuration] = useState(180) // Mặc định 3 phút (chuẩn bài hát)
  const [variationCount, setVariationCount] = useState(1) // 1 hoặc 2 biến thể (mặc định 1 để tối ưu GPU)

  // Quản lý kho bài hát riêng biệt cho từng tài khoản (Account-isolated Studio Library)
  const userStorageKey = user?.id ? ('sonavia_created_tracks_u_' + user.id) : 'sonavia_created_tracks_guest'

  const [isGenerating, setIsGenerating] = useState(false)
  const [generatingSeeds, setGeneratingSeeds] = useState([])
  const [tracks, setTracks] = useState(() => {
    try {
      // Dọn dẹp key dùng chung cũ để các tài khoản không bị trùng lặp bài hát
      localStorage.removeItem('sonavia_created_tracks')
      localStorage.removeItem('museai_created_tracks')
      const saved = localStorage.getItem(userStorageKey)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  // Modals
  const [saveModalTrack, setSaveModalTrack] = useState(null)
  const [lyricsModalTrack, setLyricsModalTrack] = useState(null)
  const [shareModalTrack, setShareModalTrack] = useState(null)

  const textareaRef = useRef(null)
  const trackIdCounter = useRef(Date.now())
  const activeKeyRef = useRef(userStorageKey)
  const loadedKeyRef = useRef(userStorageKey)

  // Tải lại thư viện riêng biệt khi tài khoản đăng nhập thay đổi
  useEffect(() => {
    activeKeyRef.current = userStorageKey
    try {
      localStorage.removeItem('sonavia_created_tracks')
      localStorage.removeItem('museai_created_tracks')
      const saved = localStorage.getItem(userStorageKey)
      const userTracks = saved ? JSON.parse(saved) : []
      setTracks(userTracks)
      loadedKeyRef.current = userStorageKey

      // Nếu tài khoản đã đăng nhập và chưa có track local nào, đồng bộ các bài đã lưu từ tài khoản trên server
      if (user?.username && userTracks.length === 0) {
        api.get('/music/songs/?artist__username=' + encodeURIComponent(user.username))
          .then(res => {
            const list = res.data?.results || res.data || []
            if (list.length > 0 && activeKeyRef.current === userStorageKey) {
              const mapped = list.map(s => ({
                id: s.id,
                title: s.title,
                prompt: s.description || s.tags || '',
                lyrics: s.lyrics,
                duration: s.duration || 180,
                audioUrl: s.audio_file_url || s.audio_url || s.audioUrl,
                audio_url: s.audio_file_url || s.audio_url || s.audioUrl,
                serverAudioUrl: s.audio_file_url || s.audio_url || s.audioUrl,
                cover_image_url: s.cover_image_url,
                coverImage: s.cover_image_url,
                genre: s.genre,
                mood: s.mood,
                engine: 'Sonavia AI',
                savedSongId: s.id,
                createdAt: s.created_at,
              }))
              setTracks(mapped)
              try {
                localStorage.setItem(userStorageKey, JSON.stringify(mapped))
              } catch {}
            }
          })
          .catch(() => {})
      }
    } catch {
      setTracks([])
      loadedKeyRef.current = userStorageKey
    }
  }, [userStorageKey, user?.username])

  // Lưu tracks riêng biệt theo đúng storageKey của tài khoản đang đăng nhập (chỉ lưu khi đã nạp đúng key)
  useEffect(() => {
    if (!userStorageKey || loadedKeyRef.current !== userStorageKey) return
    try {
      localStorage.setItem(userStorageKey, JSON.stringify(tracks))
    } catch { }
  }, [tracks, userStorageKey])

  // Khôi phục URL audio khi mở lại trang / web (vì blob: URL bị trình duyệt vô hiệu hóa khi reload)
  useEffect(() => {
    let isCancelled = false

    async function restoreAudioUrls() {
      if (!tracks || tracks.length === 0) return

      let hasChanges = false
      const updatedTracks = await Promise.all(
        tracks.map(async (track) => {
          const isBlobUrl = track.audioUrl?.startsWith('blob:')
          if (!isBlobUrl && track.audioUrl) return track

          // 1. Thử khôi phục từ IndexedDB của trình duyệt trước
          try {
            const blob = await getTrackAudioBlob(track.id)
            if (blob && blob.size > 0) {
              const freshUrl = URL.createObjectURL(blob)
              hasChanges = true
              return { ...track, audioUrl: freshUrl }
            }
          } catch (e) {
            console.warn('Lỗi đọc IndexedDB:', e)
          }

          // 2. Dùng serverAudioUrl nếu IndexedDB không có
          if (track.serverAudioUrl) {
            hasChanges = true
            return { ...track, audioUrl: track.serverAudioUrl }
          }

          // 3. Thử tìm lại file từ server bằng seed
          if (track.seed) {
            try {
              const res = await api.get('/ai/acestep/recover/', { params: { seed: track.seed } })
              if (res.data?.found && res.data?.audio_url) {
                hasChanges = true
                return {
                  ...track,
                  audioUrl: res.data.audio_url,
                  serverAudioUrl: res.data.audio_url,
                }
              }
            } catch (e) { }
          }

          return track
        })
      )

      if (!isCancelled && hasChanges) {
        setTracks(updatedTracks)
      }
    }

    restoreAudioUrls()

    return () => {
      isCancelled = true
    }
  }, [userStorageKey])

  // Kiểm tra backend engine status
  useEffect(() => {
    api.get('/ai/acestep/status/').catch(() => { })
    api.get('/ai/generate/status/').catch(() => { })
  }, [])

  // Chèn tag cấu trúc vào lyrics
  const insertLyricTag = (tag) => {
    setCustomLyrics(prev => {
      const sep = prev.trim() ? '\n\n' : ''
      return prev + sep + tag + '\n'
    })
  }

  // Thêm nhanh tag phong cách
  const addStyleTag = (tag) => {
    if (mode === 'simple') {
      const sep = simplePrompt.trim() ? ', ' : ''
      setSimplePrompt(p => (p.trim() + sep + tag.prompt).trim())
    } else {
      const sep = customStyle.trim() ? ', ' : ''
      setCustomStyle(p => (p.trim() + sep + tag.label).trim())
    }
  }

  // Tối ưu hóa prompt bằng Gemini AI (Magic Prompt)
  const handleEnhancePrompt = async (target = 'simple') => {
    const rawText = target === 'simple' ? simplePrompt.trim() : customStyle.trim()
    if (!rawText) {
      toast.error('Vui lòng nhập vài từ mô tả ý tưởng trước khi bấm tối ưu!')
      return
    }
    if (enhancingPrompt) return

    setEnhancingPrompt(true)
    try {
      const activeLanguage = target === 'simple' ? simpleLanguage : (mode === 'image' ? imageLanguage : customLanguage)
      const res = await api.post('/ai/prompt/enhance/', {
        prompt: rawText,
        language: activeLanguage,
      }, { timeout: 45000 })

      if (res.data && res.data.enhanced_prompt) {
        if (target === 'simple') {
          setSimplePrompt(res.data.enhanced_prompt)
        } else {
          setCustomStyle(res.data.style_tags || res.data.enhanced_prompt)
          if (res.data.suggested_title && !customTitle.trim()) {
            setCustomTitle(res.data.suggested_title)
          }
        }
        toast.success('✨ Đã tối ưu hóa mô tả thông minh!')
      } else {
        toast.error('Không thể tối ưu hóa mô tả lúc này.')
      }
    } catch (err) {
      console.error('[MagicPrompt] Lỗi tối ưu hóa:', err)
      toast.error('Lỗi khi tối ưu hóa prompt bằng AI.')
    } finally {
      setEnhancingPrompt(false)
    }
  }

  // Gợi ý ngẫu nhiên
  const handleRandomPrompt = () => {
    const p = PROMPT_EXAMPLES[Math.floor(Math.random() * PROMPT_EXAMPLES.length)]
    if (mode === 'simple') {
      setSimplePrompt(p)
    } else {
      setCustomStyle(p)
    }
  }

  // Gọi AI viết lời bài hát tự động
  const handleGenerateAiLyrics = async () => {
    const topic = aiTopic.trim()
    if (!topic) {
      toast.error('Vui lòng nhập chủ đề hoặc câu chuyện bạn muốn kể!')
      return
    }
    if (aiLyricsLoading) return

    setAiLyricsLoading(true)
    const t0 = Date.now()
    try {
      const chosenLyricLang = aiLyricsLanguage !== 'auto' ? aiLyricsLanguage : (customLanguage !== 'auto' ? customLanguage : (mode === 'simple' ? simpleLanguage : 'auto'))
      const res = await api.post('/ai/lyrics/generate/', {
        topic,
        genre: customStyle ? 'auto' : 'vpop',
        vocal_gender: vocalGender,
        language: chosenLyricLang,
      }, { timeout: 30000 })

      if (res.data && res.data.lyrics) {
        setCustomLyrics(res.data.lyrics)
        if (!customTitle.trim() && res.data.title) {
          setCustomTitle(res.data.title)
        }
        if (res.data.style_tags) {
          setCustomStyle(res.data.style_tags)
        }
        if (res.data.language && res.data.language !== 'auto') {
          setCustomLanguage(res.data.language)
        } else if (chosenLyricLang !== 'auto') {
          setCustomLanguage(chosenLyricLang)
        }
        setShowAiLyricsModal(false)
        setAiTopic('')
        toast.success(`✨ Đã sinh lời bài hát: "${res.data.title}"!`)
      } else {
        toast.error('Phản hồi AI không hợp lệ hoặc thiếu nội dung lời.')
      }
    } catch (err) {
      const status = err.response?.status
      const errMsg = err.response?.data?.error
      const elapsed = ((Date.now() - t0) / 1000).toFixed(2)

      console.error('[SmartLyrics] Lỗi sinh lời bài hát:', {
        endpoint: '/api/ai/lyrics/generate/',
        status,
        code: err.code,
        elapsed: `${elapsed}s`,
        message: err.message,
      })

      if (status === 400) {
        toast.error(errMsg || 'Dữ liệu nhập chưa hợp lệ.')
      } else if (status === 401) {
        toast.error('Phiên đăng nhập đã hết hạn. Vui lòng thử lại.')
      } else if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        toast.error('Yêu cầu xử lý quá thời gian. Vui lòng thử lại.')
      } else if (!err.response) {
        toast.error('Không thể kết nối máy chủ. Vui lòng kiểm tra mạng.')
      } else if (status >= 500) {
        toast.error(errMsg || 'Dịch vụ AI tạm thời không khả dụng. Vui lòng thử lại sau.')
      } else {
        toast.error(errMsg || 'Lỗi khi sinh lời bài hát. Thử lại sau.')
      }
    } finally {
      setAiLyricsLoading(false)
    }
  }

  // Tự động đặt tên bài hát
  const handleAutoTitle = () => {
    const text = mode === 'simple' ? simplePrompt : (customLyrics || customStyle)
    if (!text.trim()) {
      setCustomTitle('Bản Tình Ca Mùa Hạ')
      return
    }
    const words = text.replace(/\[.*?\]/g, '').trim().split(/\s+/).slice(0, 4).join(' ')
    const title = words.charAt(0).toUpperCase() + words.slice(1)
    setCustomTitle(title || 'Giai Điệu AI')
    toast.success('Đã đặt tên bài hát!')
  }

  // Tái sử dụng track (Remix / Nạp lại form)
  const handleRemix = (t) => {
    if (t.atmosphere || t.cover_image_url) {
      setMode('image')
      setImagePrompt(t.prompt || '')
      setImageTitle((t.title || '') + ' (Remix)')
      setImageLyrics(t.lyrics || '')
      if (t.cover_image_url) {
        setImagePreview(t.cover_image_url)
        setServerCoverImageUrl(t.cover_image_url)
      }
    } else if (t.lyrics) {
      setMode('custom')
      setCustomLyrics(t.lyrics)
      setCustomTitle(t.title + ' (Remix)')
      setCustomStyle(t.prompt)
    } else {
      setMode('simple')
      setSimplePrompt(t.prompt)
    }
    toast.success('Đã nạp lại thông số bài hát vào bảng điều khiển!')
  }

  // Phân tích hình ảnh thành âm nhạc (Image-to-Music Analyzer)
  const handleImageFileSelect = async (file) => {
    if (!file) return
    if (!file.type.startsWith('image/')) {
      toast.error('Vui lòng chọn file hình ảnh hợp lệ (JPG, PNG, WebP)')
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      toast.error('Dung lượng ảnh tối đa 20MB')
      return
    }

    const previewUrl = URL.createObjectURL(file)
    setImagePreview(previewUrl)
    setImageFile(file)
    setImageAnalyzing(true)

    const getBase64 = (f) => new Promise((resolve) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result)
      reader.onerror = () => resolve(null)
      reader.readAsDataURL(f)
    })

    try {
      toast.loading('AI đang phân tích cảm xúc & ánh sáng bức ảnh...', { id: 'analyzing-img' })
      let res = null

      const fd = new FormData()
      fd.append('image', file)
      if (imageLanguage && imageLanguage !== 'auto') {
        fd.append('language', imageLanguage)
      }

      try {
        res = await api.post('/ai/analyze-image/', fd, {
          timeout: 60000,
        })
      } catch (uploadErr) {
        console.warn('FormData upload error, attempting Base64 fallback...', uploadErr)
        const base64Data = await getBase64(file)
        if (base64Data) {
          res = await api.post('/ai/analyze-image/', {
            image_base64: base64Data,
            language: imageLanguage,
          }, { timeout: 60000 })
        } else {
          throw uploadErr
        }
      }

      if (res && res.data && res.data.success) {
        setImageAnalysis(res.data)
        setServerCoverImageUrl(res.data.cover_image_url || '')
        if (res.data.title) setImageTitle(res.data.title)
        if (res.data.prompt) setImagePrompt(res.data.prompt)
        if (res.data.lyrics) setImageLyrics(res.data.lyrics)
        if (res.data.vocal) setImageVocal(res.data.vocal)
        if (res.data.language && imageLanguage === 'auto') setImageLanguage(res.data.language)
        toast.dismiss('analyzing-img')
        toast.success(`✨ Đã cảm nhận xong: "${res.data.atmosphere || res.data.title}"!`)
      } else {
        toast.dismiss('analyzing-img')
        toast.error(res?.data?.error || 'Không thể phân tích ảnh. Vui lòng thử lại.')
      }
    } catch (err) {
      toast.dismiss('analyzing-img')
      console.error('Image analysis error:', err)
      const errorMsg =
        err.response?.data?.error ||
        err.response?.data?.detail ||
        err.response?.data?.message ||
        (err.code === 'ECONNABORTED' ? 'Quá thời gian chờ AI phân tích ảnh, vui lòng thử lại.' : 'Lỗi khi phân tích hình ảnh')
      toast.error(errorMsg)
    } finally {
      setImageAnalyzing(false)
    }
  }

  // Chọn bối cảnh thị giác mẫu
  const handleSelectPresetScene = async (sceneKey) => {
    setImageAnalyzing(true)
    try {
      toast.loading('Đang cảm nhận không gian và hòa âm...', { id: 'preset-analyzing' })
      const res = await api.post('/ai/analyze-image/', {
        preset_scene: sceneKey,
        language: imageLanguage,
      }, { timeout: 30000 })
      if (res.data && res.data.success) {
        setImageAnalysis(res.data)
        setServerCoverImageUrl(res.data.cover_image_url || '')
        setImagePreview(res.data.cover_image_url || '')
        if (res.data.title) setImageTitle(res.data.title)
        if (res.data.prompt) setImagePrompt(res.data.prompt)
        if (res.data.lyrics) setImageLyrics(res.data.lyrics)
        if (res.data.vocal) setImageVocal(res.data.vocal)
        if (res.data.language && imageLanguage === 'auto') setImageLanguage(res.data.language)
        toast.dismiss('preset-analyzing')
        toast.success(`✨ Đã nạp bối cảnh: "${res.data.atmosphere || res.data.title}"!`)
      }
    } catch (err) {
      toast.dismiss('preset-analyzing')
      toast.error('Lỗi khi nạp bối cảnh mẫu')
    } finally {
      setImageAnalyzing(false)
    }
  }

  // Gỡ ảnh
  const handleClearImage = () => {
    setImageFile(null)
    setImagePreview(null)
    setImageAnalysis(null)
    setImagePrompt('')
    setImageTitle('')
    setImageLyrics('')
    setServerCoverImageUrl('')
    if (fileInputRef.current) fileInputRef.current.value = ''
    toast.success('Đã gỡ ảnh!')
  }

  // Đổi ngôn ngữ trong chế độ Ảnh - tự động cập nhật lại ca từ và tiêu đề
  const handleImageLanguageChange = async (newLang) => {
    setImageLanguage(newLang)
    if (!imageLyrics && !imageAnalysis) return

    if (newLang !== 'auto') {
      const langName = newLang === 'ko' ? 'Tiếng Hàn' : newLang === 'ja' ? 'Tiếng Nhật' : newLang === 'zh' ? 'Tiếng Trung' : newLang === 'en' ? 'Tiếng Anh' : 'Tiếng Việt'
      try {
        toast.loading(`Đang sáng tác lời bài hát theo ảnh (${langName})...`, { id: 'lang-lyrics-change' })
        const res = await api.post('/ai/lyrics/generate/', {
          topic: imagePrompt || imageAnalysis?.prompt || 'Melodic atmospheric song',
          language: newLang,
          vocal_gender: imageVocal,
        })
        if (res.data?.lyrics) {
          setImageLyrics(res.data.lyrics)
          if (res.data.title) {
            setImageTitle(res.data.title)
          }
          toast.success(`✨ Đã đổi lời bài hát sang ${langName}!`, { id: 'lang-lyrics-change' })
        } else {
          toast.dismiss('lang-lyrics-change')
        }
      } catch (err) {
        console.warn('Lỗi sinh lời theo ngôn ngữ:', err)
        toast.dismiss('lang-lyrics-change')
      }
    }
  }

  // ─── HÀM TẠO BÀI HÁT CHÍNH (Sáng tác & Hát như Suno) ────────────────────────
  const handleCreate = async () => {
    if (isGenerating) return

    // Chuẩn bị thông số theo chế độ
    let promptToSend = ''
    let lyricsToSend = ''
    let isInstru = false
    let finalTitle = ''

    if (mode === 'simple') {
      if (!simplePrompt.trim()) {
        toast.error('Vui lòng nhập mô tả bài hát bạn muốn tạo!')
        return
      }
      promptToSend = simplePrompt.trim()
      isInstru = simpleInstrumental
      finalTitle = simplePrompt.split(',')[0].slice(0, 30).trim() || 'AI Song'
    } else if (mode === 'image') {
      if (!imageAnalysis && !imagePrompt.trim()) {
        toast.error('Vui lòng tải ảnh lên hoặc chọn bối cảnh mẫu để AI sáng tác!')
        return
      }
      promptToSend = (imagePrompt || imageAnalysis?.prompt || 'Melodic atmospheric song').trim()
      lyricsToSend = imageInstrumental ? '' : (imageLyrics || imageAnalysis?.lyrics || '').trim()
      isInstru = imageInstrumental
      finalTitle = (imageTitle || imageAnalysis?.title || 'Khúc Ca Từ Bức Ảnh').trim()

      // Kiểm tra xung đột ngôn ngữ: Nếu người dùng chọn tiếng Hàn/Nhật/Trung/Anh nhưng lyricsToSend lại là tiếng Việt (do ảnh tự sinh lúc đầu):
      const chosenLang = imageLanguage
      const hasVietnamese = /[áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ]/i.test(lyricsToSend)
      const hasHangul = /[\uac00-\ud7af]/.test(lyricsToSend)
      const hasKana = /[\u3040-\u30ff]/.test(lyricsToSend)
      const hasHanzi = /[\u4e00-\u9fff]/.test(lyricsToSend)

      if (chosenLang === 'ko' && hasVietnamese && !hasHangul) {
        lyricsToSend = '' // Để backend orchestrator tự động sinh ca từ tiếng Hàn chuẩn
      } else if (chosenLang === 'ja' && hasVietnamese && !hasKana) {
        lyricsToSend = '' // Để backend orchestrator tự động sinh ca từ tiếng Nhật chuẩn
      } else if (chosenLang === 'zh' && hasVietnamese && !hasHanzi) {
        lyricsToSend = '' // Để backend orchestrator tự động sinh ca từ tiếng Trung chuẩn
      } else if (chosenLang === 'en' && hasVietnamese) {
        lyricsToSend = '' // Để backend orchestrator tự động sinh ca từ tiếng Anh chuẩn
      }
    } else {
      // Custom mode
      if (!customLyrics.trim() && vocalGender !== 'instrumental') {
        toast.error('Vui lòng nhập lời bài hát hoặc bấm "AI Viết lời"')
        return
      }
      lyricsToSend = vocalGender === 'instrumental' ? '' : customLyrics.trim()
      promptToSend = customStyle.trim() || 'Vietnamese pop, melodic, studio recording'
      isInstru = vocalGender === 'instrumental'
      finalTitle = customTitle.trim() || 'AI Song'
    }

    setIsGenerating(true)
    const count = variationCount // 1 hoặc 2 bản
    setGeneratingSeeds(Array.from({ length: count }, (_, i) => i + 1))

    // Helper tạo 1 bản nhạc
    const generateSingleTrack = async (varIndex) => {
      try {
        const seedVal = String(Math.floor(100000000 + Math.random() * 900000000))
        const chosenLang = mode === 'simple' ? simpleLanguage : (mode === 'image' ? imageLanguage : customLanguage)
        let activeLang = chosenLang
        if (!activeLang || activeLang === 'auto') {
          const sampleText = `${lyricsToSend} ${promptToSend}`
          if (/[áàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵđĐ]/i.test(sampleText)) {
            activeLang = 'vi'
          } else if (/[\uac00-\ud7af]/.test(sampleText)) {
            activeLang = 'ko'
          } else if (/[\u3040-\u30ff]/.test(sampleText)) {
            activeLang = 'ja'
          } else if (/[\u4e00-\u9fff]/.test(sampleText)) {
            activeLang = 'zh'
          } else {
            activeLang = 'auto'
          }
        }
        const activeVocal = isInstru ? 'instrumental' : (mode === 'simple' ? simpleVocal : (mode === 'image' ? imageVocal : vocalGender))
        const activeCoverUrl = useImageAsCover ? (serverCoverImageUrl || undefined) : undefined

        // ── Sonavia Unified AI Music Generator: POST /api/music/generate/ (JSON contract) ──
        const res = await api.post('/music/generate/', {
          prompt: promptToSend,
          language: activeLang,
          vocal: activeVocal,
          custom_lyrics: !isInstru ? lyricsToSend : '',
          duration: duration,
          seed: seedVal,
          instrumental: isInstru,
          cover_image_url: activeCoverUrl,
          preferred_provider: engine === 'musicgen' ? 'musicgen' : undefined,
          guidance_scale: 14.5,
          infer_steps: 60,
        }, { timeout: 480000 })

        if (!res.data || res.data.success === false) {
          const errMsg = res.data?.error?.message || 'Không thể tạo bài hát vào lúc này'
          throw new Error(errMsg)
        }

        const song = res.data.song || res.data
        const audioUrl = song.audio_url || song.audioUrl
        if (!audioUrl) {
          throw new Error('Dữ liệu phản hồi không chứa đường dẫn âm thanh hợp lệ.')
        }

        const songTitle   = song.title || finalTitle
        const songLang    = song.language || activeLang
        const songGenre   = song.genre || imageAnalysis?.genre_name || ''
        const songMood    = song.mood || imageAnalysis?.mood_name || ''
        const songBpm     = song.bpm || imageAnalysis?.bpm || ''
        const songKey     = song.key || song.musical_key || imageAnalysis?.key || ''
        const songVocal   = song.vocal || (isInstru ? 'instrumental' : activeVocal)
        const songTheme   = song.theme || ''
        const resolvedLyrics = song.lyrics || (isInstru ? null : lyricsToSend)
        const resolvedCover = song.cover_image_url || (useImageAsCover ? (serverCoverImageUrl || imagePreview) : null)

        const displayTitle = count > 1 ? `${songTitle} (Bản #${varIndex})` : songTitle
        trackIdCounter.current += 1
        const trackId = song.id || (Date.now() + varIndex)

        const newTrack = {
          id: trackId,
          index: trackIdCounter.current,
          variation: count > 1 ? varIndex : null,
          title: displayTitle,
          prompt: promptToSend,
          lyrics: resolvedLyrics,
          duration: song.duration || duration,
          audioUrl: audioUrl,
          audio_url: audioUrl,
          serverAudioUrl: audioUrl,
          cover_image_url: resolvedCover,
          coverImage: resolvedCover,
          atmosphere: imageAnalysis?.atmosphere || '',
          visualTags: imageAnalysis?.visual_tags || [],
          palette: imageAnalysis?.palette || [],
          withVocal: !isInstru && (!!resolvedLyrics || mode === 'simple' || mode === 'image'),
          vocalGender: songVocal,
          engine: song.provider === 'musicgen' ? 'MusicGen GPU' : (song.provider === 'acestep' ? 'ACE-Step Studio' : 'Sonavia AI'),
          seed: song.seed || seedVal,
          format: song.format || (audioUrl?.toLowerCase().includes('.wav') ? 'wav' : 'mp3'),

          // Metadata phong phú từ Smart Generate
          language: songLang,
          genre: songGenre,
          mood: songMood,
          bpm: songBpm,
          musicalKey: songKey,
          theme: songTheme,
          createdAt: new Date(),
        }

        if (song.provider === 'musicgen') {
          toast('💡 Bài nhạc được tạo bởi Meta MusicGen Local GPU (Melodic Lead). Hệ thống tự động ghép nối mượt mà theo đúng thời lượng bạn chọn.', {
            icon: 'ℹ️',
            duration: 6000,
          })
        }

        return newTrack
      } catch (err) {
        console.error('Track generation failed:', err)
        throw err
      }
    }


    try {
      if (count === 1) {
        const track = await generateSingleTrack(1)
        setTracks(prev => [track, ...prev])
        toast.success(`🎵 Đã sáng tác xong "${track.title}"!`)
      } else {
        // Tạo tuần tự để không bị quá tải ZeroGPU / GPU
        toast.loading('Đang khởi tạo bản phối #1...', { id: 'generating-dual' })
        const track1 = await generateSingleTrack(1)
        setTracks(prev => [track1, ...prev])
        toast.loading('Bản #1 hoàn tất! Đang khởi tạo bản phối #2...', { id: 'generating-dual' })

        try {
          const track2 = await generateSingleTrack(2)
          setTracks(prev => [track2, ...prev])
          toast.dismiss('generating-dual')
          toast.success(`✨ Đã sáng tác xong cả 2 bản phối!`)
        } catch (err2) {
          toast.dismiss('generating-dual')
          toast.success(`🎵 Đã tạo thành công bản phối #1! (Bản #2 tạm gián đoạn)`)
        }
      }
    } catch (err) {
      toast.dismiss('generating-dual')
      let errMsg = 'Không thể tạo bản nhạc vào lúc này. Vui lòng thử lại sau.'
      if (err.response?.data?.error?.message) {
        errMsg = err.response.data.error.message
      } else if (err.response?.data?.message) {
        errMsg = err.response.data.message
      } else if (err.response?.data?.detail) {
        errMsg = err.response.data.detail
      } else if (err.response?.data?.error && typeof err.response.data.error === 'string') {
        errMsg = err.response.data.error
      } else if (err.message && !err.message.includes('status code 500')) {
        errMsg = err.message
      } else if (err.message && err.message.includes('status code 500')) {
        errMsg = 'Máy chủ AI đang điều phối tài nguyên, vui lòng bấm Tạo lại sau vài giây.'
      }
      toast.error(errMsg, { duration: 6500 })
    }

    setIsGenerating(false)
    setGeneratingSeeds([])
  }

  return (
    <div className="min-h-screen text-white bg-transparent relative">
      {/* ── Outer 2-Column Studio Layout (Suno AI Style) ── */}
      <div className="max-w-[1500px] mx-auto px-4 lg:px-8 py-6">

        {/* Studio Title Bar */}
        <div className="flex items-center justify-between pb-6 mb-6 border-b border-white/[0.06]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center shadow-lg"
              style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #6366f1 60%, #818cf8 100%)' }}>
              <MdGraphicEq size={22} className="text-white" />
            </div>
            <div>
              <h1 className="text-xl font-black tracking-tight text-white flex items-center gap-2">
                Sonavia Studio
                <span className="text-[10px] px-2 py-0.5 rounded-full font-black uppercase"
                  style={{ background: 'rgba(34,211,238,0.15)', color: '#67e8f9', border: '1px solid rgba(34,211,238,0.3)' }}>
                  Next-Gen AI
                </span>
              </h1>
              <p className="text-xs text-white/40">Sáng tác & cất giọng hát chân thật cùng AI Sonavia</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-white/40 flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/[0.08]"
              style={{ background: 'rgba(255,255,255,0.03)' }}>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Sonavia Studio AI Sẵn Sàng
            </span>

          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

          {/* ═══════════════════════════════════════════════════════════════════ */}
          {/* ── CỘT TRÁI: BẢNG ĐIỀU KHIỂN SÁNG TÁC (CREATOR STUDIO) ─────────── */}
          {/* ═══════════════════════════════════════════════════════════════════ */}
          <div className="lg:col-span-5 space-y-5">

            {/* Mode Switcher: Simple vs Image-to-Music vs Custom */}
            <div className="flex p-1.5 rounded-2xl border border-white/10 shadow-lg backdrop-blur-2xl"
              style={{ background: 'rgba(12, 14, 32, 0.75)' }}>
              <button
                type="button"
                onClick={() => setMode('simple')}
                className={clsx(
                  'flex-1 py-2.5 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5',
                  mode === 'simple'
                    ? 'text-white shadow-[0_0_20px_rgba(99,102,241,0.5)]'
                    : 'text-white/40 hover:text-white/80'
                )}
                style={mode === 'simple' ? { background: 'linear-gradient(135deg, #4f46e5, #6366f1)' } : {}}>
                <FiZap size={14} className={mode === 'simple' ? 'text-amber-300' : ''} />
                Đơn giản
              </button>
              <button
                type="button"
                onClick={() => setMode('image')}
                className={clsx(
                  'flex-1 py-2.5 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5 relative',
                  mode === 'image'
                    ? 'text-white shadow-[0_0_20px_rgba(6,182,212,0.5)]'
                    : 'text-white/40 hover:text-white/80'
                )}
                style={mode === 'image' ? { background: 'linear-gradient(135deg, #0891b2, #06b6d4)' } : {}}>
                <FiImage size={14} className={mode === 'image' ? 'text-cyan-200' : ''} />
                <span>Từ hình ảnh</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded font-black bg-cyan-400 text-black leading-tight ml-0.5 animate-pulse shadow-sm">
                  AI
                </span>
              </button>
              <button
                type="button"
                onClick={() => setMode('custom')}
                className={clsx(
                  'flex-1 py-2.5 rounded-xl text-xs font-black transition-all flex items-center justify-center gap-1.5',
                  mode === 'custom'
                    ? 'text-white shadow-[0_0_20px_rgba(124,58,237,0.5)]'
                    : 'text-white/40 hover:text-white/80'
                )}
                style={mode === 'custom' ? { background: 'linear-gradient(135deg, #7c3aed, #22d3ee)' } : {}}>
                <MdTune size={15} className={mode === 'custom' ? 'text-indigo-200' : ''} />
                Tùy chỉnh
              </button>
            </div>

            {/* ── GIAO DIỆN CHẾ ĐỘ ĐƠN GIẢN (SIMPLE MODE) ── */}
            {mode === 'simple' && (
              <div className="rounded-3xl p-5 sm:p-6 border border-white/10 space-y-4 sonavia-glass shadow-[0_16px_45px_rgba(0,0,0,0.5),0_0_30px_rgba(99,102,241,0.12)]">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-black uppercase tracking-wider text-white/70">
                      Mô tả bài hát muốn tạo
                    </label>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => handleEnhancePrompt('simple')}
                        disabled={enhancingPrompt || !simplePrompt.trim()}
                        className={clsx(
                          'text-[11px] font-bold px-2.5 py-1 rounded-xl flex items-center gap-1.5 transition-all shadow-sm border btn-shimmer',
                          enhancingPrompt
                            ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
                            : 'bg-gradient-to-r from-cyan-500/15 to-indigo-500/15 border-cyan-500/30 text-cyan-300 hover:text-white hover:border-cyan-400/60 hover:bg-cyan-500/25 active:scale-95 disabled:opacity-30 disabled:pointer-events-none'
                        )}
                        title="Tối ưu hóa mô tả ngắn thành phong cách âm nhạc chuyên sâu"
                      >
                        <MdAutoAwesome size={13} className={clsx(enhancingPrompt ? 'animate-spin text-cyan-300' : 'text-cyan-400')} />
                        {enhancingPrompt ? 'Đang tối ưu...' : '✨ Tối ưu thông minh'}
                      </button>

                      <button
                        type="button"
                        onClick={handleRandomPrompt}
                        className="text-[11px] font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
                        <MdAutoAwesome size={13} /> Thử ngẫu nhiên
                      </button>
                    </div>
                  </div>
                  <textarea
                    ref={textareaRef}
                    value={simplePrompt}
                    onChange={e => {
                      const val = e.target.value
                      setSimplePrompt(val)
                      const vLower = val.toLowerCase()
                      if (vLower.includes('giọng nam') || vLower.includes('nam hát') || vLower.includes('nam ca sĩ') || vLower.includes('male voice') || vLower.includes('male vocal')) {
                        setVocalGender('male')
                      } else if (vLower.includes('giọng nữ') || vLower.includes('nữ hát') || vLower.includes('nữ ca sĩ') || vLower.includes('female voice')) {
                        setVocalGender('female')
                      }
                    }}
                    onKeyDown={e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleCreate() }}
                    placeholder="Ví dụ: Bài V-Pop ballad buồn về tình yêu trong mưa, giọng nam trầm ấm, piano và guitar mộc mạc..."
                    rows={4}
                    className="w-full bg-black/40 border border-white/10 focus:border-cyan-400 focus:shadow-[0_0_25px_rgba(34,211,238,0.25)] rounded-2xl p-4 text-sm text-white resize-none outline-none leading-relaxed placeholder-white/25 transition-all duration-300"
                  />
                </div>

                {/* Chọn giọng hát nhanh cho Simple Mode */}
                {!simpleInstrumental && (
                  <div>
                    <label className="block text-xs font-bold text-white/70 mb-2">
                      Chất giọng ca sĩ:
                    </label>
                    <div className="grid grid-cols-4 gap-2">
                      {[
                        { key: 'auto',   label: '✨ Tự động', desc: 'AI chọn phù hợp' },
                        { key: 'female', label: '👩 Giọng Nữ', desc: 'Trong trẻo' },
                        { key: 'male',   label: '👨 Giọng Nam', desc: 'Trầm ấm' },
                        { key: 'duet',   label: '👥 Song ca',   desc: 'Nam & Nữ' },
                      ].map(v => (
                        <button
                          key={v.key}
                          type="button"
                          onClick={() => setSimpleVocal(v.key)}
                          className={clsx(
                            'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                            simpleVocal === v.key
                              ? 'bg-gradient-to-b from-indigo-500/30 to-cyan-500/20 border-cyan-400 text-white shadow-[0_0_16px_rgba(34,211,238,0.4)] scale-[1.02]'
                              : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                          )}>
                          <span className="text-[11px] font-bold">{v.label}</span>
                          <span className="text-[9px] text-white/40">{v.desc}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Language Selector — 5 ngôn ngữ + AUTO */}
                <div>
                  <label className="block text-xs font-bold text-white/70 mb-2">
                    Ngôn ngữ bài hát:
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {LANGUAGE_OPTIONS.map(l => (
                      <button
                        key={l.key}
                        type="button"
                        onClick={() => setSimpleLanguage(l.key)}
                        className={clsx(
                          'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                          simpleLanguage === l.key
                            ? 'bg-gradient-to-b from-cyan-500/30 to-indigo-500/20 border-cyan-400 text-white shadow-[0_0_16px_rgba(34,211,238,0.4)] scale-[1.02]'
                            : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                        )}>
                        <span className="text-base leading-tight">{l.flag}</span>
                        <span className="text-[10px] font-bold">{l.label}</span>
                        <span className="text-[9px] text-white/35">{l.note}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Instrumental toggle */}
                <div className="flex items-center justify-between py-2 border-t border-white/[0.05]">
                  <div>
                    <span className="text-xs font-bold text-white">Nhạc không lời (Instrumental)</span>
                    <p className="text-[10px] text-white/30">Chỉ tạo giai điệu nhạc nền, không có giọng hát</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSimpleInstrumental(!simpleInstrumental)}
                    className="w-11 h-6 rounded-full transition-all relative shrink-0"
                    style={{ background: simpleInstrumental ? '#4f46e5' : 'rgba(255,255,255,0.12)' }}>
                    <div
                      className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all"
                      style={{ left: simpleInstrumental ? '22px' : '2px' }}
                    />
                  </button>
                </div>
              </div>
            )}

            {/* ── GIAO DIỆN SÁNG TÁC TỪ HÌNH ẢNH (IMAGE-TO-MUSIC VISION AI) ── */}
            {mode === 'image' && (
              <div className="rounded-3xl p-5 sm:p-6 border border-white/10 space-y-4 sonavia-glass shadow-[0_16px_45px_rgba(0,0,0,0.5),0_0_30px_rgba(6,182,212,0.12)]">

                {/* Dropzone / Upload Box */}
                {!imagePreview ? (
                  <div
                    onDragOver={e => { e.preventDefault(); setIsDragOver(true) }}
                    onDragLeave={() => setIsDragOver(false)}
                    onDrop={e => {
                      e.preventDefault()
                      setIsDragOver(false)
                      if (e.dataTransfer.files?.[0]) handleImageFileSelect(e.dataTransfer.files[0])
                    }}
                    onClick={() => fileInputRef.current?.click()}
                    className={clsx(
                      'rounded-2xl p-6 border-2 border-dashed transition-all cursor-pointer flex flex-col items-center justify-center text-center relative group',
                      isDragOver
                        ? 'border-cyan-400 bg-cyan-500/10 shadow-[0_0_25px_rgba(34,211,238,0.25)]'
                        : 'border-cyan-500/30 hover:border-cyan-400/60 bg-white/[0.02] hover:bg-white/[0.04]'
                    )}>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={e => { if (e.target.files?.[0]) handleImageFileSelect(e.target.files[0]) }}
                    />
                    <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-3 shadow-lg group-hover:scale-110 transition-transform"
                      style={{ background: 'linear-gradient(135deg, #0891b2, #06b6d4)' }}>
                      <FiUploadCloud size={28} className="text-white" />
                    </div>
                    <p className="text-sm font-black text-white mb-1">
                      Kéo thả bức ảnh vào đây hoặc bấm để chọn ảnh
                    </p>
                    <p className="text-xs text-white/40 max-w-sm leading-relaxed mb-3">
                      Hỗ trợ JPG, PNG, WebP (tối đa 20MB). AI sẽ cảm nhận màu sắc, độ sáng, không gian & cảm xúc để sáng tác giai điệu độc bản.
                    </p>
                    <div className="flex items-center gap-2 flex-wrap justify-center">
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full text-cyan-300 border border-cyan-500/30 bg-cyan-500/10">
                        ✨ Phân tích ánh sáng & bảng màu
                      </span>
                      <span className="text-[10px] font-bold px-2.5 py-1 rounded-full text-indigo-300 border border-indigo-500/30 bg-indigo-500/10">
                        🎨 Tự động gắn ảnh bìa
                      </span>
                    </div>
                  </div>
                ) : (
                  /* Image Preview & Synesthesia Analysis Visualizer */
                  <div className="space-y-4">
                    <div className="relative rounded-2xl overflow-hidden border border-white/10 group shadow-xl"
                      style={{ background: 'rgba(0,0,0,0.4)' }}>
                      <div className="flex items-center justify-between p-3 border-b border-white/[0.08] bg-black/40 backdrop-blur-md">
                        <div className="flex items-center gap-2">
                          <FiImage size={15} className="text-cyan-400" />
                          <span className="text-xs font-black text-white">Ảnh nguồn cảm hứng</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {!imageAnalysis && !imageAnalyzing && imageFile && (
                            <button
                              type="button"
                              onClick={() => handleImageFileSelect(imageFile)}
                              className="text-[11px] font-bold text-cyan-400 hover:text-cyan-300 px-2 py-1 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 transition-all"
                              title="Phân tích lại bức ảnh">
                              Phân tích lại
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-[11px] font-bold text-white/60 hover:text-white px-2 py-1 rounded-lg bg-white/[0.05] hover:bg-white/[0.1] transition-all">
                            Đổi ảnh khác
                          </button>
                          <button
                            type="button"
                            onClick={handleClearImage}
                            className="text-[11px] font-bold text-rose-400 hover:text-rose-300 p-1 rounded-lg hover:bg-rose-500/10 transition-all"
                            title="Xóa ảnh">
                            <FiTrash2 size={13} />
                          </button>
                        </div>
                      </div>

                      <div className="relative h-48 sm:h-56 w-full overflow-hidden flex items-center justify-center bg-black/60">
                        <img
                          src={imagePreview}
                          alt="Inspiration Source"
                          className={clsx(
                            'w-full h-full object-cover transition-all duration-700',
                            imageAnalyzing ? 'blur-sm scale-105' : 'group-hover:scale-105'
                          )}
                        />

                        {/* Animated Laser Scanning Beam when analyzing */}
                        {imageAnalyzing && (
                          <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/65 backdrop-blur-[3px] z-10">
                            <div className="w-full absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-pulse" />
                            <div className="w-10 h-10 border-3 border-cyan-400 border-t-transparent rounded-full animate-spin mb-3" />
                            <p className="text-xs font-black text-white">AI đang cảm nhận bức ảnh...</p>
                            <p className="text-[10px] text-cyan-300/70 mt-1">Trích xuất màu sắc, tâm trạng & cấu trúc hợp âm</p>
                          </div>
                        )}
                      </div>

                      {/* Palette & Atmosphere Bar */}
                      {imageAnalysis && (
                        <div className="p-3.5 bg-black/50 backdrop-blur-md space-y-2.5">
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <div className="flex items-center gap-2 flex-wrap mb-1">
                                <p className="text-xs font-black text-white flex items-center gap-1.5">
                                  <MdAutoAwesome size={14} className="text-amber-400 shrink-0" />
                                  <span>{imageAnalysis.atmosphere || 'Bối cảnh nghệ thuật'}</span>
                                </p>
                              </div>
                              {imageAnalysis.visual_tags?.length > 0 && (
                                <div className="flex flex-wrap gap-1 mt-1.5">
                                  {imageAnalysis.visual_tags.map(t => (
                                    <span key={t} className="text-[9px] font-semibold px-2 py-0.5 rounded-md bg-white/[0.08] text-white/70">
                                      {t}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Color Palette Dots */}
                            {imageAnalysis.palette?.length > 0 && (
                              <div className="flex items-center gap-1.5 shrink-0 bg-white/[0.05] p-1.5 rounded-xl border border-white/[0.08]">
                                {imageAnalysis.palette.map((hex, i) => (
                                  <div
                                    key={i}
                                    className="w-4 h-4 rounded-full border border-white/20 shadow-sm transition-transform hover:scale-125"
                                    style={{ backgroundColor: hex }}
                                    title={`Mã màu: ${hex}`}
                                  />
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/jpeg,image/png,image/webp"
                      className="hidden"
                      onChange={e => { if (e.target.files?.[0]) handleImageFileSelect(e.target.files[0]) }}
                    />

                    {/* Detected Musical Parameters Grid */}
                    {imageAnalysis && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                          <p className="text-[10px] text-white/40 font-bold uppercase">Thể loại</p>
                          <p className="text-xs font-black text-cyan-300 mt-0.5">{imageAnalysis.genre_name || imageAnalysis.genre || 'V-Pop'}</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                          <p className="text-[10px] text-white/40 font-bold uppercase">Tâm trạng</p>
                          <p className="text-xs font-black text-indigo-300 mt-0.5">{imageAnalysis.mood_name || imageAnalysis.mood || 'Lãng mạn'}</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                          <p className="text-[10px] text-white/40 font-bold uppercase">Nhịp điệu</p>
                          <p className="text-xs font-black text-emerald-300 mt-0.5">{imageAnalysis.bpm || 80} BPM</p>
                        </div>
                        <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-center">
                          <p className="text-[10px] text-white/40 font-bold uppercase">Điệu thức</p>
                          <p className="text-xs font-black text-amber-300 mt-0.5">{imageAnalysis.key || 'G Major'}</p>
                        </div>
                      </div>
                    )}

                    {/* Title Input */}
                    <div>
                      <label className="text-xs font-black uppercase tracking-wider text-white/70 block mb-1.5">
                        Tên bài hát AI gợi ý cho ảnh:
                      </label>
                      <input
                        type="text"
                        value={imageTitle}
                        onChange={e => setImageTitle(e.target.value)}
                        placeholder="Nhập tên bài hát..."
                        className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-cyan-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                      />
                    </div>

                    {/* AI Musical Prompt */}
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-black uppercase tracking-wider text-white/70">
                          Mô tả phong cách âm nhạc tạo từ ảnh:
                        </label>
                        <span className="text-[10px] text-white/30 font-medium">Có thể tùy chỉnh theo ý bạn</span>
                      </div>
                      <textarea
                        value={imagePrompt}
                        onChange={e => setImagePrompt(e.target.value)}
                        rows={3}
                        className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-cyan-500 rounded-2xl p-3.5 text-xs text-white resize-none outline-none leading-relaxed"
                        placeholder="Mô tả giai điệu kết hợp cùng hình ảnh..."
                      />
                    </div>

                    {/* Vocalist Selection for Image Mode */}
                    {!imageInstrumental && (
                      <div>
                        <label className="block text-xs font-bold text-white/70 mb-2">
                          Chất giọng ca sĩ:
                        </label>
                        <div className="grid grid-cols-4 gap-2">
                          {[
                            { key: 'female', label: '👩 Giọng Nữ', desc: 'Trong trẻo' },
                            { key: 'male',   label: '👨 Giọng Nam', desc: 'Trầm ấm' },
                            { key: 'duet',   label: '👥 Song ca',   desc: 'Nam & Nữ' },
                            { key: 'instrumental', label: '🎹 Không lời', desc: 'Nhạc nền' },
                          ].map(v => (
                            <button
                              key={v.key}
                              type="button"
                              onClick={() => {
                                if (v.key === 'instrumental') {
                                  setImageInstrumental(true)
                                } else {
                                  setImageInstrumental(false)
                                  setImageVocal(v.key)
                                }
                              }}
                              className={clsx(
                                'p-2 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                                (imageInstrumental && v.key === 'instrumental') || (!imageInstrumental && imageVocal === v.key)
                                  ? 'bg-cyan-600/30 border-cyan-400 text-white shadow-md'
                                  : 'bg-white/[0.03] border-white/[0.08] text-white/60 hover:text-white hover:bg-white/[0.06]'
                              )}>
                              <span className="text-[11px] font-bold">{v.label}</span>
                              <span className="text-[9px] text-white/40">{v.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Ngôn ngữ bài hát khi đã có ảnh */}
                    <div>
                      <label className="block text-xs font-bold text-white/70 mb-2">
                        Ngôn ngữ bài hát:
                      </label>
                      <div className="grid grid-cols-3 gap-2">
                        {LANGUAGE_OPTIONS.map(l => (
                          <button
                            key={l.key}
                            type="button"
                            onClick={() => handleImageLanguageChange(l.key)}
                            className={clsx(
                              'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                              imageLanguage === l.key
                                ? 'bg-gradient-to-b from-cyan-500/30 to-indigo-500/20 border-cyan-400 text-white shadow-[0_0_16px_rgba(34,211,238,0.4)] scale-[1.02]'
                                : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                            )}>
                            <span className="text-base leading-tight">{l.flag}</span>
                            <span className="text-[10px] font-bold">{l.label}</span>
                            <span className="text-[9px] text-white/35">{l.note}</span>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Collapsible Lyrics Editor */}
                    {!imageInstrumental && (
                      <div className="rounded-2xl border border-white/[0.08] overflow-hidden bg-white/[0.015]">
                        <button
                          type="button"
                          onClick={() => setShowLyricsEditor(!showLyricsEditor)}
                          className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-white/[0.03] transition-colors">
                          <div className="flex items-center gap-2">
                            <MdLyrics size={16} className="text-cyan-400" />
                            <span className="text-xs font-bold text-white">
                              Lời bài hát sáng tác theo ảnh {imageLyrics ? `(${imageLyrics.split('\n').filter(Boolean).length} dòng)` : ''}
                            </span>
                          </div>
                          <span className="text-[11px] font-semibold text-cyan-400">
                            {showLyricsEditor ? 'Thu gọn ▲' : 'Xem & Chỉnh sửa ▼'}
                          </span>
                        </button>
                        {showLyricsEditor && (
                          <div className="p-3.5 border-t border-white/[0.06] space-y-2">
                            <textarea
                              value={imageLyrics}
                              onChange={e => setImageLyrics(e.target.value)}
                              rows={6}
                              placeholder="Nhập hoặc chỉnh sửa lời bài hát..."
                              className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-cyan-500 rounded-xl p-3 text-xs font-sans text-white/90 resize-none outline-none leading-relaxed"
                            />
                          </div>
                        )}
                      </div>
                    )}

                    {/* Toggle: Use Image as Album Cover Art */}
                    <div className="flex items-center justify-between py-2 px-1 border-t border-white/[0.06]">
                      <div className="flex items-center gap-2.5">
                        <MdColorLens size={18} className="text-cyan-400 shrink-0" />
                        <div>
                          <span className="text-xs font-bold text-white">Dùng ảnh này làm bìa bài hát (Cover Art)</span>
                          <p className="text-[10px] text-white/40">Ảnh sẽ hiển thị trên đĩa phát nhạc & thư viện cá nhân</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setUseImageAsCover(!useImageAsCover)}
                        className="w-11 h-6 rounded-full transition-all relative shrink-0"
                        style={{ background: useImageAsCover ? '#06b6d4' : 'rgba(255,255,255,0.12)' }}>
                        <div
                          className="absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-all"
                          style={{ left: useImageAsCover ? '22px' : '2px' }}
                        />
                      </button>
                    </div>
                  </div>
                )}

                {/* Preset Scene Inspiration Buttons & Pre-upload Settings */}
                {!imagePreview && (
                  <div className="space-y-4">
                    <div>
                      <p className="text-[11px] text-white/35 font-bold uppercase tracking-wider mb-2">
                        Hoặc trải nghiệm ngay bối cảnh thị giác mẫu:
                      </p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {[
                          { key: 'golden_sunset_romantic', label: '🌅 Hoàng hôn lãng mạn', note: 'V-Pop Ballad' },
                          { key: 'neon_cyber_night',       label: '🌃 Cyberpunk đêm neon',  note: 'Synthwave / EDM' },
                          { key: 'rainy_melancholic_room',  label: '🌧️ Chiều mưa hoài niệm', note: 'Lo-fi chill' },
                          { key: 'ocean_blue_sky_freedom', label: '🌊 Biển xanh tự do',     note: 'Tropical Pop' },
                          { key: 'nature_forest_peaceful', label: '🌲 Rừng thông bình yên', note: 'Acoustic Folk' },
                        ].map(scene => (
                          <button
                            key={scene.key}
                            type="button"
                            onClick={() => handleSelectPresetScene(scene.key)}
                            className="p-2.5 rounded-xl border border-white/[0.08] hover:border-cyan-400/50 bg-white/[0.02] hover:bg-cyan-500/10 text-left transition-all group">
                            <p className="text-xs font-bold text-white/80 group-hover:text-cyan-300">{scene.label}</p>
                            <p className="text-[10px] text-white/35">{scene.note}</p>
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Cấu hình Chất giọng & Ngôn ngữ trước khi tạo theo ảnh */}
                    <div className="space-y-3.5 pt-3 border-t border-white/[0.06]">
                      {/* Chất giọng ca sĩ */}
                      <div>
                        <label className="block text-xs font-bold text-white/70 mb-2">
                          Chất giọng ca sĩ:
                        </label>
                        <div className="grid grid-cols-4 gap-2">
                          {[
                            { key: 'female', label: '👩 Giọng Nữ', desc: 'Trong trẻo' },
                            { key: 'male',   label: '👨 Giọng Nam', desc: 'Trầm ấm' },
                            { key: 'duet',   label: '👥 Song ca',   desc: 'Nam & Nữ' },
                            { key: 'instrumental', label: '🎹 Không lời', desc: 'Nhạc nền' },
                          ].map(v => (
                            <button
                              key={v.key}
                              type="button"
                              onClick={() => {
                                if (v.key === 'instrumental') {
                                  setImageInstrumental(true)
                                } else {
                                  setImageInstrumental(false)
                                  setImageVocal(v.key)
                                }
                              }}
                              className={clsx(
                                'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                                (imageInstrumental && v.key === 'instrumental') || (!imageInstrumental && imageVocal === v.key)
                                  ? 'bg-cyan-600/30 border-cyan-400 text-white shadow-md scale-[1.02]'
                                  : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                              )}>
                              <span className="text-[11px] font-bold">{v.label}</span>
                              <span className="text-[9px] text-white/40">{v.desc}</span>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Ngôn ngữ bài hát */}
                      <div>
                        <label className="block text-xs font-bold text-white/70 mb-2">
                          Ngôn ngữ bài hát:
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                          {LANGUAGE_OPTIONS.map(l => (
                            <button
                              key={l.key}
                              type="button"
                              onClick={() => handleImageLanguageChange(l.key)}
                              className={clsx(
                                'p-2.5 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                                imageLanguage === l.key
                                ? 'bg-gradient-to-b from-cyan-500/30 to-indigo-500/20 border-cyan-400 text-white shadow-[0_0_16px_rgba(34,211,238,0.4)] scale-[1.02]'
                                : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                              )}>
                              <span className="text-base leading-tight">{l.flag}</span>
                              <span className="text-[10px] font-bold">{l.label}</span>
                              <span className="text-[9px] text-white/35">{l.note}</span>
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}


            {/* ── GIAO DIỆN CHẾ ĐỘ TÙY CHỈNH (CUSTOM MODE - SIGNATURE SUNO) ── */}
            {mode === 'custom' && (
              <div className="rounded-3xl p-5 sm:p-6 border border-white/10 space-y-4 sonavia-glass shadow-[0_16px_45px_rgba(0,0,0,0.5),0_0_30px_rgba(124,58,237,0.12)]">

                {/* 1. Lời bài hát */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-black uppercase tracking-wider text-white/70 flex items-center gap-1.5">
                      <MdLyrics size={15} className="text-cyan-400" />
                      Lời bài hát (Lyrics)
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setAiLyricsLanguage(customLanguage !== 'auto' ? customLanguage : 'auto')
                        setShowAiLyricsModal(true)
                      }}
                      className="text-[11px] font-black text-cyan-300 hover:text-cyan-200 flex items-center gap-1 px-2.5 py-1 rounded-lg"
                      style={{ background: 'rgba(34,211,238,0.12)', border: '1px solid rgba(34,211,238,0.25)' }}>
                      <MdAutoAwesome size={12} /> AI Viết lời tự động
                    </button>
                  </div>

                  {/* Phím tắt chèn tag phân đoạn */}
                  <div className="flex items-center gap-1.5 mb-2 overflow-x-auto pb-1">
                    {['[Verse]', '[Chorus]', '[Bridge]', '[Outro]', '[Intro]'].map(tag => (
                      <button
                        key={tag}
                        type="button"
                        onClick={() => insertLyricTag(tag)}
                        className="px-2 py-0.5 rounded-lg text-[10px] font-mono font-bold text-white/50 hover:text-white bg-white/[0.05] hover:bg-indigo-500/20 transition-all shrink-0">
                        + {tag}
                      </button>
                    ))}
                  </div>

                  <textarea
                    value={customLyrics}
                    onChange={e => setCustomLyrics(e.target.value)}
                    placeholder={"[Verse 1]\nTừng giọt mưa rơi bên hiên vắng bóng người\nNhớ nụ cười nhớ ánh mắt ngày xưa\n\n[Chorus]\nVà anh muốn hát cho em nghe khúc ca này\nGửi trọn yêu thương vào từng cơn gió bay..."}
                    rows={6}
                    className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-cyan-500 rounded-2xl p-4 text-xs font-sans text-white/90 resize-none outline-none leading-relaxed placeholder-white/20 font-medium"
                  />
                </div>

                {/* 2. Phong cách âm nhạc (Style of Music) */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-black uppercase tracking-wider text-white/70">
                      Phong cách âm nhạc (Style of Music)
                    </label>
                    <button
                      type="button"
                      onClick={() => handleEnhancePrompt('custom')}
                      disabled={enhancingPrompt || !customStyle.trim()}
                      className={clsx(
                        'text-[11px] font-bold px-2.5 py-0.5 rounded-lg flex items-center gap-1.5 transition-all shadow-sm border btn-shimmer',
                        enhancingPrompt
                          ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40 animate-pulse'
                          : 'bg-gradient-to-r from-cyan-500/15 to-indigo-500/15 border-cyan-500/30 text-cyan-300 hover:text-white hover:border-cyan-400/60 hover:bg-cyan-500/25 active:scale-95 disabled:opacity-30 disabled:pointer-events-none'
                      )}
                      title="Tối ưu hóa phong cách và nhạc cụ thông minh"
                    >
                      <MdAutoAwesome size={12} className={clsx(enhancingPrompt ? 'animate-spin text-cyan-300' : 'text-cyan-400')} />
                      {enhancingPrompt ? 'Đang tối ưu...' : '✨ Tối ưu thông minh'}
                    </button>
                  </div>
                  <textarea
                    value={customStyle}
                    onChange={e => setCustomStyle(e.target.value)}
                    placeholder="Ví dụ: Vietnamese pop ballad, emotional piano, acoustic guitar, slow tempo..."
                    rows={2}
                    className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-indigo-500 rounded-2xl p-3 text-xs text-white resize-none outline-none leading-relaxed placeholder-white/20"
                  />
                </div>

                {/* 3. Lựa chọn chất giọng (Vocalist) */}
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-white/70 mb-2">
                    Chất giọng ca sĩ (Vocalist)
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {VOCAL_OPTIONS.map(opt => (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => setVocalGender(opt.key)}
                        className={clsx(
                          'p-2.5 rounded-2xl border text-center transition-all flex flex-col items-center gap-1',
                          vocalGender === opt.key
                            ? 'bg-indigo-600/25 border-indigo-400 shadow-md scale-[1.02]'
                            : 'border-white/[0.08] hover:border-white/20 bg-white/[0.02]'
                        )}>
                        <span className="text-base">{opt.icon}</span>
                        <span className={clsx(
                          'text-xs font-bold leading-none',
                          vocalGender === opt.key ? 'text-indigo-300' : 'text-white/60'
                        )}>{opt.label}</span>
                        <span className="text-[9px] text-white/30 leading-none">{opt.desc}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 4. Ngôn ngữ bài hát (Language) */}
                <div>
                  <label className="block text-xs font-black uppercase tracking-wider text-white/70 mb-2">
                    Ngôn ngữ bài hát:
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {LANGUAGE_OPTIONS.map(l => (
                      <button
                        key={l.key}
                        type="button"
                        onClick={() => setCustomLanguage(l.key)}
                        className={clsx(
                          'p-2.5 rounded-2xl border text-center transition-all flex flex-col items-center gap-0.5',
                          customLanguage === l.key
                            ? 'bg-gradient-to-b from-indigo-500/30 to-purple-500/20 border-indigo-400 text-white shadow-[0_0_16px_rgba(99,102,241,0.4)] scale-[1.02]'
                            : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08] hover:border-white/20'
                        )}>
                        <span className="text-base leading-tight">{l.flag}</span>
                        <span className="text-[10px] font-bold">{l.label}</span>
                        <span className="text-[9px] text-white/35">{l.note}</span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* 5. Tiêu đề bài hát */}
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-black uppercase tracking-wider text-white/70">
                      Tiêu đề bài hát (Title)
                    </label>
                    <button
                      type="button"
                      onClick={handleAutoTitle}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1">
                      <MdAutoAwesome size={11} /> Tự động đặt tên
                    </button>
                  </div>
                  <input
                    type="text"
                    value={customTitle}
                    onChange={e => setCustomTitle(e.target.value)}
                    placeholder="Nhập tên bài hát..."
                    className="w-full bg-white/[0.04] border border-white/[0.09] focus:border-indigo-500 rounded-xl px-4 py-2.5 text-xs text-white outline-none"
                  />
                </div>
              </div>
            )}

            {/* Quick Style Chips */}
            <div>
              <p className="text-[11px] text-white/30 font-bold uppercase tracking-wider mb-2">Thêm nhanh phong cách:</p>
              <div className="flex flex-wrap gap-1.5">
                {STYLE_TAGS.map(tag => (
                  <button
                    key={tag.label}
                    type="button"
                    onClick={() => addStyleTag(tag)}
                    className="px-3 py-1 rounded-full text-xs font-semibold border transition-all text-white/50 border-white/[0.08] hover:border-indigo-400/50 hover:text-indigo-300 hover:bg-indigo-500/10"
                    style={{ background: 'rgba(255,255,255,0.03)' }}>
                    + {tag.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Cài đặt thời lượng & biến thể (Settings Box) */}
            <div className="rounded-3xl p-4 border border-white/[0.08] space-y-3.5"
              style={{ background: 'rgba(255,255,255,0.02)' }}>

              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white/70">Thời lượng nhạc:</span>
                <div className="flex gap-1">
                  {DURATION_OPTIONS.map(d => (
                    <button
                      key={d.s}
                      type="button"
                      onClick={() => setDuration(d.s)}
                      className={clsx(
                        'px-2.5 py-1 rounded-xl text-xs font-bold transition-all',
                        duration === d.s
                          ? 'bg-indigo-600 text-white shadow-md'
                          : 'bg-white/[0.05] text-white/40 hover:text-white'
                      )}>
                      {d.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-white/[0.04]">
                <div>
                  <span className="text-xs font-bold text-white/70">Số lượng biến thể:</span>
                  <p className="text-[10px] text-white/30">Tạo 2 bản cùng lúc để chọn bản ưng ý (chuẩn Suno)</p>
                </div>
                <div className="flex gap-1">
                  {[1, 2].map(num => (
                    <button
                      key={num}
                      type="button"
                      onClick={() => setVariationCount(num)}
                      className={clsx(
                        'px-3 py-1 rounded-xl text-xs font-black transition-all',
                        variationCount === num
                          ? 'bg-cyan-500 text-black shadow-md'
                          : 'bg-white/[0.05] text-white/40 hover:text-white'
                      )}>
                      {num} bản
                    </button>
                  ))}
                </div>
              </div>

              {/* Engine switcher */}
              <div className="pt-2 border-t border-white/[0.04] space-y-2">
                <div className="flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-white/70">Engine AI:</span>
                    <p className="text-[10px] text-white/30">
                      {engine === 'acestep' ? 'Cloud GPU: Có giọng ca sĩ, bài hát dài ~3 phút' : 'Local GPU: Offline trên máy, tối đa 30s'}
                    </p>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => setEngine('acestep')}
                      className={clsx(
                        'px-2.5 py-1 rounded-xl text-[11px] font-bold flex items-center gap-1 transition-all',
                        engine === 'acestep'
                          ? 'bg-indigo-500/30 text-indigo-300 border border-indigo-500/50'
                          : 'bg-white/[0.04] text-white/40'
                      )}>
                      <FiMic size={11} /> ACE-Step (~3 phút)
                    </button>
                    <button
                      type="button"
                      onClick={() => setEngine('musicgen')}
                      className={clsx(
                        'px-2.5 py-1 rounded-xl text-[11px] font-bold flex items-center gap-1 transition-all',
                        engine === 'musicgen'
                          ? 'bg-indigo-500/30 text-indigo-300 border border-indigo-500/50'
                          : 'bg-white/[0.04] text-white/40'
                      )}>
                      <FiMusic size={11} /> MusicGen GPU (30s)
                    </button>
                  </div>
                </div>

                {engine === 'musicgen' && duration >= 60 && (
                  <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-start gap-2 text-[11px] text-amber-200/90 leading-tight">
                    <FiAlertCircle size={14} className="text-amber-400 shrink-0 mt-0.5" />
                    <span>Mô hình <b>Meta MusicGen</b> trên GPU máy chỉ hỗ trợ độ dài tối đa <b>30 giây</b>. Hãy chọn <b>ACE-Step (~3 phút)</b> để tạo bài hát đầy đủ {Math.floor(duration / 60)} phút có ca sĩ hát.</span>
                  </div>
                )}
              </div>
            </div>

            {/* NÚT TẠO BÀI HÁT LỚN (SUNO CREATE BUTTON) */}
            <button
              type="button"
              onClick={handleCreate}
              disabled={isGenerating}
              className="w-full py-4 rounded-3xl font-black text-base transition-all duration-300 flex items-center justify-center gap-3 shadow-2xl active:scale-[0.98] relative overflow-hidden group btn-shimmer"
              style={{
                background: isGenerating
                  ? 'rgba(99,102,241,0.3)'
                  : 'linear-gradient(135deg, #4f46e5 0%, #6366f1 45%, #22d3ee 100%)',
                boxShadow: isGenerating
                  ? 'none'
                  : '0 14px 40px rgba(99,102,241,0.5), 0 0 25px rgba(34,211,238,0.35)',
                cursor: isGenerating ? 'not-allowed' : 'pointer',
              }}>
              {isGenerating ? (
                <>
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>
                    {mode === 'image'
                      ? `Đang sáng tác nhạc từ bức ảnh (${variationCount > 1 ? '2 bản phối' : '1 bản'})...`
                      : `Đang sáng tác ${variationCount > 1 ? '2 bản phối' : 'bài hát'}...`}
                  </span>
                </>
              ) : (
                <>
                  {mode === 'image' ? (
                    <MdAutoAwesome size={22} className="text-white group-hover:scale-110 transition-transform text-cyan-300" />
                  ) : (
                    <MdGraphicEq size={22} className="text-white group-hover:scale-110 transition-transform" />
                  )}
                  <span>
                    {mode === 'image'
                      ? (variationCount > 1 ? 'Sáng tác 2 bản nhạc theo ảnh' : 'Sáng tác nhạc theo bức ảnh')
                      : `Tạo ${variationCount > 1 ? '2 bản nhạc' : 'bài hát'}`}{' '}
                    {((mode === 'image' && !imageInstrumental) || (mode === 'simple' && !simpleInstrumental) || (mode === 'custom' && vocalGender !== 'instrumental'))
                      ? '(Có giọng hát)'
                      : '(Hòa tấu)'}
                  </span>
                </>
              )}
            </button>

            <p className="text-center text-[11px] text-white/25">
              Phím tắt: nhấn <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-white/10">⌘ / Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded text-[10px] bg-white/10">Enter</kbd> để tạo nhanh
            </p>
          </div>

          {/* ═══════════════════════════════════════════════════════════════════ */}
          {/* ── CỘT PHẢI: KHÔNG GIAN SÁNG TÁC & DANH SÁCH BÀI (CREATIONS FEED) ─ */}
          {/* ═══════════════════════════════════════════════════════════════════ */}
          <div className="lg:col-span-7 space-y-4">
            {/* Header danh sách */}
            <div className="flex items-center justify-between px-2">
              <div className="flex items-center gap-2">
                <h2 className="text-base font-black text-white flex items-center gap-2">
                  <MdQueueMusic size={18} className="text-indigo-400" />
                  Thư viện sáng tác của bạn
                </h2>
                <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-white/10 text-white/70">
                  {tracks.length} bài
                </span>
              </div>

              {tracks.length > 0 && (
                <button
                  onClick={() => {
                    if (window.confirm('Bạn có chắc muốn xóa danh sách sáng tác của tài khoản này?')) {
                      tracks.forEach(t => deleteTrackAudioBlob(t.id))
                      setTracks([])
                      try { localStorage.removeItem(userStorageKey) } catch {}
                    }
                  }}
                  className="text-xs text-white/30 hover:text-rose-400 flex items-center gap-1 transition-colors">
                  <FiTrash2 size={12} /> Xóa danh sách
                </button>
              )}
            </div>

            {/* Các thẻ đang xử lý (Generating Cards) */}
            {isGenerating && (
              <div className="space-y-3 animate-fade-in">
                {generatingSeeds.map((vNum) => (
                  <SunoGeneratingCard
                    key={vNum}
                    variationNumber={vNum}
                    duration={duration}
                    prompt={mode === 'simple' ? simplePrompt : customStyle}
                    engine={engine}
                  />
                ))}
              </div>
            )}

            {/* Danh sách bài hát đã tạo (Track Cards) */}
            {tracks.length > 0 && (
              <div className="space-y-3.5">
                {tracks.map((track) => (
                  <SunoTrackCard
                    key={track.id}
                    track={track}
                    onDelete={(id) => {
                      deleteTrackAudioBlob(id)
                      setTracks(prev => prev.filter(t => t.id !== id))
                    }}
                    onSave={(t) => setSaveModalTrack(t)}
                    onRemix={(t) => handleRemix(t)}
                    onViewLyrics={(t) => setLyricsModalTrack(t)}
                    onShare={(t) => setShareModalTrack(t)}
                  />
                ))}
              </div>
            )}

            {/* Trạng thái trống (Empty State) */}
            {!isGenerating && tracks.length === 0 && (
              <div className="rounded-3xl p-12 text-center border border-white/[0.06] space-y-4"
                style={{ background: 'rgba(255,255,255,0.02)' }}>
                <div className="w-16 h-16 rounded-3xl mx-auto flex items-center justify-center"
                  style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(34,211,238,0.1))' }}>
                  <MdGraphicEq size={32} className="text-indigo-300" />
                </div>
                <div>
                  <h3 className="text-lg font-black text-white">Chưa có bài hát nào</h3>
                  <p className="text-xs text-white/40 max-w-sm mx-auto mt-1">
                    Hãy nhập mô tả bài hát ở cột bên trái hoặc bấm nút "AI Viết lời tự động" để bắt đầu sáng tác!
                  </p>
                </div>

                <div className="pt-2 flex justify-center gap-2 flex-wrap max-w-md mx-auto">
                  {PROMPT_EXAMPLES.slice(0, 3).map((ex, i) => (
                    <button
                      key={i}
                      onClick={() => {
                        setMode('simple')
                        setSimplePrompt(ex)
                      }}
                      className="text-left px-3.5 py-2 rounded-xl text-xs text-white/60 hover:text-white bg-white/[0.04] hover:bg-white/[0.08] transition-all border border-white/[0.06]">
                      "{ex.slice(0, 45)}..."
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Modal AI Viết Lời Bài Hát (Smart AI Lyricist) ── */}
      {showAiLyricsModal && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
          style={{ background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(16px)' }}
          onClick={e => e.target === e.currentTarget && setShowAiLyricsModal(false)}>
          <div className="w-full max-w-md rounded-3xl overflow-hidden shadow-2xl animate-scale-in"
            style={{
              background: 'rgba(12,12,28,0.98)',
              border: '1px solid rgba(34,211,238,0.3)',
            }}>
            <div className="flex items-center justify-between px-6 py-5 border-b border-white/[0.08]">
              <div className="flex items-center gap-2.5">
                <MdAutoAwesome size={18} className="text-cyan-400" />
                <h3 className="font-black text-white text-base">AI Viết lời bài hát</h3>
              </div>
              <button onClick={() => setShowAiLyricsModal(false)} className="text-white/40 hover:text-white">
                <FiX size={18} />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div>
                <label className="block text-xs font-bold text-white/70 mb-2">
                  Chủ đề hoặc câu chuyện bạn muốn kể:
                </label>
                <input
                  type="text"
                  value={aiTopic}
                  onChange={e => setAiTopic(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleGenerateAiLyrics() }}
                  placeholder="Ví dụ: Mưa đêm Hà Nội, thanh xuân tuổi học trò, tình yêu xa..."
                  autoFocus
                  className="w-full bg-white/[0.05] border border-white/[0.09] focus:border-cyan-400 rounded-xl px-4 py-3 text-sm text-white outline-none"
                />
              </div>

              <div>
                <p className="text-[11px] text-white/40 mb-1.5 font-medium">Chủ đề gợi ý:</p>
                <div className="flex flex-wrap gap-1.5">
                  {['Tình yêu lãng mạn', 'Thất tình dưới mưa', 'Thanh xuân áo trắng', 'Bình yên & Chill', 'Cháy hết đam mê'].map(th => (
                    <button
                      key={th}
                      type="button"
                      onClick={() => setAiTopic(th)}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-white/[0.05] hover:bg-cyan-500/20 text-white/60 hover:text-cyan-300 transition-all border border-white/[0.06]">
                      {th}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-white/70 mb-2">
                  Ngôn ngữ ca từ muốn sáng tác:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {LANGUAGE_OPTIONS.map(l => (
                    <button
                      key={l.key}
                      type="button"
                      onClick={() => setAiLyricsLanguage(l.key)}
                      className={clsx(
                        'p-2 rounded-xl border text-center transition-all flex flex-col items-center gap-0.5',
                        aiLyricsLanguage === l.key
                          ? 'bg-gradient-to-b from-cyan-500/30 to-indigo-500/20 border-cyan-400 text-white shadow-md scale-[1.02]'
                          : 'bg-black/30 border-white/10 text-white/50 hover:text-white hover:bg-white/[0.08]'
                      )}>
                      <span className="text-base leading-tight">{l.flag}</span>
                      <span className="text-[10px] font-bold">{l.label}</span>
                      <span className="text-[9px] text-white/35">{l.note}</span>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAiLyricsModal(false)}
                  className="flex-1 py-3 rounded-2xl text-xs font-bold text-white/60 hover:text-white bg-white/[0.05]">
                  Hủy
                </button>
                <button
                  type="button"
                  onClick={handleGenerateAiLyrics}
                  disabled={!aiTopic.trim() || aiLyricsLoading}
                  className="flex-1 py-3 rounded-2xl text-xs font-black text-white flex items-center justify-center gap-2"
                  style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
                  {aiLyricsLoading ? (
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <MdAutoAwesome size={14} />
                  )}
                  {aiLyricsLoading ? 'Đang viết lời...' : 'Tạo lời bài hát'}
                </button>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* ── Modal Xem Lời Bài Hát (Lyrics Modal) ── */}
      {lyricsModalTrack && (
        <LyricsModal
          track={lyricsModalTrack}
          onClose={() => setLyricsModalTrack(null)}
        />
      )}

      {/* ── Modal Đăng Bài Lên Bảng Tin (Share to Feed Modal) ── */}
      {shareModalTrack && (
        <SharePostModal
          track={shareModalTrack}
          onClose={() => setShareModalTrack(null)}
        />
      )}

      {/* ── Modal Lưu Vào Thư Viện (SaveSongModal) ── */}
      {saveModalTrack && (
        <SaveSongModal
          track={saveModalTrack}
          onClose={() => setSaveModalTrack(null)}
          onSaved={(savedSong) => {
            setSaveModalTrack(null)
            const permUrl = savedSong?.audio_file || savedSong?.audio_url
            if (permUrl) {
              setTracks(prev => prev.map(t => t.id === saveModalTrack.id ? {
                ...t,
                savedSongId: savedSong.id,
                audioUrl: permUrl,
                serverAudioUrl: permUrl,
              } : t))
            }
            toast.success(`✅ "${savedSong.title}" đã lưu vào thư viện!`)
          }}
        />
      )}
    </div>
  )
}
