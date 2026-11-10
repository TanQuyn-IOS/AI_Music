import { useState } from 'react'
import { FiX, FiClock, FiMusic, FiCheck } from 'react-icons/fi'
import { MdAutoAwesome, MdGraphicEq } from 'react-icons/md'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import usePlayerStore from '../../store/playerStore'

export default function ExtendModal({ isOpen, onClose, song, onExtended }) {
  const [duration, setDuration] = useState(60)
  const [prompt, setPrompt] = useState('')
  const [additionalLyrics, setAdditionalLyrics] = useState('')
  const [loading, setLoading] = useState(false)
  const { playSong } = usePlayerStore()

  if (!isOpen || !song) return null

  const handleExtend = async (e) => {
    e?.preventDefault()
    setLoading(true)

    try {
      const res = await api.post(`/music/songs/${song.id}/extend/`, {
        duration,
        prompt: prompt.trim(),
        additional_lyrics: additionalLyrics.trim(),
      })

      const extendedSong = res.data
      toast.success(`Đã mở rộng thành công bài hát: "${extendedSong.title}"!`)
      if (onExtended) {
        onExtended(extendedSong)
      }
      // Tự động phát bài hát mở rộng mới tạo
      playSong(extendedSong, [extendedSong])
      onClose()
    } catch (err) {
      console.error('[Extend Song Error]', err)
      const msg = err.response?.data?.error || err.message || 'Không thể mở rộng bài hát.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/75 backdrop-blur-md transition-opacity animate-fade-in"
        onClick={!loading ? onClose : undefined}
      />

      {/* Modal Dialog */}
      <div
        className="relative z-10 w-full max-w-lg rounded-3xl overflow-hidden border border-white/10 shadow-2xl animate-scale-in"
        style={{
          background: 'linear-gradient(180deg, rgba(16, 17, 40, 0.98) 0%, rgba(8, 9, 22, 0.98) 100%)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 50px rgba(99, 102, 241, 0.2)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-400 via-indigo-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-cyan-500/20 text-white">
              <MdAutoAwesome size={17} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">
                Mở rộng Bài hát AI (Inpainting & Extend)
              </h3>
              <p className="text-[11px] text-white/40">
                Sáng tác tiếp 30s - 60s đồng điệu hòa âm liền mạch
              </p>
            </div>
          </div>
          {!loading && (
            <button
              onClick={onClose}
              className="p-1.5 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.08] transition-colors"
            >
              <FiX size={18} />
            </button>
          )}
        </div>

        {/* Content Form */}
        <form onSubmit={handleExtend} className="p-6 space-y-4">
          {/* Target Song Info */}
          <div className="flex items-center gap-3 p-3 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-500 flex items-center justify-center text-lg overflow-hidden shrink-0">
              {song.cover_image_url ? (
                <img src={song.cover_image_url} alt={song.title} className="w-full h-full object-cover" />
              ) : (
                '🎵'
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h4 className="text-xs font-bold text-white truncate">{song.title}</h4>
              <p className="text-[11px] text-white/40 truncate">
                Hiện tại: {Math.floor(song.duration / 60)}:{String(song.duration % 60).padStart(2, '0')} • Thể loại: {song.genre} • Vibe: {song.mood || 'AI Sound'}
              </p>
            </div>
          </div>

          {/* Extension Duration Selector */}
          <div>
            <label className="text-xs font-semibold text-white/70 block mb-2">
              Thời lượng mở rộng thêm
            </label>
            <div className="grid grid-cols-3 gap-2.5">
              {[30, 45, 60].map((sec) => (
                <button
                  key={sec}
                  type="button"
                  disabled={loading}
                  onClick={() => setDuration(sec)}
                  className={clsx(
                    "py-2.5 px-3 rounded-2xl text-xs font-bold border transition-all flex items-center justify-center gap-1.5",
                    duration === sec
                      ? "bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 border-cyan-400 text-cyan-300 shadow-[0_0_12px_rgba(34,211,238,0.25)]"
                      : "bg-white/[0.03] border-white/10 text-white/60 hover:text-white hover:bg-white/[0.06]"
                  )}
                >
                  <FiClock size={13} />
                  <span>+{sec} giây</span>
                </button>
              ))}
            </div>
          </div>

          {/* Continuation Prompt Guidance */}
          <div>
            <label className="text-xs font-semibold text-white/70 block mb-1.5">
              Ý tưởng phát triển đoạn tiếp theo (Tùy chọn)
            </label>
            <input
              type="text"
              disabled={loading}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Ví dụ: Đoạn giang tấu guitar solo, beat drop dồn dập hoặc outro êm đềm..."
              className="w-full bg-white/[0.04] text-xs text-white rounded-2xl px-4 py-2.5 border border-white/[0.08] focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          {/* Additional Lyrics (if song has vocals) */}
          <div>
            <label className="text-xs font-semibold text-white/70 block mb-1.5">
              Lời ca cho đoạn mở rộng (Tùy chọn)
            </label>
            <textarea
              rows={3}
              disabled={loading}
              value={additionalLyrics}
              onChange={(e) => setAdditionalLyrics(e.target.value)}
              placeholder="Nhập lời ca tiếp theo cho ca sĩ AI..."
              className="w-full bg-white/[0.04] text-xs text-white rounded-2xl px-4 py-2.5 border border-white/[0.08] focus:outline-none focus:border-cyan-500/50 resize-none"
            />
          </div>

          {/* Action Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading}
              className={clsx(
                "w-full py-3 rounded-2xl text-xs font-bold text-white transition-all flex items-center justify-center gap-2 shadow-lg",
                loading
                  ? "bg-white/10 text-white/40 cursor-wait"
                  : "bg-gradient-to-r from-cyan-500 via-indigo-600 to-fuchsia-600 hover:brightness-110 shadow-cyan-500/25 active:scale-[0.99]"
              )}
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Đang mở rộng âm thanh & hòa âm nối tiếp (+{duration}s)...</span>
                </>
              ) : (
                <>
                  <MdAutoAwesome size={15} />
                  <span>Xác nhận Mở rộng (+{duration}s)</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
