import { useState } from 'react'
import { FiX, FiCopy, FiCheck, FiShare2, FiCode } from 'react-icons/fi'
import { FaFacebookF, FaTwitter, FaTelegramPlane } from 'react-icons/fa'
import { SiZalo } from 'react-icons/si'
import toast from 'react-hot-toast'

export default function ShareModal({ isOpen, onClose, song, post, type = 'song' }) {
  const [copiedLink, setCopiedLink] = useState(false)
  const [copiedEmbed, setCopiedEmbed] = useState(false)

  if (!isOpen) return null

  const baseUrl = window.location.origin
  const isSong = type === 'song' || !!song
  const item = isSong ? song : post

  const title = isSong
    ? (item?.title || 'Bản nhạc Sonavia AI')
    : (item?.author?.username ? `Bài viết của ${item.author.username}` : 'Bài viết Sonavia')

  const subtitle = isSong
    ? (typeof item?.artist === 'object' ? item?.artist?.username : item?.artist || 'Sonavia Artist')
    : (item?.content?.slice(0, 60) || '')

  const shareUrl = isSong
    ? `${baseUrl}/songs/${item?.id}`
    : `${baseUrl}/community`

  const embedCode = `<iframe src="${shareUrl}?embed=true" width="100%" height="160" frameborder="0" allow="autoplay; encrypted-media"></iframe>`

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareUrl)
    setCopiedLink(true)
    toast.success('Đã sao chép liên kết vào bộ nhớ tạm!')
    setTimeout(() => setCopiedLink(false), 2000)
  }

  const handleCopyEmbed = () => {
    navigator.clipboard.writeText(embedCode)
    setCopiedEmbed(true)
    toast.success('Đã sao chép mã nhúng!')
    setTimeout(() => setCopiedEmbed(false), 2000)
  }

  const handleShareFacebook = () => {
    const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`
    window.open(url, '_blank', 'width=600,height=500')
  }

  const handleShareTwitter = () => {
    const text = `Nghe thử "${title}" sáng tác bởi AI trên Sonavia!`
    const url = `https://twitter.com/intent/tweet?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`
    window.open(url, '_blank', 'width=600,height=450')
  }

  const handleShareZalo = () => {
    const url = `https://sp.zalo.me/plugins/share?url=${encodeURIComponent(shareUrl)}&title=${encodeURIComponent(title)}`
    window.open(url, '_blank', 'width=600,height=500')
  }

  const handleShareTelegram = () => {
    const text = `Nghe "${title}" trên Sonavia AI:`
    const url = `https://t.me/share/url?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(text)}`
    window.open(url, '_blank', 'width=600,height=500')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/70 backdrop-blur-md transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div
        className="relative z-10 w-full max-w-md rounded-3xl overflow-hidden border border-white/10 shadow-2xl animate-scale-in"
        style={{
          background: 'linear-gradient(180deg, rgba(17, 18, 42, 0.98) 0%, rgba(9, 10, 24, 0.98) 100%)',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.7), 0 0 40px rgba(99, 102, 241, 0.15)',
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
              <FiShare2 size={16} className="text-white" />
            </div>
            <h3 className="text-base font-bold text-white">
              Chia sẻ {isSong ? 'bài hát' : 'nội dung'}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.08] transition-colors"
          >
            <FiX size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Item Preview Card */}
          <div className="flex items-center gap-3.5 p-3 rounded-2xl bg-white/[0.03] border border-white/[0.06]">
            {isSong && (
              <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-500 flex items-center justify-center text-xl shrink-0 overflow-hidden shadow-md">
                {item?.cover_image_url ? (
                  <img src={item.cover_image_url} alt={title} className="w-full h-full object-cover" />
                ) : (
                  '🎵'
                )}
              </div>
            )}
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-bold text-white truncate">{title}</h4>
              <p className="text-xs text-white/50 truncate mt-0.5">{subtitle}</p>
            </div>
          </div>

          {/* Social Platforms Row */}
          <div>
            <label className="text-xs font-semibold text-white/50 block mb-2.5">
              Chia sẻ qua mạng xã hội
            </label>
            <div className="grid grid-cols-4 gap-2.5 text-center">
              <button
                onClick={handleShareFacebook}
                className="flex flex-col items-center justify-center gap-1.5 py-3 rounded-2xl bg-[#1877f2]/10 hover:bg-[#1877f2]/20 border border-[#1877f2]/30 text-[#1877f2] transition-all group"
              >
                <div className="w-8 h-8 rounded-xl bg-[#1877f2] text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
                  <FaFacebookF size={15} />
                </div>
                <span className="text-[11px] font-medium text-white/70">Facebook</span>
              </button>

              <button
                onClick={handleShareZalo}
                className="flex flex-col items-center justify-center gap-1.5 py-3 rounded-2xl bg-[#0068ff]/10 hover:bg-[#0068ff]/20 border border-[#0068ff]/30 text-[#0068ff] transition-all group"
              >
                <div className="w-8 h-8 rounded-xl bg-[#0068ff] text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform font-bold text-xs">
                  <SiZalo size={16} />
                </div>
                <span className="text-[11px] font-medium text-white/70">Zalo</span>
              </button>

              <button
                onClick={handleShareTwitter}
                className="flex flex-col items-center justify-center gap-1.5 py-3 rounded-2xl bg-white/[0.05] hover:bg-white/[0.1] border border-white/10 text-white transition-all group"
              >
                <div className="w-8 h-8 rounded-xl bg-white/10 text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
                  <FaTwitter size={15} />
                </div>
                <span className="text-[11px] font-medium text-white/70">Twitter / X</span>
              </button>

              <button
                onClick={handleShareTelegram}
                className="flex flex-col items-center justify-center gap-1.5 py-3 rounded-2xl bg-[#229ed9]/10 hover:bg-[#229ed9]/20 border border-[#229ed9]/30 text-[#229ed9] transition-all group"
              >
                <div className="w-8 h-8 rounded-xl bg-[#229ed9] text-white flex items-center justify-center shadow-md group-hover:scale-105 transition-transform">
                  <FaTelegramPlane size={15} />
                </div>
                <span className="text-[11px] font-medium text-white/70">Telegram</span>
              </button>
            </div>
          </div>

          {/* Copy Direct Link */}
          <div>
            <label className="text-xs font-semibold text-white/50 block mb-1.5">
              Liên kết trực tiếp
            </label>
            <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-white/[0.04] border border-white/[0.08]">
              <input
                type="text"
                readOnly
                value={shareUrl}
                className="flex-1 bg-transparent px-3 text-xs text-white/70 focus:outline-none font-mono truncate"
              />
              <button
                onClick={handleCopyLink}
                className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white transition-all flex items-center gap-1.5 shadow-md shadow-cyan-500/20 shrink-0"
              >
                {copiedLink ? (
                  <>
                    <FiCheck size={14} className="text-emerald-300" />
                    <span>Đã chép</span>
                  </>
                ) : (
                  <>
                    <FiCopy size={14} />
                    <span>Sao chép</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Embed Code (Dành cho bài hát) */}
          {isSong && (
            <div className="pt-1">
              <button
                onClick={handleCopyEmbed}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/[0.06] text-xs text-white/60 hover:text-white transition-all font-medium"
              >
                <FiCode size={14} />
                <span>{copiedEmbed ? 'Đã sao chép mã nhúng Web!' : 'Sao chép mã nhúng Web Player (<iframe />)'}</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
