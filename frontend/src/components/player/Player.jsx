import { useRef, useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FiPlay, FiPause, FiSkipBack, FiSkipForward,
  FiVolume2, FiVolumeX, FiHeart, FiList, FiX, FiShare2,
} from 'react-icons/fi'
import { MdShuffle, MdRepeat, MdRepeatOne, MdLyrics, MdGraphicEq } from 'react-icons/md'
import usePlayerStore from '../../store/playerStore'
import useAuthStore from '../../store/authStore'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import QueuePanel from './QueuePanel'
import LyricsPanel from './LyricsPanel'
import EqualizerPanel, { EQ_PRESETS } from './EqualizerPanel'
import RealtimeVisualizer from './RealtimeVisualizer'
import ShareModal from '../common/ShareModal'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600', 'from-cyan-600 to-blue-600',
]

function fmtTime(s) {
  if (!s || isNaN(s)) return '0:00'
  return `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`
}

export default function Player() {
  const {
    currentSong, isPlaying, volume, shuffle, repeat,
    togglePlay, playNext, playPrev, setVolume, setCurrentTime,
    toggleShuffle, cycleRepeat, clearPlayer,
  } = usePlayerStore()
  const { isAuthenticated } = useAuthStore()
  const audioRef = useRef(null)
  const [progress, setProgress] = useState(0)
  const [currentSec, setCurrentSec] = useState(0)
  const [duration, setDuration] = useState(0)
  const [muted, setMuted] = useState(false)
  const [liked, setLiked] = useState(false)
  const [showQueue, setShowQueue] = useState(false)
  const [showLyrics, setShowLyrics] = useState(false)
  const [showEQ, setShowEQ] = useState(false)
  const [showShare, setShowShare] = useState(false)
  const [eqPreset, setEqPreset] = useState(() => localStorage.getItem('sonavia_eq_preset') || 'studio')
  const [customEQ, setCustomEQ] = useState({ bass: 3.5, mid: 1.0, treble: 3.0 })

  // Web Audio Context & DSP Filter Nodes & Analyser
  const audioCtxRef = useRef(null)
  const sourceNodeRef = useRef(null)
  const bassFilterRef = useRef(null)
  const midFilterRef = useRef(null)
  const presenceFilterRef = useRef(null)
  const trebleFilterRef = useRef(null)
  const compressorRef = useRef(null)
  const gainNodeRef = useRef(null)
  const analyserRef = useRef(null)

  const applyEQParams = useCallback((bassVal, midVal, presenceVal, trebleVal, gainVal, compActive) => {
    if (bassFilterRef.current) bassFilterRef.current.gain.value = bassVal
    if (midFilterRef.current) midFilterRef.current.gain.value = midVal
    if (presenceFilterRef.current) presenceFilterRef.current.gain.value = presenceVal
    if (trebleFilterRef.current) trebleFilterRef.current.gain.value = trebleVal
    if (gainNodeRef.current) gainNodeRef.current.gain.value = gainVal
    if (compressorRef.current) {
      compressorRef.current.ratio.value = compActive ? 3 : 1
    }
  }, [])

  const setupWebAudio = useCallback(() => {
    if (audioCtxRef.current || !audioRef.current) return
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext
      if (!AudioCtx) return
      const ctx = new AudioCtx()
      const source = ctx.createMediaElementSource(audioRef.current)

      const bass = ctx.createBiquadFilter()
      bass.type = 'lowshelf'
      bass.frequency.value = 85
      bass.gain.value = 3.5

      const mid = ctx.createBiquadFilter()
      mid.type = 'peaking'
      mid.frequency.value = 1200
      mid.Q.value = 0.85
      mid.gain.value = 1.0

      const presence = ctx.createBiquadFilter()
      presence.type = 'peaking'
      presence.frequency.value = 3200
      presence.Q.value = 1.0
      presence.gain.value = 2.5

      const treble = ctx.createBiquadFilter()
      treble.type = 'highshelf'
      treble.frequency.value = 11500
      treble.gain.value = 3.0

      const comp = ctx.createDynamicsCompressor()
      comp.threshold.value = -20
      comp.knee.value = 12
      comp.ratio.value = 3
      comp.attack.value = 0.005
      comp.release.value = 0.25

      const gain = ctx.createGain()
      gain.gain.value = 1.05

      // AnalyserNode cho sóng âm thanh realtime Web Audio API
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 64
      analyser.smoothingTimeConstant = 0.8

      source.connect(bass)
      bass.connect(mid)
      mid.connect(presence)
      presence.connect(treble)
      treble.connect(comp)
      comp.connect(gain)
      gain.connect(analyser)
      analyser.connect(ctx.destination)

      audioCtxRef.current = ctx
      sourceNodeRef.current = source
      bassFilterRef.current = bass
      midFilterRef.current = mid
      presenceFilterRef.current = presence
      trebleFilterRef.current = treble
      compressorRef.current = comp
      gainNodeRef.current = gain
      analyserRef.current = analyser

      // Apply initial saved preset
      const saved = localStorage.getItem('sonavia_eq_preset') || 'studio'
      const p = EQ_PRESETS[saved] || EQ_PRESETS.studio
      bass.gain.value = p.bass
      mid.gain.value = p.mid
      presence.gain.value = p.presence
      treble.gain.value = p.treble
      gain.gain.value = p.gain
      comp.ratio.value = p.compressor ? 3 : 1
    } catch (e) {
      console.warn('[WebAudio] Không thể khởi tạo DSP Engine:', e)
    }
  }, [])

  const handleSelectPreset = (presetId) => {
    setEqPreset(presetId)
    localStorage.setItem('sonavia_eq_preset', presetId)
    const p = EQ_PRESETS[presetId] || EQ_PRESETS.studio
    setCustomEQ({ bass: p.bass, mid: p.mid, treble: p.treble })
    applyEQParams(p.bass, p.mid, p.presence, p.treble, p.gain, p.compressor)
  }

  const handleChangeCustom = (band, val) => {
    setEqPreset('custom')
    const updated = { ...customEQ, [band]: val }
    setCustomEQ(updated)
    applyEQParams(
      updated.bass,
      updated.mid,
      updated.mid * 1.5,
      updated.treble,
      1.05,
      true
    )
  }

  const audioSrc = currentSong?.audio_file_url || currentSong?.audio_url || currentSong?.audioUrl || ''
  const grad = COVER_GRADIENTS[(currentSong?.id || 0) % COVER_GRADIENTS.length]

  const playingRef = useRef(false)
  const playCountedRef = useRef(null)

  const reportPlay = useCallback(async (songId) => {
    if (playCountedRef.current === songId) return
    playCountedRef.current = songId
    try {
      await api.post(`/music/songs/${songId}/play/`)
    } catch { /* silent */ }
  }, [])

  const handlePrev = useCallback(() => {
    const audio = audioRef.current
    if (audio && audio.currentTime > 3) {
      audio.currentTime = 0
      setProgress(0)
      setCurrentSec(0)
    } else {
      playPrev()
    }
  }, [playPrev])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const safePlay = () => {
      audio.play()
        .then(() => {
          playingRef.current = true
          if (currentSong?.id) reportPlay(currentSong.id)
        })
        .catch(() => {
          playingRef.current = false
        })
    }

    setDuration(0)
    setProgress(0)
    setCurrentSec(0)
    playingRef.current = false
    setLiked(currentSong?.is_liked || false)

    if (audioSrc) {
      if (audio.getAttribute('src') !== audioSrc) {
        audio.src = audioSrc
      }
      audio.currentTime = 0
      if (isPlaying) {
        if (audio.readyState >= 1) {
          safePlay()
        }
      }
    }
  }, [currentSong, audioSrc, isPlaying, reportPlay])

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return
    if (isPlaying) {
      if (!playingRef.current && audio.readyState >= 1) {
        audio.play()
          .then(() => {
            playingRef.current = true
            if (currentSong?.id) reportPlay(currentSong.id)
          })
          .catch(() => { playingRef.current = false })
      }
    } else {
      audio.pause()
      playingRef.current = false
    }
  }, [isPlaying, currentSong, reportPlay])

  const handleEnded = () => {
    if (repeat === 'one') {
      const audio = audioRef.current
      if (audio) { audio.currentTime = 0; audio.play().catch(() => { }) }
    } else {
      playNext()
    }
  }

  useEffect(() => {
    if (audioRef.current) audioRef.current.volume = muted ? 0 : volume
  }, [volume, muted])

  if (!currentSong) return null

  const handleTimeUpdate = () => {
    const a = audioRef.current
    if (!a?.duration) return
    setCurrentSec(a.currentTime)
    setProgress((a.currentTime / a.duration) * 100)
    setCurrentTime(a.currentTime)
  }

  const handleLike = async () => {
    if (!isAuthenticated) return
    try {
      const { data } = await api.post(`/social/songs/${currentSong.id}/like/`)
      setLiked(data.liked)
    } catch { }
  }

  const RepeatIcon = repeat === 'one' ? MdRepeatOne : MdRepeat

  return (
    /* ── Floating Capsule Container (Nổi cách đáy màn hình 16px) ── */
    <div className="fixed bottom-3 sm:bottom-5 left-3 sm:left-6 right-3 sm:right-6 z-50 select-none max-w-6xl mx-auto pointer-events-none">
      
      {/* ── Ambient Aura Backlight (Vầng hào quang cực quang đổi màu tỏa sáng) ── */}
      <div className={clsx(
        "aurora-ambient-glow transition-all duration-700",
        isPlaying ? "opacity-95 scale-100" : "opacity-35 scale-95"
      )} />

      {/* ── Main Capsule Body ── */}
      <div className="relative pointer-events-auto rounded-2xl sm:rounded-3xl sonavia-player-capsule overflow-hidden">
        {showLyrics && <LyricsPanel onClose={() => setShowLyrics(false)} />}
        {showQueue && <QueuePanel onClose={() => setShowQueue(false)} />}
        {showEQ && (
          <EqualizerPanel
            onClose={() => setShowEQ(false)}
            currentPreset={eqPreset}
            onSelectPreset={handleSelectPreset}
            customSettings={customEQ}
            onChangeCustom={handleChangeCustom}
          />
        )}
        {showShare && (
          <ShareModal
            isOpen={showShare}
            onClose={() => setShowShare(false)}
            song={currentSong}
          />
        )}

        <audio
          ref={audioRef}
          src={audioSrc || undefined}
          crossOrigin="anonymous"
          onPlay={() => {
            setupWebAudio()
            if (audioCtxRef.current?.state === 'suspended') {
              audioCtxRef.current.resume().catch(() => {})
            }
          }}
          onEnded={handleEnded}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
          onCanPlay={() => {
            if (isPlaying && !playingRef.current) {
              audioRef.current?.play().then(() => {
                playingRef.current = true
                if (currentSong?.id) reportPlay(currentSong.id)
              }).catch(() => {
                playingRef.current = false
              })
            }
          }}
          onError={(e) => {
            const audio = audioRef.current
            if (audio && audio.getAttribute('crossOrigin')) {
              console.warn('[Global Player] Thử fallback phát trực tiếp bỏ crossOrigin...')
              audio.removeAttribute('crossOrigin')
              audio.load()
              if (isPlaying) {
                audio.play().then(() => {
                  playingRef.current = true
                }).catch(() => {
                  usePlayerStore.setState({ isPlaying: false })
                  playingRef.current = false
                })
              }
              return
            }
            console.error('[Global Player Audio Error]', {
              songId: currentSong?.id,
              audioSrc,
              error: audioRef.current?.error ? { code: audioRef.current.error.code, message: audioRef.current.error.message } : e,
            })
            usePlayerStore.setState({ isPlaying: false })
            playingRef.current = false
            toast.error('Không thể phát âm thanh bài hát này. Vui lòng thử lại hoặc chọn bài khác.', { id: 'player-audio-error' })
          }}
          preload="auto"
          playsInline
        />

        {/* Interactive Glowing Seek Progress Line at Top */}
        <div
          className="h-1 w-full bg-white/[0.08] hover:h-1.5 cursor-pointer group/bar transition-all relative"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect()
            const pct = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100))
            if (audioRef.current?.duration) {
              audioRef.current.currentTime = (pct / 100) * audioRef.current.duration
              setProgress(pct)
            }
          }}>
          <div
            className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 relative transition-all duration-75 shadow-[0_0_12px_#22d3ee]"
            style={{ width: `${progress}%` }}>
            <div className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 bg-white rounded-full shadow-[0_0_8px_#ffffff] opacity-0 group-hover/bar:opacity-100 transition-opacity" />
          </div>
        </div>

        <div className="flex items-center justify-between gap-2 sm:gap-4 px-3.5 sm:px-6 py-2 sm:py-2.5">

          {/* ── Left: Vinyl Disc + Song Info ── */}
          <div className="flex items-center gap-2.5 sm:gap-4 sm:w-72 min-w-0 max-w-[42%] sm:max-w-none">
            {/* Spinning Vinyl Disc Record Effect */}
            <div className="relative w-10 h-10 sm:w-12 sm:h-12 shrink-0 flex items-center justify-center">
              <div
                className={clsx(
                  "w-10 h-10 sm:w-12 sm:h-12 rounded-full vinyl-ring overflow-hidden transition-all duration-500",
                  isPlaying ? "animate-spin-slow shadow-[0_0_18px_rgba(34,211,238,0.45)]" : "animate-spin-slow-paused"
                )}
              >
                {currentSong.cover_image_url ? (
                  <img
                    src={currentSong.cover_image_url}
                    alt={currentSong.title}
                    className="w-full h-full object-cover rounded-full"
                  />
                ) : (
                  <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-sm rounded-full`}>
                    🎵
                  </div>
                )}
                {/* Lỗ tâm đĩa than */}
                <div className="vinyl-center-hole" />
              </div>

              {/* Realtime Audio Wave Visualizer khi đang phát */}
              {isPlaying && (
                <div className="absolute -bottom-1 -right-1 flex items-center justify-center bg-black/90 backdrop-blur-md border border-cyan-400/40 rounded-full px-1 py-0.5 shadow-md">
                  <RealtimeVisualizer analyserRef={analyserRef} isPlaying={isPlaying} barCount={5} height={12} width={20} />
                </div>
              )}
            </div>

            <div className="min-w-0 flex-1">
              <Link
                to={`/songs/${currentSong.id}`}
                className="text-xs sm:text-sm font-bold text-white hover:text-cyan-300 transition-colors truncate block">
                {currentSong.title}
              </Link>
              <Link
                to={`/profile/${currentSong.artist?.username}`}
                className="text-[10px] sm:text-xs text-white/50 hover:text-white/80 truncate block transition-colors mt-0.5">
                {currentSong.artist?.username || 'Sonavia AI'}
              </Link>
            </div>

            <button
              onClick={handleLike}
              className={clsx(
                'shrink-0 p-1.5 rounded-lg transition-all hidden xs:block',
                liked ? 'text-rose-400 bg-rose-500/10' : 'text-white/30 hover:text-white hover:bg-white/[0.05]'
              )}
              title="Thích bài hát">
              <FiHeart size={14} className={liked ? 'fill-current' : ''} />
            </button>
          </div>

          {/* ── Middle: Player Controls & Visualizer ── */}
          <div className="flex-1 max-w-lg flex flex-col items-center gap-0.5 sm:gap-1">
            <div className="flex items-center gap-3 sm:gap-5">
              {/* Shuffle */}
              <button
                onClick={toggleShuffle}
                title={shuffle ? 'Tắt phát ngẫu nhiên' : 'Bật phát ngẫu nhiên'}
                className={clsx(
                  'transition-colors hidden md:block',
                  shuffle ? 'text-cyan-400 drop-shadow-[0_0_6px_#22d3ee]' : 'text-white/35 hover:text-white'
                )}>
                <MdShuffle size={17} />
              </button>

              {/* Prev */}
              <button
                onClick={handlePrev}
                title="Bài trước"
                className="text-white/65 hover:text-white transition-transform active:scale-90">
                <FiSkipBack size={18} />
              </button>

              {/* Main Play / Pause Button with Shimmer Aurora Effect */}
              <button
                onClick={togglePlay}
                title={isPlaying ? 'Tạm dừng' : 'Phát'}
                className="w-9 h-9 sm:w-10 sm:h-10 rounded-full flex items-center justify-center transition-all duration-200 shadow-[0_0_22px_rgba(99,102,241,0.55)] active:scale-95 hover:scale-105 btn-shimmer"
                style={{
                  background: 'linear-gradient(135deg, #ffffff 0%, #e0e7ff 100%)',
                  color: '#060713',
                }}>
                {isPlaying ? (
                  <FiPause size={17} className="fill-current" />
                ) : (
                  <FiPlay size={17} className="fill-current ml-0.5" />
                )}
              </button>

              {/* Next */}
              <button
                onClick={playNext}
                title="Bài kế tiếp"
                className="text-white/65 hover:text-white transition-transform active:scale-90">
                <FiSkipForward size={18} />
              </button>

              {/* Repeat */}
              <button
                onClick={cycleRepeat}
                title={repeat === 'none' ? 'Lặp lại tất cả' : repeat === 'all' ? 'Lặp lại 1 bài' : 'Tắt lặp lại'}
                className={clsx(
                  'transition-colors hidden md:block',
                  repeat !== 'none' ? 'text-cyan-400 drop-shadow-[0_0_6px_#22d3ee]' : 'text-white/35 hover:text-white'
                )}>
                <RepeatIcon size={17} />
              </button>
            </div>

            {/* Time scrubber with Realtime Audio Spectrum */}
            <div className="flex items-center gap-2 sm:gap-3 w-full">
              <span className="text-[10px] sm:text-[11px] text-white/35 tabular-nums w-7 sm:w-8 text-right font-mono">
                {fmtTime(currentSec)}
              </span>
              <div
                className="flex-1 relative h-1 bg-white/[0.08] rounded-full group/seek cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect()
                  const pct = ((e.clientX - rect.left) / rect.width) * 100
                  if (audioRef.current?.duration) {
                    audioRef.current.currentTime = (pct / 100) * audioRef.current.duration
                    setProgress(pct)
                  }
                }}>
                <div
                  className="h-full bg-gradient-to-r from-indigo-400 to-cyan-400 rounded-full transition-all"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <span className="text-[10px] sm:text-[11px] text-white/35 tabular-nums w-7 sm:w-8 font-mono">
                {fmtTime(duration)}
              </span>

              {/* Mini Spectrum Visualizer next to time */}
              <div className="hidden lg:flex items-center pl-1">
                <RealtimeVisualizer analyserRef={analyserRef} isPlaying={isPlaying} barCount={8} height={14} width={38} />
              </div>
            </div>
          </div>

          {/* ── Right: Share, EQ, Lyrics, Queue, Volume ── */}
          <div className="flex items-center gap-1.5 sm:gap-2 sm:w-72 justify-end shrink-0">
            {/* Nút Chia Sẻ (Social Share) */}
            <button
              onClick={() => setShowShare(true)}
              className="p-1.5 sm:p-2 rounded-xl text-white/40 hover:text-cyan-300 hover:bg-white/[0.05] transition-all"
              title="Chia sẻ bài hát">
              <FiShare2 size={16} />
            </button>

            {/* Nút Bộ Tối Ưu Âm Thanh HD (Equalizer) */}
            <button
              onClick={() => {
                setShowEQ(!showEQ)
                if (!showEQ) {
                  setShowLyrics(false)
                  setShowQueue(false)
                  setupWebAudio()
                }
              }}
              className={clsx(
                'p-1.5 sm:p-2 rounded-xl transition-all relative',
                showEQ
                  ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 text-cyan-300 drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]'
                  : eqPreset !== 'flat'
                    ? 'text-cyan-400 bg-cyan-500/10 hover:bg-cyan-500/20'
                    : 'text-white/40 hover:text-white hover:bg-white/[0.05]'
              )}
              title="Bộ Tối Ưu Âm Thanh HD (Equalizer)">
              <MdGraphicEq size={18} />
              {eqPreset !== 'flat' && (
                <span className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_6px_#22d3ee]" />
              )}
            </button>

            {/* Nút Xem Lời Bài Hát (Synced Karaoke Lyrics) */}
            <button
              onClick={() => {
                setShowLyrics(!showLyrics)
                if (!showLyrics) {
                  setShowQueue(false)
                  setShowEQ(false)
                }
              }}
              className={clsx(
                'p-1.5 sm:p-2 rounded-xl transition-all',
                showLyrics
                  ? 'bg-cyan-500/20 text-cyan-300 drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]'
                  : 'text-white/40 hover:text-white hover:bg-white/[0.05]'
              )}
              title="Lời bài hát Karaoke (Lyrics)">
              <MdLyrics size={17} />
            </button>

            <button
              onClick={() => {
                setShowQueue(!showQueue)
                if (!showQueue) setShowLyrics(false)
              }}
              className={clsx(
                'p-1.5 sm:p-2 rounded-xl transition-all',
                showQueue ? 'bg-indigo-500/20 text-cyan-300' : 'text-white/40 hover:text-white hover:bg-white/[0.05]'
              )}
              title="Danh sách chờ phát">
              <FiList size={16} />
            </button>

            <div className="hidden sm:flex items-center gap-2">
              <button
                onClick={() => setMuted(!muted)}
                className="text-white/40 hover:text-white transition-colors"
                title={muted ? 'Bật âm' : 'Tắt tiếng'}>
                {muted || volume === 0 ? <FiVolumeX size={17} /> : <FiVolume2 size={17} />}
              </button>

              <div
                className="w-16 md:w-20 relative h-1 bg-white/[0.08] rounded-full group/vol cursor-pointer"
                onClick={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect()
                  const vol = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
                  setMuted(false)
                  setVolume(vol)
                }}>
                <div
                  className="h-full bg-gradient-to-r from-indigo-400 to-cyan-400 rounded-full"
                  style={{ width: `${(muted ? 0 : volume) * 100}%` }}
                />
              </div>
            </div>

            {/* Close player button */}
            <button
              onClick={() => { audioRef.current?.pause(); clearPlayer() }}
              className="p-1.5 sm:p-2 rounded-xl text-white/30 hover:text-white hover:bg-white/[0.05] transition-all ml-1"
              title="Đóng player"
            >
              <FiX size={16} />
            </button>
          </div>

        </div>
      </div>
    </div>
  )
}
