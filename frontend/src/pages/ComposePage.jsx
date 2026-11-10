import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FiPlay, FiPause, FiDownload, FiSave, FiRefreshCw,
  FiCopy, FiCheck, FiCpu, FiMusic, FiSend, FiZap,
  FiChevronDown, FiChevronUp, FiClock, FiInfo, FiX,
  FiMic, FiVolume2, FiAlertCircle,
} from 'react-icons/fi'
import {
  MdGraphicEq, MdAutoAwesome, MdMusicNote,
  MdLyrics, MdPiano, MdChat, MdTimer,
} from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import clsx from 'clsx'

// ─── Constants ────────────────────────────────────────────────────────────────

const MOODS = [
  { key: 'happy', emoji: '😄', label: 'Vui vẻ', color: '#f59e0b' },
  { key: 'sad', emoji: '😢', label: 'Buồn', color: '#60a5fa' },
  { key: 'energetic', emoji: '⚡', label: 'Sôi động', color: '#f97316' },
  { key: 'calm', emoji: '🌿', label: 'Bình yên', color: '#34d399' },
  { key: 'romantic', emoji: '💕', label: 'Lãng mạn', color: '#f472b6' },
  { key: 'melancholic', emoji: '🌙', label: 'Hoài niệm', color: '#a78bfa' },
  { key: 'uplifting', emoji: '🌟', label: 'Phấn khởi', color: '#22d3ee' },
  { key: 'angry', emoji: '🔥', label: 'Mạnh mẽ', color: '#ef4444' },
]

const GENRES = [
  { key: 'vpop', label: '🇻🇳 V-Pop' },
  { key: 'kpop', label: '🇰🇷 K-Pop' },
  { key: 'pop', label: '🎤 Pop' },
  { key: 'rock', label: '🎸 Rock' },
  { key: 'jazz', label: '🎷 Jazz' },
  { key: 'lofi', label: '☕ Lo-fi' },
  { key: 'classical', label: '🎻 Classical' },
  { key: 'hip_hop', label: '🎧 Hip-Hop' },
  { key: 'r&b', label: '🎵 R&B' },
  { key: 'electronic', label: '🎹 Electronic' },
  { key: 'folk', label: '🪕 Folk' },
  { key: 'indie', label: '🌿 Indie' },
]

const TEMPOS = [
  { key: 'slow', label: 'Chậm', bpm: '60-80', emoji: '🐢' },
  { key: 'medium', label: 'Vừa', bpm: '90-120', emoji: '🚶' },
  { key: 'fast', label: 'Nhanh', bpm: '130-160', emoji: '🏃' },
]

const INSTRUMENTS = [
  { key: 'full', label: '🎼 Full band' },
  { key: 'piano', label: '🎹 Piano' },
  { key: 'guitar', label: '🎸 Guitar' },
  { key: 'strings', label: '🎻 Strings' },
  { key: 'synth', label: '🔊 Synth' },
  { key: 'minimal', label: '✨ Minimal' },
]

const VOICES = [
  { key: 'female_vi', label: '👩 Nữ (Châu Á)' },
  { key: 'male_vi', label: '👨 Nam (Châu Á)' },
  { key: 'female_soft', label: '🌸 Nữ (Nhẹ)' },
  { key: 'male_deep', label: '🎙️ Nam (Trầm)' },
]

const DURATIONS = [
  { seconds: 60, label: '1 phút', note: '~1-2 phút xử lý' },
  { seconds: 120, label: '2 phút', note: '~2-4 phút xử lý' },
  { seconds: 180, label: '3 phút', note: '~4-7 phút xử lý' },
  { seconds: 240, label: '4 phút', note: '~7-12 phút xử lý' },
]

const PRESETS = [
  { label: '💕 V-Pop Lãng mạn', genre: 'vpop', mood: 'romantic', tempo: 'medium', instruments: 'strings' },
  { label: '🔥 Rock Bốc lửa', genre: 'rock', mood: 'energetic', tempo: 'fast', instruments: 'full' },
  { label: '☕ Lo-fi Chill', genre: 'lofi', mood: 'calm', tempo: 'slow', instruments: 'minimal' },
  { label: '😢 Ballad Buồn', genre: 'pop', mood: 'sad', tempo: 'slow', instruments: 'piano' },
  { label: '🎷 Jazz Thư giãn', genre: 'jazz', mood: 'calm', tempo: 'medium', instruments: 'full' },
  { label: '⚡ EDM Sôi động', genre: 'electronic', mood: 'energetic', tempo: 'fast', instruments: 'synth' },
  { label: '🌙 K-Pop', genre: 'kpop', mood: 'melancholic', tempo: 'medium', instruments: 'full' },
  { label: '🌟 Pop Phấn khởi', genre: 'pop', mood: 'uplifting', tempo: 'fast', instruments: 'full' },
]

// ─── Helpers ──────────────────────────────────────────────────────────────────

function fmtTime(s) {
  if (!s || isNaN(s)) return '0:00'
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

function fmtSeconds(s) {
  if (!s) return ''
  const m = Math.floor(s / 60)
  const sec = s % 60
  return m > 0 ? `${m}:${String(sec).padStart(2, '0')}` : `${sec}s`
}

// ─── WaveBar animation ────────────────────────────────────────────────────────

function WaveBar({ playing, color = '#6366f1', bars = 18 }) {
  return (
    <div className="flex items-end gap-[2px] h-10">
      {Array.from({ length: bars }).map((_, i) => (
        <div key={i} className="w-1 rounded-full transition-all duration-100"
          style={{
            background: color,
            height: playing ? `${25 + Math.sin(i * 0.8) * 20}%` : `${15 + (i % 4) * 5}%`,
            animation: playing ? `eq-bar ${0.5 + (i % 4) * 0.15}s ease ${i * 0.04}s infinite` : 'none',
            opacity: 0.6 + (i % 3) * 0.1,
          }}
        />
      ))}
    </div>
  )
}

// ─── Progress Bar (Suno-style) ────────────────────────────────────────────────

function ProgressPanel({ pct, message, elapsed, estimatedTotal }) {
  const remaining = estimatedTotal && elapsed ? Math.max(0, estimatedTotal - elapsed) : null

  const PHASES = [
    { label: 'Khởi động', from: 0, to: 5 },
    { label: 'Nhạc nền', from: 5, to: 50 },
    { label: 'Giọng hát', from: 50, to: 88 },
    { label: 'Mix audio', from: 88, to: 98 },
    { label: 'Hoàn thành', from: 98, to: 100 },
  ]
  const currentPhase = PHASES.findLast(p => pct >= p.from) || PHASES[0]

  return (
    <div className="glass-card overflow-hidden animate-fade-in">
      {/* Animated top border */}
      <div className="h-0.5 w-full overflow-hidden">
        <div className="h-full animate-shimmer"
          style={{
            width: `${pct}%`,
            background: 'linear-gradient(to right, #4f46e5, #6366f1, #22d3ee)',
            transition: 'width 0.8s ease',
          }} />
      </div>

      <div className="p-6">
        {/* Spinning rings + icon */}
        <div className="relative w-20 h-20 mx-auto mb-5">
          <div className="absolute inset-0 rounded-full border-2 border-indigo-500/20 animate-spin"
            style={{ animationDuration: '4s' }} />
          <div className="absolute inset-2 rounded-full border-2 border-indigo-400/30 animate-spin"
            style={{ animationDuration: '2.5s', animationDirection: 'reverse' }} />
          <div className="absolute inset-4 rounded-full border-2 border-cyan-400/40 animate-spin"
            style={{ animationDuration: '1.8s' }} />
          {/* Percentage */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-lg font-black text-white">{pct}%</span>
          </div>
        </div>

        {/* Phase steps */}
        <div className="flex justify-center gap-1.5 mb-4 flex-wrap">
          {PHASES.map((phase, i) => {
            const done = pct > phase.to
            const active = pct >= phase.from && pct <= phase.to
            return (
              <div key={i} className={clsx(
                'flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-semibold transition-all',
                done ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/25' :
                  active ? 'bg-indigo-500/20  text-indigo-300  border border-indigo-500/30 animate-pulse' :
                    'bg-white/[0.04]   text-white/25   border border-white/[0.06]'
              )}>
                {done ? '✓' : active ? '→' : '·'}
                {phase.label}
              </div>
            )
          })}
        </div>

        {/* Status message */}
        <p className="text-sm text-white/70 text-center font-medium mb-1 min-h-[20px]">{message}</p>

        {/* Time info */}
        <div className="flex justify-center gap-4 text-[11px] text-white/30">
          {elapsed > 0 && (
            <span className="flex items-center gap-1">
              <FiClock size={10} /> Đã chạy {fmtSeconds(elapsed)}
            </span>
          )}
          {remaining !== null && remaining > 0 && (
            <span className="flex items-center gap-1">
              <MdTimer size={11} /> Còn ~{fmtSeconds(remaining)}
            </span>
          )}
        </div>

        {/* Equalizer */}
        <div className="flex justify-center mt-4">
          <WaveBar playing color="#6366f1" bars={24} />
        </div>

        <p className="text-[10px] text-white/20 text-center mt-3">
          RTX 3050 · Sonavia Studio Engine · Tiếng Việt
        </p>
      </div>
    </div>
  )
}

// ─── Track Card (kết quả generate) ───────────────────────────────────────────

function TrackCard({ track, onSave, onDelete }) {
  const [playing, setPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [copied, setCopied] = useState(false)
  const audioRef = useRef(null)
  const { isAuthenticated } = useAuthStore()
  const mood = MOODS.find(m => m.key === track.mood)
  const genre = GENRES.find(g => g.key === track.genre)

  const togglePlay = () => {
    const a = audioRef.current
    if (!a) return
    if (playing) { a.pause(); setPlaying(false) }
    else { a.play(); setPlaying(true) }
  }

  const handleDownload = async () => {
    const url = track.audioUrl
    if (!url) return
    const ext = (track.format || (url.toLowerCase().includes('.mp3') ? 'mp3' : 'wav')).replace('.', '').toLowerCase()
    const fileName = `aimusic_${track.genre}_${track.mood}.${ext}`

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
      toast.success(`Đã tải file .${ext.toUpperCase()}!`)
    } catch {
      const a = document.createElement('a')
      a.href = url
      a.download = fileName
      a.target = '_blank'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      toast.success(`Đã tải file .${ext.toUpperCase()}!`)
    }
  }

  const handleCopyLyrics = () => {
    if (!track.lyrics) return
    navigator.clipboard.writeText(track.lyrics)
    setCopied(true); setTimeout(() => setCopied(false), 2000)
    toast.success('Đã copy lời!')
  }

  return (
    <div className={clsx(
      'glass-card overflow-hidden animate-slide-up transition-all',
      playing && 'border-indigo-500/40 shadow-lg shadow-indigo-500/10'
    )}>
      {/* Mood color bar */}
      <div className="h-1 w-full transition-all"
        style={{ background: `linear-gradient(to right, ${mood?.color || '#6366f1'}, ${mood?.color || '#6366f1'}30)` }} />

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start gap-3 mb-4">
          {/* Album art placeholder */}
          <div className="relative w-14 h-14 rounded-2xl overflow-hidden shrink-0"
            style={{ background: `linear-gradient(135deg, ${mood?.color || '#6366f1'}30, ${mood?.color || '#6366f1'}10)` }}>
            <div className="absolute inset-0 flex items-center justify-center">
              {playing
                ? <div className="eq-bars scale-110"><div className="eq-bar" /><div className="eq-bar" /><div className="eq-bar" /></div>
                : <MdMusicNote size={22} style={{ color: mood?.color || '#6366f1' }} />
              }
            </div>
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-black text-white text-sm leading-tight mb-1 truncate">
              {track.title}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="badge badge-purple text-[9px]">
                {track.withVocal ? '🎤 Sonavia AI' : '🎵 MusicGen'}
              </span>
              <span className="text-[11px]" style={{ color: mood?.color }}>
                {mood?.emoji} {mood?.label}
              </span>
              <span className="text-white/20">·</span>
              <span className="text-[11px] text-white/40">{genre?.label}</span>
              <span className="text-white/20">·</span>
              <span className="text-[11px] text-white/40">{fmtSeconds(track.duration)}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-1.5 shrink-0">
            <button onClick={handleDownload}
              className="btn-icon w-7 h-7 text-white/35 hover:text-white" title="Tải WAV">
              <FiDownload size={13} />
            </button>
            {isAuthenticated && (
              <button onClick={() => onSave(track)}
                className="btn-icon w-7 h-7 text-white/35 hover:text-indigo-400" title="Lưu thư viện">
                <FiSave size={13} />
              </button>
            )}
            <button onClick={() => onDelete(track.id)}
              className="btn-icon w-7 h-7 text-white/20 hover:text-red-400" title="Xóa">
              <FiX size={13} />
            </button>
          </div>
        </div>

        {/* Audio player */}
        <audio ref={audioRef} src={track.audioUrl}
          onEnded={() => setPlaying(false)}
          onTimeUpdate={() => setCurrentTime(audioRef.current?.currentTime || 0)}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
        />

        {/* Waveform + seek */}
        <div className="mb-3 p-3 rounded-2xl border border-white/[0.05]"
          style={{ background: 'rgba(99,102,241,0.05)' }}>
          <div className="mb-3">
            <WaveBar playing={playing} color={mood?.color || '#6366f1'} bars={32} />
          </div>
          <div className="flex items-center gap-2.5">
            <button onClick={togglePlay}
              className="w-10 h-10 bg-white rounded-full flex items-center justify-center
                         hover:scale-105 active:scale-95 transition-all shadow-lg shrink-0">
              {playing ? <FiPause size={16} className="text-black" /> : <FiPlay size={16} className="text-black ml-0.5" />}
            </button>
            <span className="text-[10px] text-white/30 tabular-nums w-8 text-right">{fmtTime(currentTime)}</span>
            <div className="flex-1 h-1.5 rounded-full cursor-pointer relative group"
              style={{ background: 'rgba(255,255,255,0.08)' }}
              onClick={e => {
                const rect = e.currentTarget.getBoundingClientRect()
                const pct = (e.clientX - rect.left) / rect.width
                if (audioRef.current?.duration) audioRef.current.currentTime = pct * audioRef.current.duration
              }}>
              <div className="h-full rounded-full transition-all"
                style={{
                  width: `${duration ? (currentTime / duration) * 100 : 0}%`,
                  background: mood?.color || '#6366f1',
                }} />
              <div className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow opacity-0 group-hover:opacity-100 transition-opacity"
                style={{ left: `calc(${duration ? (currentTime / duration) * 100 : 0}% - 6px)` }} />
            </div>
            <span className="text-[10px] text-white/30 tabular-nums w-8">{fmtTime(duration)}</span>
          </div>
        </div>

        {/* Lyrics */}
        {track.lyrics && (
          <details className="group mt-2">
            <summary className="flex items-center gap-2 cursor-pointer py-1.5 text-xs text-white/40 hover:text-white/70 transition-colors select-none">
              <MdLyrics size={13} className="text-indigo-400" />
              <span>Lời bài hát</span>
              <FiChevronDown size={11} className="ml-auto group-open:rotate-180 transition-transform" />
            </summary>
            <div className="mt-2 p-3 rounded-xl border border-white/[0.05] relative"
              style={{ background: 'rgba(255,255,255,0.02)' }}>
              <button onClick={handleCopyLyrics}
                className="absolute top-2 right-2 btn-icon w-6 h-6 text-white/25">
                {copied ? <FiCheck size={11} className="text-emerald-400" /> : <FiCopy size={11} />}
              </button>
              <pre className="text-xs text-white/60 whitespace-pre-wrap font-sans leading-6 pr-6">
                {track.lyrics}
              </pre>
            </div>
          </details>
        )}

        {/* Prompt */}
        {track.prompt && (
          <details className="mt-1">
            <summary className="flex items-center gap-1.5 cursor-pointer py-1 text-[10px] text-white/20 hover:text-white/40 transition-colors select-none">
              <FiInfo size={9} /> AI Prompt
            </summary>
            <p className="mt-1 text-[10px] text-white/30 font-mono p-2 rounded-lg leading-relaxed"
              style={{ background: 'rgba(255,255,255,0.02)' }}>{track.prompt}</p>
          </details>
        )}
      </div>
    </div>
  )
}

// ─── AI Chatbot Panel ─────────────────────────────────────────────────────────

function ChatbotPanel({ onApplySuggestion }) {
  const [msgs, setMsgs] = useState([{
    role: 'bot',
    text: '🎵 Chào! Mô tả nhạc bạn muốn tạo, tôi sẽ gợi ý cài đặt phù hợp!',
  }])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [msgs, loading])

  const send = async (text) => {
    const msg = (text || input).trim()
    if (!msg || loading) return
    setInput('')
    setMsgs(p => [...p, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const { data } = await api.post('/ai/chatbot/', { message: msg })
      setMsgs(p => [...p, {
        role: 'bot',
        text: data.message || 'Thử cài đặt này nhé!',
        suggestion: data.mood ? { mood: data.mood, genres: data.recommended_genres } : null,
        songs: data.songs,
      }])
    } catch {
      setMsgs(p => [...p, { role: 'bot', text: 'Xin lỗi, thử lại nhé! 😅' }])
    }
    setLoading(false)
  }

  const QUICK = ['Nhạc V-Pop buồn', 'EDM sôi động', 'Jazz thư giãn', 'Ballad lãng mạn']

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-4 py-3 shrink-0 border-b border-white/[0.05]">
        <div className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
          style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
          <MdChat size={13} className="text-white" />
        </div>
        <div>
          <p className="text-xs font-bold text-white">AI Tư vấn</p>
          <p className="text-[9px] text-emerald-400">● Online</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-3 space-y-2.5 scrollbar-none">
        {msgs.map((m, i) => (
          <div key={i} className={clsx('flex gap-2', m.role === 'user' && 'justify-end')}>
            {m.role === 'bot' && (
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] shrink-0 mt-0.5"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>🤖</div>
            )}
            <div className={clsx(
              'max-w-[85%] rounded-2xl px-3 py-2 text-xs leading-relaxed',
              m.role === 'user'
                ? 'text-white rounded-br-sm'
                : 'border border-white/[0.07] text-white/80 rounded-bl-sm'
            )} style={m.role === 'user'
              ? { background: 'linear-gradient(135deg, #4f46e5, #6366f1)' }
              : { background: 'rgba(255,255,255,0.05)' }}>
              {m.text}
              {m.suggestion && (
                <button onClick={() => onApplySuggestion(m.suggestion)}
                  className="mt-2 flex items-center gap-1.5 text-[10px] px-2.5 py-1.5 rounded-lg transition-all font-semibold"
                  style={{ background: 'rgba(99,102,241,0.2)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.3)' }}>
                  <FiZap size={9} /> Áp dụng gợi ý
                </button>
              )}
              {m.songs?.length > 0 && (
                <div className="mt-1.5 space-y-1">
                  {m.songs.slice(0, 3).map(s => (
                    <Link key={s.id} to={`/songs/${s.id}`}
                      className="flex items-center gap-1.5 text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors">
                      <MdMusicNote size={9} /> {s.title}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-2">
            <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] shrink-0"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>🤖</div>
            <div className="bg-white/[0.05] border border-white/[0.07] rounded-2xl rounded-bl-sm px-3 py-2.5 flex gap-1">
              {[0, 1, 2].map(i => (
                <div key={i} className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="px-3 pb-2 flex gap-1.5 flex-wrap shrink-0">
        {QUICK.map(q => (
          <button key={q} onClick={() => send(q)}
            className="text-[9px] text-white/40 hover:text-white px-2 py-1 rounded-full border border-white/[0.06] hover:border-white/15 transition-all"
            style={{ background: 'rgba(255,255,255,0.03)' }}>
            {q}
          </button>
        ))}
      </div>

      <div className="px-3 pb-3 border-t border-white/[0.05] pt-2 shrink-0">
        <form onSubmit={e => { e.preventDefault(); send() }} className="flex gap-2">
          <input value={input} onChange={e => setInput(e.target.value)}
            placeholder="Hỏi AI gợi ý..."
            className="input-field flex-1 text-xs py-2" disabled={loading} />
          <button type="submit" disabled={!input.trim() || loading}
            className="btn-primary px-2.5 py-2 text-xs shrink-0">
            <FiSend size={12} />
          </button>
        </form>
      </div>
    </div>
  )
}

// ─── MAIN COMPOSE PAGE ────────────────────────────────────────────────────────

export default function ComposePage() {
  const { isAuthenticated } = useAuthStore()

  // Mode: 'full' (2-3 phút, Sonavia Studio) | 'quick' (30s, chỉ MusicGen)
  const [mode, setMode] = useState('full')

  // Shared form state
  const [form, setForm] = useState({
    genre: 'vpop', mood: 'romantic', tempo: 'medium',
    instruments: 'strings', custom_prompt: '',
    // Full mode
    total_duration: 180, voice: 'female_vi', with_vocal: true,
    guidance_scale: 3.0, temperature: 1.0,
    model: 'facebook/musicgen-small',
    // Lyrics
    num_verses: 2, has_chorus: true, title: '',
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Output
  const [tracks, setTracks] = useState([])
  const [lyrics, setLyrics] = useState(null)
  const [midiPreview, setMidiPreview] = useState(null)
  const [promptPreview, setPromptPreview] = useState('')
  const [copiedLyrics, setCopiedLyrics] = useState(false)

  // Loading
  const [genLoading, setGenLoading] = useState(false)
  const [lyricsLoading, setLyricsLoading] = useState(false)
  const [midiLoading, setMidiLoading] = useState(false)
  const [dlMidi, setDlMidi] = useState(false)

  // Full song job tracking
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState(null)   // { pct, message, elapsed, status }
  const [estTotal, setEstTotal] = useState(null)
  const pollRef = useRef(null)

  // Active tab
  const [activeTab, setActiveTab] = useState('music')   // 'music'|'lyrics'|'midi'

  // GPU status
  const [gpuStatus, setGpuStatus] = useState(null)

  const moodInfo = MOODS.find(m => m.key === form.mood)

  useEffect(() => {
    api.get('/ai/generate/status/').then(r => setGpuStatus(r.data)).catch(() => { })
  }, [])

  // Live prompt preview
  useEffect(() => {
    const t = setTimeout(() => {
      api.post('/ai/generate/preview/', form)
        .then(r => setPromptPreview(r.data.prompt))
        .catch(() => { })
    }, 500)
    return () => clearTimeout(t)
  }, [form.genre, form.mood, form.tempo, form.instruments, form.custom_prompt])

  // Poll job status khi đang generate Full song
  useEffect(() => {
    if (!jobId) return
    pollRef.current = setInterval(async () => {
      try {
        const { data } = await api.get(`/ai/generate/full/${jobId}/status/`)
        setJobStatus({
          pct: data.pct,
          message: data.message,
          elapsed: data.elapsed,
          status: data.status,
        })

        if (data.status === 'done') {
          clearInterval(pollRef.current)
          // Download audio
          try {
            const res = await api.get(`/ai/generate/full/${jobId}/download/`, { responseType: 'blob' })
            const cType = res.headers['content-type'] || (res.headers['x-format'] === 'mp3' ? 'audio/mpeg' : 'audio/wav')
            const fmt = res.headers['x-format'] || (cType.includes('mpeg') ? 'mp3' : 'wav')
            const blob = new Blob([res.data], { type: cType })
            const audioUrl = URL.createObjectURL(blob)
            const prompt = res.headers['x-prompt'] || promptPreview
            const dur = parseInt(res.headers['x-duration'] || form.total_duration)

            const newTrack = {
              id: Date.now(),
              audioUrl, prompt, duration: dur,
              genre: form.genre,
              mood: form.mood,
              tempo: form.tempo,
              format: fmt,
              withVocal: form.with_vocal,
              lyrics: lyrics?.lyrics || null,
              title: form.title || `${moodInfo?.emoji} ${moodInfo?.label} — ${GENRES.find(g => g.key === form.genre)?.label}`,
            }
            setTracks(p => [newTrack, ...p])
            setJobId(null)
            setJobStatus(null)
            setGenLoading(false)
            setActiveTab('music')
            toast.success('🎵 Bài nhạc đã sáng tác xong!')
            api.get('/ai/generate/status/').then(r => setGpuStatus(r.data)).catch(() => { })
          } catch (e) {
            toast.error('Lỗi tải file audio')
            setGenLoading(false); setJobId(null); setJobStatus(null)
          }
        } else if (data.status === 'error') {
          clearInterval(pollRef.current)
          toast.error(`Lỗi: ${data.error || 'Xem console backend'}`)
          setGenLoading(false); setJobId(null); setJobStatus(null)
        }
      } catch { /* ignore poll errors */ }
    }, 2000)   // poll mỗi 2 giây
    return () => clearInterval(pollRef.current)
  }, [jobId])

  const applyPreset = (preset) => {
    setForm(f => ({ ...f, ...preset }))
    toast.success(`Preset: ${preset.label}`)
  }

  const handleApplyChatSuggestion = (suggestion) => {
    if (suggestion.mood) setForm(f => ({ ...f, mood: suggestion.mood }))
    if (suggestion.genres?.length) setForm(f => ({ ...f, genre: suggestion.genres[0] }))
    toast.success('Đã áp dụng gợi ý!')
  }

  const validateComposeForm = () => {
    if (!form.genre) {
      toast.error('Vui lòng chọn thể loại nhạc.')
      return false
    }
    if (!form.mood) {
      toast.error('Vui lòng chọn cảm xúc cho bài nhạc.')
      return false
    }
    if (form.with_vocal && !lyrics?.lyrics) {
      toast.error('Vui lòng tạo lời nhạc trước khi bật giọng hát.')
      return false
    }
    return true
  }

  // ── Generate Full Song ──
  const handleGenerateFull = async () => {
    if (!validateComposeForm()) return
    if (!lyrics && form.with_vocal) {
      const ok = window.confirm('Bạn chưa tạo lời nhạc. Tạo nhạc nền không có giọng hát?')
      if (!ok) return
      setForm(f => ({ ...f, with_vocal: false }))
    }
    setGenLoading(true)
    setActiveTab('music')
    try {
      const { data } = await api.post('/ai/generate/full/', {
        genre: form.genre,
        mood: form.mood,
        tempo: form.tempo,
        instruments: form.instruments,
        custom_prompt: form.custom_prompt,
        total_duration: form.total_duration,
        lyrics: lyrics?.lyrics || '',
        voice: form.voice,
        with_vocal: form.with_vocal && !!lyrics?.lyrics,
        guidance_scale: form.guidance_scale,
        temperature: form.temperature,
        model: form.model,
      })
      setJobId(data.job_id)
      setEstTotal(data.estimated_seconds)
      setJobStatus({ pct: 0, message: 'Đang khởi động...', elapsed: 0, status: 'running' })
    } catch (err) {
      toast.error(err.response?.data?.error || 'Lỗi khởi động job')
      setGenLoading(false)
    }
  }

  // ── Generate Quick (30s, chỉ MusicGen) ──
  const handleGenerateQuick = async () => {
    if (!validateComposeForm()) return
    setGenLoading(true)
    setActiveTab('music')
    try {
      const res = await api.post('/ai/generate/music/', {
        genre: form.genre,
        mood: form.mood,
        tempo: form.tempo,
        instruments: form.instruments,
        custom_prompt: form.custom_prompt,
        duration: 30,
        guidance_scale: form.guidance_scale,
        temperature: form.temperature,
        model: form.model,
      }, { responseType: 'blob', timeout: 120000 })

      const blob = new Blob([res.data], { type: 'audio/wav' })
      const audioUrl = URL.createObjectURL(blob)
      const prompt = res.headers['x-prompt'] || promptPreview

      const newTrack = {
        id: Date.now(), audioUrl, prompt, duration: 30,
        genre: form.genre, mood: form.mood, tempo: form.tempo,
        withVocal: false, lyrics: null,
        title: form.title || `${moodInfo?.emoji} ${moodInfo?.label} — ${GENRES.find(g => g.key === form.genre)?.label} (30s)`,
      }
      setTracks(p => [newTrack, ...p])
      api.get('/ai/generate/status/').then(r => setGpuStatus(r.data)).catch(() => { })
      toast.success('🎵 Nhạc 30s đã tạo xong!')
    } catch (err) {
      if (err.code === 'ECONNABORTED') toast.error('Timeout — model đang load, thử lại!')
      else toast.error(err.response?.data?.error || 'Lỗi tạo nhạc')
    }
    setGenLoading(false)
  }

  // ── Generate Lyrics ──
  const handleGenerateLyrics = async () => {
    setLyricsLoading(true)
    setActiveTab('lyrics')
    try {
      const { data } = await api.post('/ai/compose/lyrics/', {
        mood: form.mood, genre: form.genre, title: form.title,
        num_verses: form.num_verses, has_chorus: form.has_chorus,
      })
      setLyrics(data)
      toast.success('✍️ Lời nhạc đã tạo xong!')
    } catch { toast.error('Lỗi tạo lời nhạc') }
    setLyricsLoading(false)
  }

  // ── Generate MIDI ──
  const handleGenerateMidi = async () => {
    setMidiLoading(true)
    setActiveTab('midi')
    try {
      const { data } = await api.post('/ai/compose/preview/', {
        genre: form.genre, mood: form.mood, root_note: 'C',
        num_bars: form.total_duration <= 60 ? 16 : form.total_duration <= 120 ? 32 : 64,
      })
      setMidiPreview(data)
      toast.success('Đã tạo preview MIDI!')
    } catch { toast.error('Lỗi tạo MIDI') }
    setMidiLoading(false)
  }

  const handleDownloadMidi = async () => {
    setDlMidi(true)
    try {
      const res = await api.post('/ai/compose/midi/', {
        genre: form.genre, mood: form.mood, root_note: 'C',
        num_bars: form.total_duration <= 60 ? 16 : form.total_duration <= 120 ? 32 : 64,
      }, { responseType: 'blob' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'audio/midi' }))
      const a = document.createElement('a')
      a.href = url; a.download = `ai_midi_${form.genre}_${form.mood}.mid`; a.click()
      toast.success('Đã tải MIDI!')
    } catch { toast.error('Lỗi tải MIDI') }
    setDlMidi(false)
  }

  const handleSaveToLibrary = async (track) => {
    if (!isAuthenticated) { toast.error('Vui lòng đăng nhập'); return }
    const toastId = toast.loading('Đang lưu vào thư viện...')
    try {
      if (track.audioUrl) {
        const response = await fetch(track.audioUrl)
        const blob = await response.blob()
        const isMp3 = blob.type?.includes('mpeg') || String(track.audioUrl).endsWith('.mp3')
        const ext = isMp3 ? 'mp3' : 'wav'
        const audioFile = new File([blob], `${track.title || 'ai_song'}.${ext}`, {
          type: isMp3 ? 'audio/mpeg' : 'audio/wav',
        })

        const fd = new FormData()
        fd.append('title', track.title || 'AI Song')
        fd.append('genre', track.genre || 'other')
        fd.append('mood', track.mood || '')
        fd.append('duration', track.duration || 0)
        fd.append('lyrics', track.lyrics || '')
        fd.append('description', `🤖 AI Generated\nPrompt: ${track.prompt || ''}`)
        fd.append('is_published', 'true')
        fd.append('audio_file', audioFile)

        await api.post('/music/songs/save-ai/', fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000,
        })
      } else {
        await api.post('/music/songs/', {
          title: track.title, genre: track.genre, mood: track.mood,
          duration: track.duration,
          lyrics: track.lyrics || '',
          description: `🤖 AI Generated\nPrompt: ${track.prompt}`,
          is_published: true,
        })
      }
      toast.dismiss(toastId)
      toast.success('Đã lưu thư viện! 🎉')
    } catch (err) {
      toast.dismiss(toastId)
      toast.error(err.response?.data?.error || 'Lỗi khi lưu')
    }
  }

  // ── Determine generate button config ──
  const isGenerating = genLoading || !!jobId
  const generateFn = mode === 'full' ? handleGenerateFull : handleGenerateQuick
  const durInfo = DURATIONS.find(d => d.seconds === form.total_duration)

  return (
    <div className="flex h-full overflow-hidden animate-fade-in">

      {/* ══ LEFT: Settings ══════════════════════════════════════════════════════ */}
      <div className="w-72 shrink-0 flex flex-col border-r border-white/[0.05] overflow-y-auto scrollbar-thin"
        style={{ background: 'linear-gradient(180deg, #09091e 0%, #080815 100%)' }}>

        {/* Header + Mode switch */}
        <div className="px-4 pt-5 pb-3 border-b border-white/[0.05] shrink-0">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              <MdGraphicEq size={16} className="text-white" />
            </div>
            <div>
              <h1 className="font-black text-white text-sm leading-none">AI Sáng tác</h1>
              <p className="text-[9px] mt-0.5 leading-none" style={{ color: 'rgba(165,180,252,0.45)' }}>
                Sonavia AI · Lyrics · SVS
              </p>
            </div>
          </div>

          {/* Mode switch */}
          <div className="flex gap-1 p-1 rounded-xl border border-white/[0.05]"
            style={{ background: 'rgba(255,255,255,0.03)' }}>
            {[
              { key: 'full', label: '🎤 Full (2-3 phút)', note: 'Sonavia Studio' },
              { key: 'quick', label: '⚡ Nhanh (30s)', note: 'Chỉ nhạc nền' },
            ].map(m => (
              <button key={m.key} onClick={() => setMode(m.key)}
                className={clsx(
                  'flex-1 py-2 rounded-lg text-[10px] font-bold transition-all',
                  mode === m.key
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-white/35 hover:text-white/70'
                )}>
                <div>{m.label}</div>
                <div className={clsx('text-[8px] font-normal mt-0.5', mode === m.key ? 'text-indigo-300' : 'text-white/20')}>{m.note}</div>
              </button>
            ))}
          </div>

          {/* GPU badge */}
          {gpuStatus && (
            <div className="mt-2 flex items-center gap-1.5 text-[9px] px-2 py-1 rounded-lg"
              style={{
                background: gpuStatus.cuda_available ? 'rgba(16,185,129,0.1)' : 'rgba(245,158,11,0.1)',
                border: `1px solid ${gpuStatus.cuda_available ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'}`,
                color: gpuStatus.cuda_available ? '#6ee7b7' : '#fcd34d',
              }}>
              <FiCpu size={9} />
              {gpuStatus.cuda_available
                ? `${gpuStatus.gpu_name?.replace('NVIDIA GeForce ', '')} · ${gpuStatus.vram_total_gb}GB`
                : 'CPU Mode'
              }
              {gpuStatus.model_loaded && <span style={{ color: '#a5b4fc' }} className="ml-1 font-bold">· Ready ✓</span>}
            </div>
          )}
        </div>

        <div className="flex-1 px-3 py-3 space-y-3 overflow-y-auto scrollbar-none">

          {/* Presets */}
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest px-1 mb-1.5"
              style={{ color: 'rgba(165,180,252,0.35)' }}>⚡ Preset nhanh</p>
            <div className="grid grid-cols-2 gap-1">
              {PRESETS.map(p => (
                <button key={p.label} onClick={() => applyPreset(p)}
                  className="text-[10px] px-2 py-1.5 rounded-lg border text-left transition-all"
                  style={{ background: 'rgba(255,255,255,0.03)', borderColor: 'rgba(255,255,255,0.05)', color: 'rgba(255,255,255,0.45)' }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.07)'; e.currentTarget.style.color = 'white' }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'rgba(255,255,255,0.03)'; e.currentTarget.style.color = 'rgba(255,255,255,0.45)' }}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* Mood */}
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest px-1 mb-1.5"
              style={{ color: 'rgba(165,180,252,0.35)' }}>Cảm xúc</p>
            <div className="grid grid-cols-4 gap-1">
              {MOODS.map(m => (
                <button key={m.key} onClick={() => setForm(f => ({ ...f, mood: m.key }))}
                  style={form.mood === m.key
                    ? { borderColor: m.color + '60', background: m.color + '18' }
                    : { borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.02)' }}
                  className={clsx(
                    'flex flex-col items-center gap-0.5 py-2 rounded-xl border text-center transition-all',
                    form.mood === m.key && 'scale-105'
                  )}>
                  <span className="text-sm leading-none">{m.emoji}</span>
                  <span className="text-[8px] font-semibold leading-none mt-0.5"
                    style={{ color: form.mood === m.key ? m.color : 'rgba(255,255,255,0.4)' }}>
                    {m.label}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Genre */}
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest px-1 mb-1.5"
              style={{ color: 'rgba(165,180,252,0.35)' }}>Thể loại</p>
            <div className="flex flex-wrap gap-1">
              {GENRES.map(g => (
                <button key={g.key} onClick={() => setForm(f => ({ ...f, genre: g.key }))}
                  className={clsx(
                    'px-2 py-1 rounded-full text-[10px] font-semibold border transition-all',
                    form.genre === g.key
                      ? 'bg-indigo-600 text-white border-indigo-500'
                      : 'border-white/[0.07] text-white/35 hover:text-white hover:border-white/15'
                  )}>
                  {g.label}
                </button>
              ))}
            </div>
          </div>

          {/* Tempo + Instruments */}
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-[9px] font-bold uppercase tracking-widest px-0.5 mb-1.5"
                style={{ color: 'rgba(165,180,252,0.35)' }}>Tốc độ</p>
              {TEMPOS.map(t => (
                <button key={t.key} onClick={() => setForm(f => ({ ...f, tempo: t.key }))}
                  className={clsx(
                    'w-full flex items-center gap-1.5 px-2 py-1.5 rounded-lg border text-[10px] mb-1 transition-all',
                    form.tempo === t.key
                      ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300'
                      : 'border-white/[0.05] text-white/35 hover:border-white/10 hover:text-white/60'
                  )}>
                  <span>{t.emoji}</span>
                  <div>
                    <p className="font-semibold leading-none">{t.label}</p>
                    <p className="text-[8px] opacity-60">{t.bpm}</p>
                  </div>
                </button>
              ))}
            </div>
            <div>
              <p className="text-[9px] font-bold uppercase tracking-widest px-0.5 mb-1.5"
                style={{ color: 'rgba(165,180,252,0.35)' }}>Nhạc cụ</p>
              {INSTRUMENTS.map(i => (
                <button key={i.key} onClick={() => setForm(f => ({ ...f, instruments: i.key }))}
                  className={clsx(
                    'w-full px-2 py-1.5 rounded-lg border text-[10px] mb-1 transition-all text-left',
                    form.instruments === i.key
                      ? 'border-cyan-500/40 bg-cyan-500/10 text-cyan-300'
                      : 'border-white/[0.05] text-white/35 hover:border-white/10 hover:text-white/60'
                  )}>
                  {i.label}
                </button>
              ))}
            </div>
          </div>

          {/* Full mode — Duration + Voice */}
          {mode === 'full' && (
            <>
              <div>
                <p className="text-[9px] font-bold uppercase tracking-widest px-1 mb-1.5"
                  style={{ color: 'rgba(165,180,252,0.35)' }}>
                  <FiClock size={8} className="inline mr-1" /> Thời lượng
                </p>
                <div className="grid grid-cols-2 gap-1.5">
                  {DURATIONS.map(d => (
                    <button key={d.seconds} onClick={() => setForm(f => ({ ...f, total_duration: d.seconds }))}
                      className={clsx(
                        'px-2.5 py-2 rounded-xl border text-center transition-all',
                        form.total_duration === d.seconds
                          ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300'
                          : 'border-white/[0.06] text-white/35 hover:border-white/12 hover:text-white/60'
                      )}>
                      <p className="text-[11px] font-bold leading-none">{d.label}</p>
                      <p className="text-[8px] mt-0.5 opacity-60">{d.note}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Voice + Vocal toggle */}
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <p className="text-[9px] font-bold uppercase tracking-widest"
                    style={{ color: 'rgba(165,180,252,0.35)' }}>
                    <FiMic size={8} className="inline mr-1" /> Giọng hát AI
                  </p>
                  <button onClick={() => setForm(f => ({ ...f, with_vocal: !f.with_vocal }))}
                    className={clsx(
                      'w-8 h-4 rounded-full transition-all relative shrink-0',
                      form.with_vocal ? 'bg-indigo-600' : 'bg-white/10'
                    )}>
                    <div className={clsx(
                      'absolute top-0.5 w-3 h-3 bg-white rounded-full shadow transition-all',
                      form.with_vocal ? 'left-4.5' : 'left-0.5'
                    )} style={{ left: form.with_vocal ? '18px' : '2px' }} />
                  </button>
                </div>
                {form.with_vocal && (
                  <div className="space-y-1">
                    {VOICES.map(v => (
                      <button key={v.key} onClick={() => setForm(f => ({ ...f, voice: v.key }))}
                        className={clsx(
                          'w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg border text-[10px] transition-all text-left',
                          form.voice === v.key
                            ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300'
                            : 'border-white/[0.05] text-white/35 hover:border-white/10 hover:text-white/60'
                        )}>
                        <div className={`w-1.5 h-1.5 rounded-full ${form.voice === v.key ? 'bg-indigo-400' : 'bg-white/20'}`} />
                        {v.label}
                        {form.voice === v.key && <FiCheck size={9} className="ml-auto text-indigo-400" />}
                      </button>
                    ))}
                    <p className="text-[9px] px-1" style={{ color: 'rgba(165,180,252,0.3)' }}>
                      ⚠️ Cần tạo lời nhạc trước để AI hát
                    </p>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Title */}
          <div>
            <p className="text-[9px] font-bold uppercase tracking-widest px-1 mb-1.5"
              style={{ color: 'rgba(165,180,252,0.35)' }}>Tên bài (tuỳ chọn)</p>
            <input className="input-field text-xs py-2" placeholder="AI sẽ tự đặt tên..."
              value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          </div>

          {/* Advanced */}
          <div className="rounded-xl overflow-hidden border border-white/[0.05]">
            <button onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center justify-between px-3 py-2 text-[9px] font-bold uppercase tracking-widest transition-colors"
              style={{ color: 'rgba(165,180,252,0.35)' }}>
              <span>⚙️ Nâng cao</span>
              {showAdvanced ? <FiChevronUp size={11} /> : <FiChevronDown size={11} />}
            </button>
            {showAdvanced && (
              <div className="px-3 pb-3 space-y-3 border-t border-white/[0.04] pt-3">
                <div>
                  <label className="text-[9px] text-white/30 mb-1 block uppercase tracking-wider">Custom Prompt</label>
                  <textarea className="input-field text-xs resize-none py-2" rows={2}
                    placeholder="VD: night jazz, saxophone, rain..."
                    value={form.custom_prompt}
                    onChange={e => setForm(f => ({ ...f, custom_prompt: e.target.value }))} />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <label className="text-[9px] text-white/30 uppercase tracking-wider">Guidance</label>
                    <span className="text-[9px] font-bold text-indigo-400">{form.guidance_scale.toFixed(1)}</span>
                  </div>
                  <input type="range" min={1} max={10} step={0.5} value={form.guidance_scale}
                    onChange={e => setForm(f => ({ ...f, guidance_scale: parseFloat(e.target.value) }))}
                    className="w-full" style={{ accentColor: '#6366f1' }} />
                </div>
                <div>
                  <div className="flex justify-between mb-1">
                    <label className="text-[9px] text-white/30 uppercase tracking-wider">Temperature</label>
                    <span className="text-[9px] font-bold text-cyan-400">{form.temperature.toFixed(1)}</span>
                  </div>
                  <input type="range" min={0.5} max={2.0} step={0.1} value={form.temperature}
                    onChange={e => setForm(f => ({ ...f, temperature: parseFloat(e.target.value) }))}
                    className="w-full" style={{ accentColor: '#22d3ee' }} />
                </div>
                <div>
                  <label className="text-[9px] text-white/30 uppercase tracking-wider mb-1.5 block">Model</label>
                  {[
                    { id: 'facebook/musicgen-small', name: 'Small (Nhanh ~15s/đoạn)', color: 'emerald' },
                    { id: 'facebook/musicgen-medium', name: 'Medium (Tốt ~30s/đoạn)', color: 'amber' },
                  ].map(m => (
                    <button key={m.id} onClick={() => setForm(f => ({ ...f, model: m.id }))}
                      className={clsx(
                        'w-full flex items-center gap-2 p-2 rounded-lg border mb-1 text-left transition-all',
                        form.model === m.id
                          ? 'border-indigo-500/40 bg-indigo-500/10 text-indigo-300'
                          : 'border-white/[0.05] text-white/35 hover:border-white/10'
                      )}>
                      <div className={`w-1.5 h-1.5 rounded-full bg-${m.color}-400`} />
                      <span className="text-[10px] font-medium">{m.name}</span>
                      {form.model === m.id && <FiCheck size={9} className="ml-auto text-indigo-400" />}
                    </button>
                  ))}
                </div>
                {/* Lyrics config */}
                <div className="border-t border-white/[0.04] pt-2 space-y-2">
                  <label className="text-[9px] text-white/30 uppercase tracking-wider block">Cấu trúc lời</label>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[8px] text-white/25 mb-1 block">Số verse</label>
                      <select className="input-field text-xs py-1.5 cursor-pointer" value={form.num_verses}
                        onChange={e => setForm(f => ({ ...f, num_verses: parseInt(e.target.value) }))}>
                        {[1, 2, 3].map(n => <option key={n} value={n}>{n} verse</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="text-[8px] text-white/25 mb-1 block">Chorus</label>
                      <button onClick={() => setForm(f => ({ ...f, has_chorus: !f.has_chorus }))}
                        className={clsx(
                          'w-full py-1.5 rounded-lg border text-[10px] font-bold transition-all',
                          form.has_chorus
                            ? 'border-indigo-500/40 bg-indigo-500/15 text-indigo-300'
                            : 'border-white/[0.06] text-white/30'
                        )}>
                        {form.has_chorus ? '✅ Có' : '❌ Không'}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ══ CENTER: Main content ═════════════════════════════════════════════ */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Top toolbar */}
        <div className="px-5 pt-4 pb-3 border-b border-white/[0.04] shrink-0"
          style={{ background: 'rgba(8,8,21,0.6)' }}>

          {/* Prompt preview */}
          {promptPreview && (
            <div className="mb-3 px-3 py-2 rounded-xl border border-indigo-500/15"
              style={{ background: 'rgba(99,102,241,0.07)' }}>
              <p className="text-[9px] text-indigo-400 font-bold uppercase tracking-wider mb-0.5">AI Prompt</p>
              <p className="text-[10px] text-white/45 font-mono truncate">{promptPreview}</p>
            </div>
          )}

          {/* 3 Action buttons */}
          <div className="flex gap-2 mb-3">
            {/* Main generate button */}
            <button onClick={generateFn} disabled={isGenerating}
              className="flex-1 flex items-center justify-center gap-2 py-3 rounded-xl font-black text-sm transition-all active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
              style={{
                background: isGenerating
                  ? 'rgba(99,102,241,0.3)'
                  : 'linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #22d3ee 100%)',
                boxShadow: isGenerating ? 'none' : '0 6px 24px rgba(99,102,241,0.4)',
              }}>
              {isGenerating ? (
                <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  {mode === 'full' ? 'Đang sáng tác...' : 'Đang tạo...'}</>
              ) : (
                <><MdGraphicEq size={18} />
                  {mode === 'full'
                    ? `Sáng tác ${durInfo?.label || '3 phút'}`
                    : 'Tạo nhạc 30s (nhanh)'
                  }</>
              )}
            </button>

            {/* Lyrics */}
            <button onClick={handleGenerateLyrics} disabled={lyricsLoading || isGenerating}
              className="flex items-center gap-1.5 px-4 py-3 rounded-xl font-semibold text-sm border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-white/70 hover:text-white transition-all disabled:opacity-50 active:scale-95">
              {lyricsLoading
                ? <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                : <MdLyrics size={15} />
              }
              <span className="hidden sm:inline">Tạo lời</span>
            </button>

            {/* MIDI */}
            <button onClick={handleGenerateMidi} disabled={midiLoading || isGenerating}
              className="flex items-center gap-1.5 px-4 py-3 rounded-xl font-semibold text-sm border border-white/10 bg-white/[0.04] hover:bg-white/[0.08] text-white/70 hover:text-white transition-all disabled:opacity-50 active:scale-95">
              {midiLoading
                ? <span className="w-3.5 h-3.5 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                : <MdPiano size={15} />
              }
              <span className="hidden sm:inline">MIDI</span>
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1">
            {[
              { key: 'music', label: 'Nhạc AI', icon: MdGraphicEq, count: tracks.length },
              { key: 'lyrics', label: 'Lời nhạc', icon: MdLyrics, count: lyrics ? 1 : 0 },
              { key: 'midi', label: 'MIDI', icon: MdPiano, count: midiPreview ? 1 : 0 },
            ].map(({ key, label, icon: Icon, count }) => (
              <button key={key} onClick={() => setActiveTab(key)}
                className={clsx(
                  'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all',
                  activeTab === key
                    ? 'border border-indigo-500/30 text-indigo-300'
                    : 'text-white/35 hover:text-white hover:bg-white/[0.04]'
                )}
                style={activeTab === key ? { background: 'rgba(99,102,241,0.15)' } : {}}>
                <Icon size={13} />
                {label}
                {count > 0 && (
                  <span className="text-[9px] font-black px-1.5 py-0.5 rounded-full"
                    style={{ background: 'rgba(99,102,241,0.3)', color: '#a5b4fc' }}>
                    {count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4">

          {/* ── Tab: Music ── */}
          {activeTab === 'music' && (
            <div className="space-y-4 max-w-2xl">
              {/* Progress panel khi đang generate */}
              {isGenerating && jobStatus && (
                <ProgressPanel
                  pct={jobStatus.pct}
                  message={jobStatus.message}
                  elapsed={jobStatus.elapsed}
                  estimatedTotal={estTotal}
                />
              )}

              {/* Quick generate loading */}
              {isGenerating && !jobStatus && (
                <div className="glass-card p-8 text-center animate-fade-in">
                  <div className="w-16 h-16 mx-auto mb-4 relative">
                    <div className="absolute inset-0 rounded-full border-2 border-indigo-500/20 animate-spin" style={{ animationDuration: '3s' }} />
                    <div className="absolute inset-2 rounded-full border-2 border-cyan-400/30 animate-spin" style={{ animationDuration: '2s', animationDirection: 'reverse' }} />
                    <div className="absolute inset-0 flex items-center justify-center text-2xl">🎵</div>
                  </div>
                  <p className="font-black text-white mb-1">Đang tạo nhạc 30s...</p>
                  <p className="text-sm text-white/40 animate-pulse">MusicGen đang xử lý</p>
                </div>
              )}

              {/* Empty state */}
              {!isGenerating && tracks.length === 0 && (
                <div className="glass-card p-10 text-center">
                  <div className="text-6xl mb-5 animate-float">🎼</div>
                  <h3 className="text-xl font-black text-white mb-2">Sẵn sàng sáng tác!</h3>
                  <p className="text-white/35 text-sm mb-5 leading-relaxed">
                    {mode === 'full'
                      ? <><span className="text-indigo-400 font-bold">Tạo lời nhạc</span> trước, rồi nhấn <span className="text-indigo-400 font-bold">Sáng tác {durInfo?.label}</span></>
                      : <>Nhấn <span className="text-indigo-400 font-bold">Tạo nhạc 30s</span> để thử nhanh</>
                    }
                  </p>

                  {mode === 'full' && form.with_vocal && !lyrics && (
                    <div className="inline-flex items-start gap-2 p-3 rounded-xl text-left max-w-sm"
                      style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}>
                      <FiAlertCircle size={14} className="text-amber-400 shrink-0 mt-0.5" />
                      <p className="text-[11px] text-amber-400 leading-relaxed">
                        Bật giọng hát: Hãy tạo <strong>Lời nhạc</strong> trước để AI có thể thể hiện
                      </p>
                    </div>
                  )}

                  {/* Estimated time */}
                  {mode === 'full' && (
                    <div className="mt-4 grid grid-cols-2 gap-3 max-w-sm mx-auto text-center">
                      {[
                        { icon: '🎹', label: 'Nhạc nền', time: `~${Math.ceil(form.total_duration / 25) * 25}s` },
                        { icon: '🎤', label: 'Giọng hát', time: form.with_vocal ? '~5-15 phút' : 'Tắt' },
                      ].map(s => (
                        <div key={s.label} className="glass-card p-3">
                          <p className="text-xl mb-1">{s.icon}</p>
                          <p className="text-xs font-bold text-white">{s.label}</p>
                          <p className="text-[10px] text-white/35 mt-0.5">{s.time}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tracks */}
              {!isGenerating && tracks.map(t => (
                <TrackCard key={t.id} track={t}
                  onSave={handleSaveToLibrary}
                  onDelete={id => setTracks(p => p.filter(x => x.id !== id))}
                />
              ))}

              {/* Clear all */}
              {!isGenerating && tracks.length > 1 && (
                <button onClick={() => setTracks([])}
                  className="w-full py-2 text-xs text-white/20 hover:text-white/50 flex items-center justify-center gap-1.5 transition-colors">
                  <FiRefreshCw size={11} /> Xóa tất cả bài
                </button>
              )}
            </div>
          )}

          {/* ── Tab: Lyrics ── */}
          {activeTab === 'lyrics' && (
            <div className="max-w-2xl space-y-4">
              {lyricsLoading && (
                <div className="glass-card p-8 text-center">
                  <div className="text-4xl mb-3 animate-bounce">✍️</div>
                  <p className="font-black text-white mb-1">AI đang viết lời...</p>
                  <p className="text-sm text-white/40 animate-pulse">
                    Tạo {form.num_verses} verse{form.has_chorus ? ' + chorus' : ''}
                  </p>
                </div>
              )}

              {!lyricsLoading && !lyrics && (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4 animate-float">✍️</div>
                  <h3 className="text-xl font-black text-white mb-2">Tạo lời bài hát</h3>
                  <p className="text-white/35 text-sm mb-4">AI viết lời tiếng Việt theo mood + thể loại</p>
                  <button onClick={handleGenerateLyrics} className="btn-primary flex items-center gap-2 mx-auto text-sm">
                    <MdLyrics size={15} /> Tạo lời ngay
                  </button>
                </div>
              )}

              {lyrics && (
                <div className="glass-card overflow-hidden animate-slide-up">
                  <div className="px-5 py-4 border-b border-white/[0.05] flex items-center justify-between">
                    <div>
                      <p className="text-[10px] text-white/30 mb-0.5">Lời bài hát AI</p>
                      <h3 className="font-black text-white text-base">{lyrics.title}</h3>
                      <div className="flex gap-2 mt-1">
                        <span className="badge badge-purple text-[9px]">{lyrics.genre}</span>
                        <span className="badge badge-cyan text-[9px]">{lyrics.mood}</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button onClick={handleGenerateLyrics} disabled={lyricsLoading}
                        className="btn-icon w-8 h-8 text-white/40" title="Tạo lại">
                        <FiRefreshCw size={13} />
                      </button>
                      <button onClick={() => {
                        navigator.clipboard.writeText(lyrics.lyrics)
                        setCopiedLyrics(true)
                        setTimeout(() => setCopiedLyrics(false), 2000)
                        toast.success('Đã copy!')
                      }} className="btn-icon w-8 h-8 text-white/40" title="Copy">
                        {copiedLyrics ? <FiCheck size={13} className="text-emerald-400" /> : <FiCopy size={13} />}
                      </button>
                    </div>
                  </div>
                  <div className="p-5">
                    <div className="rounded-2xl p-5 font-mono text-sm leading-8 border border-white/[0.04]"
                      style={{ background: 'rgba(255,255,255,0.02)' }}>
                      {lyrics.lyrics?.split('\n').map((line, i) => {
                        const isSec = line.startsWith('[') && line.endsWith(']')
                        if (!line) return <div key={i} className="h-3" />
                        return (
                          <div key={i} className={isSec
                            ? 'text-indigo-400 font-black text-[10px] uppercase tracking-widest mt-4 mb-1'
                            : 'text-white/70'}>
                            {line}
                          </div>
                        )
                      })}
                    </div>

                    {/* Attach to song button */}
                    {mode === 'full' && form.with_vocal && (
                      <div className="mt-3 p-3 rounded-xl border border-indigo-500/20 flex items-center gap-3"
                        style={{ background: 'rgba(99,102,241,0.07)' }}>
                        <FiMic size={14} className="text-indigo-400 shrink-0" />
                        <div className="flex-1">
                          <p className="text-xs text-indigo-300 font-semibold">Lời đã sẵn sàng</p>
                          <p className="text-[10px] text-white/30 mt-0.5">
                            AI sẽ thể hiện lời này với giọng <strong>{VOICES.find(v => v.key === form.voice)?.label}</strong>
                          </p>
                        </div>
                        <FiCheck size={14} className="text-emerald-400 shrink-0" />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Tab: MIDI ── */}
          {activeTab === 'midi' && (
            <div className="max-w-2xl space-y-4">
              {midiLoading && (
                <div className="glass-card p-8 text-center">
                  <div className="text-4xl mb-3">🎹</div>
                  <p className="font-black text-white">Đang tạo MIDI...</p>
                </div>
              )}

              {!midiLoading && !midiPreview && (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4 animate-float">🎹</div>
                  <h3 className="text-xl font-black text-white mb-2">Tạo file MIDI</h3>
                  <p className="text-white/35 text-sm mb-4">Chord progression + melody, mở được trong DAW</p>
                  <button onClick={handleGenerateMidi} className="btn-primary flex items-center gap-2 mx-auto text-sm">
                    <MdPiano size={15} /> Tạo MIDI
                  </button>
                </div>
              )}

              {midiPreview && (
                <div className="glass-card overflow-hidden animate-slide-up">
                  <div className="h-1" style={{ background: `linear-gradient(to right, ${moodInfo?.color || '#6366f1'}, transparent)` }} />
                  <div className="p-5">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-black text-white flex items-center gap-2">
                        <MdPiano className="text-indigo-400" /> Preview MIDI
                      </h3>
                      <button onClick={handleDownloadMidi} disabled={dlMidi}
                        className="btn-primary flex items-center gap-2 text-sm px-4 py-2">
                        {dlMidi ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <FiDownload size={14} />}
                        Tải .mid
                      </button>
                    </div>

                    <div className="grid grid-cols-3 gap-2 mb-4">
                      {[
                        { k: 'Thể loại', v: midiPreview.genre?.toUpperCase() },
                        { k: 'Giọng', v: `${midiPreview.root_note} ${midiPreview.mode}` },
                        { k: 'Tempo', v: `${midiPreview.bpm} BPM` },
                        { k: 'Ô nhịp', v: midiPreview.num_bars },
                        { k: 'Tâm trạng', v: MOODS.find(m => m.key === midiPreview.mood)?.label },
                        { k: 'Thời lượng', v: `~${midiPreview.estimated_duration_seconds}s` },
                      ].map(({ k, v }) => (
                        <div key={k} className="rounded-xl p-2.5 text-center border border-white/[0.05]"
                          style={{ background: 'rgba(255,255,255,0.04)' }}>
                          <p className="text-[9px] text-white/30 mb-0.5">{k}</p>
                          <p className="text-xs font-black text-white">{v}</p>
                        </div>
                      ))}
                    </div>

                    <div className="mb-4">
                      <p className="text-[9px] font-bold text-white/30 uppercase tracking-wider mb-2">Gamme {midiPreview.mode}</p>
                      <div className="flex gap-1.5 flex-wrap">
                        {midiPreview.scale?.map((n, i) => (
                          <div key={i} className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-black text-indigo-300"
                            style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.25)' }}>
                            {n}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="mb-4">
                      <p className="text-[9px] font-bold text-white/30 uppercase tracking-wider mb-2">Chord Progression</p>
                      <div className="flex items-center gap-2 flex-wrap">
                        {midiPreview.chord_progression?.map((c, i) => (
                          <div key={i} className="flex items-center gap-1.5">
                            <div className="px-3 py-2 rounded-xl text-sm font-black text-white font-mono border border-white/[0.08]"
                              style={{ background: 'rgba(255,255,255,0.06)' }}>{c}</div>
                            {i < midiPreview.chord_progression.length - 1 && (
                              <span className="text-white/20 text-xs">→</span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      {midiPreview.tracks?.map((t, i) => (
                        <div key={i} className="flex items-center gap-2.5 text-xs text-white/50">
                          <div className="w-2 h-2 rounded-full"
                            style={{ background: ['#6366f1', '#22d3ee', '#f97316'][i] }} />
                          {t}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ══ RIGHT: Chatbot ═══════════════════════════════════════════════════ */}
      <div className="w-72 shrink-0 flex flex-col border-l border-white/[0.04]"
        style={{ background: 'linear-gradient(180deg, #09091e 0%, #080815 100%)' }}>
        <ChatbotPanel onApplySuggestion={handleApplyChatSuggestion} />
      </div>
    </div>
  )
}
