import { useState, useMemo, useEffect, useRef } from 'react'
import { FiX, FiCopy, FiCheck, FiMusic, FiPlayCircle } from 'react-icons/fi'
import { MdLyrics, MdOutlineAutoAwesome } from 'react-icons/md'
import usePlayerStore from '../../store/playerStore'
import clsx from 'clsx'

const SECTION_COLORS = {
  intro: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  verse: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  chorus: 'bg-amber-500/15 text-amber-300 border-amber-500/30 font-semibold',
  bridge: 'bg-fuchsia-500/15 text-fuchsia-300 border-fuchsia-500/30',
  outro: 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30',
  hook: 'bg-rose-500/15 text-rose-300 border-rose-500/30 font-semibold',
}

function getSectionBadgeClass(tag) {
  const clean = tag.toLowerCase()
  for (const [key, cls] of Object.entries(SECTION_COLORS)) {
    if (clean.includes(key)) return cls
  }
  return 'bg-white/10 text-white/70 border-white/15'
}

function formatTime(sec) {
  if (!Number.isFinite(sec)) return '0:00'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s < 10 ? '0' : ''}${s}`
}

export default function LyricsPanel({ onClose }) {
  const { currentSong, currentTime, isPlaying } = usePlayerStore()
  const [copied, setCopied] = useState(false)
  const [autoScroll, setAutoScroll] = useState(true)
  const [syncMode, setSyncMode] = useState(true) // Karaoke sync vs Full text
  const listContainerRef = useRef(null)
  const activeLineRef = useRef(null)

  const rawLyrics = currentSong?.lyrics || ''
  const songDuration = currentSong?.duration || 180

  // ── Parse Lyrics (Hỗ trợ file LRC chuẩn [mm:ss.xx] & Phân bổ nhịp thông minh) ──
  const parsedLines = useMemo(() => {
    if (!rawLyrics.trim()) return []

    const rawList = rawLyrics.split('\n').map(l => l.trim())
    const lrcRegex = /^\[(\d{1,2}):(\d{2})(?:[.:](\d{1,3}))?\](.*)$/

    // Kiểm tra xem bài hát có chứa timestamp LRC không
    const hasTimestamps = rawList.some(line => lrcRegex.test(line))

    if (hasTimestamps) {
      const items = []
      for (const line of rawList) {
        if (!line) continue
        const match = line.match(lrcRegex)
        if (match) {
          const minutes = parseInt(match[1], 10)
          const seconds = parseInt(match[2], 10)
          const millis = match[3] ? parseInt(match[3].padEnd(3, '0').slice(0, 3), 10) : 0
          const time = minutes * 60 + seconds + millis / 1000
          const text = match[4].trim()
          if (text) {
            items.push({
              time,
              text,
              isSection: text.startsWith('[') && text.endsWith(']'),
              hasExactTime: true,
            })
          }
        } else if (line.startsWith('[') && line.endsWith(']')) {
          items.push({
            time: items.length > 0 ? items[items.length - 1].time : 0,
            text: line,
            isSection: true,
            hasExactTime: false,
          })
        }
      }
      return items.sort((a, b) => a.time - b.time)
    }

    // ── Fallback Tự Động Phân Bổ Nhịp Điệu (Auto-Pacing Pacer) ──
    // Nếu lời bài hát dạng văn bản thường, phân bổ thời gian đều dựa trên thời lượng bài hát
    const textLines = []
    for (const line of rawList) {
      if (!line) continue
      const isSection = line.startsWith('[') && line.endsWith(']')
      textLines.push({ text: line, isSection })
    }

    const lyricalCount = textLines.filter(item => !item.isSection).length
    if (lyricalCount === 0) return []

    // Dự trù 6s dạo đầu (intro) và 6s kết thúc (outro)
    const introOffset = 6
    const usableDuration = Math.max(10, songDuration - 12)
    const step = usableDuration / Math.max(1, lyricalCount)

    let lyricIndex = 0
    return textLines.map(item => {
      if (item.isSection) {
        return {
          time: Math.max(0, introOffset + lyricIndex * step - 2),
          text: item.text,
          isSection: true,
          hasExactTime: false,
        }
      }
      const time = introOffset + lyricIndex * step
      lyricIndex++
      return {
        time,
        text: item.text,
        isSection: false,
        hasExactTime: false,
      }
    })
  }, [rawLyrics, songDuration])

  // ── Xác định dòng đang hát (Active Line Index) ──
  const activeIndex = useMemo(() => {
    if (!parsedLines.length) return -1
    let best = -1
    for (let i = 0; i < parsedLines.length; i++) {
      if (currentTime >= parsedLines[i].time) {
        best = i
      } else {
        break
      }
    }
    return best
  }, [parsedLines, currentTime])

  // ── Tự động cuộn theo nhịp hát ──
  useEffect(() => {
    if (!autoScroll || activeIndex < 0 || !activeLineRef.current || !syncMode) return
    activeLineRef.current.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
    })
  }, [activeIndex, autoScroll, syncMode])

  // ── Click để tua nhạc tới dòng đó ──
  const handleSeekToLine = (time) => {
    const audio = document.querySelector('audio')
    if (audio && Number.isFinite(time)) {
      audio.currentTime = Math.max(0, time)
      usePlayerStore.getState().setCurrentTime(time)
    }
  }

  const handleCopy = () => {
    if (!rawLyrics.trim()) return
    navigator.clipboard.writeText(rawLyrics)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const artistName = typeof currentSong?.artist === 'object'
    ? (currentSong?.artist?.username || 'Sonavia AI')
    : (currentSong?.artist || 'Sonavia AI')

  return (
    <div
      className="fixed bottom-20 right-3 sm:right-6 z-40 w-96 sm:w-[460px] max-w-[calc(100vw-1.5rem)] h-[540px] max-h-[75vh] flex flex-col shadow-2xl animate-slide-up rounded-3xl overflow-hidden border border-white/10"
      style={{
        background: 'linear-gradient(180deg, rgba(14, 15, 34, 0.98) 0%, rgba(9, 10, 22, 0.98) 100%)',
        backdropFilter: 'blur(30px)',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 45px rgba(99, 102, 241, 0.15)',
      }}
    >
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.08] bg-white/[0.02]">
        <div className="flex items-center gap-2.5 min-w-0 pr-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20">
            <MdLyrics size={16} className="text-white" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-1.5">
              <h3 className="text-sm font-bold text-white truncate leading-tight">
                {currentSong?.title || 'Bài hát đang phát'}
              </h3>
              {syncMode && (
                <span className="shrink-0 px-1.5 py-0.2 rounded-full text-[9px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
                  Live Sync
                </span>
              )}
            </div>
            <p className="text-[11px] text-white/40 truncate">
              {artistName}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {/* Nút Toggle Chế độ Karaoke Sync / Toàn văn bản */}
          <button
            onClick={() => setSyncMode(!syncMode)}
            title={syncMode ? "Chuyển sang xem toàn văn bản" : "Bật đồng bộ Karaoke theo nhạc"}
            className={clsx(
              "p-1.5 sm:px-2.5 sm:py-1 rounded-xl text-xs font-medium transition-all flex items-center gap-1 border",
              syncMode
                ? "bg-cyan-500/15 text-cyan-300 border-cyan-500/30 shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                : "bg-white/[0.04] text-white/50 border-white/10 hover:text-white"
            )}
          >
            <MdOutlineAutoAwesome size={13} />
            <span className="hidden sm:inline">{syncMode ? 'Karaoke' : 'Văn bản'}</span>
          </button>

          {rawLyrics.trim() && (
            <button
              onClick={handleCopy}
              title="Sao chép toàn bộ lời"
              className="p-2 rounded-xl text-white/50 hover:text-white hover:bg-white/[0.08] transition-all flex items-center gap-1 text-xs"
            >
              {copied ? (
                <>
                  <FiCheck size={14} className="text-emerald-400" />
                  <span className="text-[11px] text-emerald-400 font-medium">Đã chép</span>
                </>
              ) : (
                <FiCopy size={14} />
              )}
            </button>
          )}

          <button
            onClick={onClose}
            title="Đóng lời bài hát"
            className="p-2 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.08] transition-all ml-1"
          >
            <FiX size={17} />
          </button>
        </div>
      </div>

      {/* ── Content: Synced Lyrics Body ── */}
      <div
        ref={listContainerRef}
        onWheel={() => {
          // Tạm ngừng auto scroll nếu người dùng chủ động cuộn tay trong 4 giây
          setAutoScroll(false)
          clearTimeout(window.__lyricsScrollTimeout)
          window.__lyricsScrollTimeout = setTimeout(() => setAutoScroll(true), 4000)
        }}
        className="flex-1 overflow-y-auto px-6 py-6 space-y-4 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent select-text"
      >
        {parsedLines.length > 0 ? (
          parsedLines.map((item, idx) => {
            const isActive = syncMode && idx === activeIndex
            const isPast = syncMode && activeIndex >= 0 && idx < activeIndex

            if (item.isSection) {
              return (
                <div key={idx} className="pt-3 pb-1">
                  <span
                    className={clsx(
                      'inline-block px-2.5 py-0.5 text-[11px] uppercase tracking-wider rounded-lg border shadow-sm transition-all',
                      getSectionBadgeClass(item.text),
                      isActive && 'ring-2 ring-cyan-400/50 scale-105'
                    )}
                  >
                    {item.text.replace(/[\[\]]/g, '')}
                  </span>
                </div>
              )
            }

            return (
              <div
                key={idx}
                ref={isActive ? activeLineRef : null}
                onClick={() => handleSeekToLine(item.time)}
                className={clsx(
                  "group relative cursor-pointer rounded-xl px-3 py-2 transition-all duration-300 flex items-center justify-between gap-3",
                  isActive
                    ? "bg-gradient-to-r from-cyan-500/20 via-indigo-500/15 to-transparent border-l-4 border-cyan-400 pl-3 scale-[1.02]"
                    : "hover:bg-white/[0.04] opacity-80 hover:opacity-100"
                )}
              >
                {/* Dòng chữ bài hát */}
                <p
                  className={clsx(
                    "transition-all duration-300 leading-relaxed",
                    isActive
                      ? "text-lg sm:text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 via-white to-indigo-200 drop-shadow-[0_0_15px_rgba(34,211,238,0.7)]"
                      : isPast
                        ? "text-[14px] sm:text-[15px] text-white/55 font-normal"
                        : "text-[14px] sm:text-[15px] text-white/35 font-normal group-hover:text-white/70"
                  )}
                >
                  {item.text}
                </p>

                {/* Badge thời gian & nút bấm tua khi hover */}
                <div className="shrink-0 flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                  <span className="text-[10px] font-mono text-cyan-300/70 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-500/30">
                    {formatTime(item.time)}
                  </span>
                  <FiPlayCircle size={15} className="text-cyan-400" />
                </div>
              </div>
            )
          })
        ) : (
          <div className="h-full flex flex-col items-center justify-center text-center px-4 py-12 space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-white/[0.04] border border-white/10 flex items-center justify-center text-white/30">
              <FiMusic size={26} />
            </div>
            <p className="text-sm font-medium text-white/70">
              Chưa có lời cho bài hát này
            </p>
            <p className="text-xs text-white/40 max-w-[260px] leading-relaxed">
              Bản nhạc này có thể là nhạc không lời (Instrumental) hoặc chưa được cập nhật lời ca.
            </p>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      {parsedLines.length > 0 && (
        <div className="px-5 py-2.5 bg-white/[0.02] border-t border-white/[0.05] flex items-center justify-between text-[11px] text-white/40">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span>Click bất kỳ dòng nào để tua nhạc</span>
          </div>
          <span>{parsedLines.filter(l => !l.isSection).length} câu hát</span>
        </div>
      )}
    </div>
  )
}
