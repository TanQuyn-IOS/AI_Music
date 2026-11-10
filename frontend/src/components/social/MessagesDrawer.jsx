import { useState, useEffect, useRef } from 'react'
import { FiX, FiSend, FiMessageSquare, FiUser, FiSearch, FiCheck } from 'react-icons/fi'
import { MdGraphicEq } from 'react-icons/md'
import useAuthStore from '../../store/authStore'
import api from '../../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

function formatMessageTime(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diffSec = Math.floor((now - d) / 1000)
  if (diffSec < 60) return 'Vừa xong'
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)} phút trước`
  if (diffSec < 86400) return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
  return `${d.getDate()}/${d.getMonth() + 1}`
}

export default function MessagesDrawer({ isOpen, onClose, initialTargetUsername = null }) {
  const { user: currentUser } = useAuthStore()
  const [conversations, setConversations] = useState([])
  const [activePartner, setActivePartner] = useState(null)
  const [messages, setMessages] = useState([])
  const [inputText, setInputText] = useState('')
  const [loadingHistory, setLoadingHistory] = useState(false)
  const [sending, setSending] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const messagesEndRef = useRef(null)

  // Fetch danh sách cuộc trò chuyện
  const fetchConversations = async () => {
    try {
      const { data } = await api.get('/social/messages/conversations/')
      setConversations(Array.isArray(data) ? data : [])
    } catch {
      // silent
    }
  }

  // Fetch tin nhắn giữa current user và partner
  const fetchMessages = async (username) => {
    if (!username) return
    try {
      const { data } = await api.get(`/social/messages/${username}/`)
      setMessages(data?.messages || [])
      if (data?.target_user) {
        setActivePartner(data.target_user)
      }
    } catch {
      // silent
    }
  }

  // Khởi tạo drawer
  useEffect(() => {
    if (!isOpen) return
    fetchConversations()

    if (initialTargetUsername) {
      // Mở ngay chat với target được chỉ định
      setLoadingHistory(true)
      fetchMessages(initialTargetUsername).finally(() => setLoadingHistory(false))
    }
  }, [isOpen, initialTargetUsername])

  // Polling tin nhắn mới khi đang mở đoạn chat (mỗi 3 giây)
  useEffect(() => {
    if (!isOpen || !activePartner?.username) return
    const interval = setInterval(() => {
      fetchMessages(activePartner.username)
    }, 3000)
    return () => clearInterval(interval)
  }, [isOpen, activePartner?.username])

  // Tự động cuộn xuống tin nhắn cuối
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  const handleSelectConversation = (partner) => {
    setActivePartner(partner)
    setLoadingHistory(true)
    fetchMessages(partner.username).finally(() => setLoadingHistory(false))
  }

  const handleSendMessage = async (e) => {
    e?.preventDefault()
    if (!inputText.trim() || !activePartner?.username || sending) return

    const content = inputText.trim()
    setInputText('')
    setSending(true)

    // Optimistic UI update
    const tempId = `temp_${Date.now()}`
    const optimisticMsg = {
      id: tempId,
      sender: currentUser,
      recipient: activePartner,
      content,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, optimisticMsg])

    try {
      const { data } = await api.post(`/social/messages/${activePartner.username}/`, { content })
      // Cập nhật lại tin nhắn thật từ backend
      setMessages(prev => prev.map(m => m.id === tempId ? data : m))
      fetchConversations()
    } catch (err) {
      toast.error('Không thể gửi tin nhắn. Vui lòng thử lại.')
      setMessages(prev => prev.filter(m => m.id !== tempId))
    } finally {
      setSending(false)
    }
  }

  if (!isOpen) return null

  // Lọc cuộc trò chuyện theo search
  const filteredConversations = conversations.filter(c => {
    const q = searchQuery.toLowerCase().trim()
    if (!q) return true
    return (
      c.partner?.username?.toLowerCase().includes(q) ||
      c.partner?.first_name?.toLowerCase().includes(q) ||
      c.partner?.last_name?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Drawer Body */}
      <div
        className="relative z-10 w-full max-w-xl h-full flex flex-col sonavia-glass border-l border-white/10 shadow-2xl animate-slide-left overflow-hidden"
        style={{
          background: 'linear-gradient(180deg, rgba(14, 15, 34, 0.98) 0%, rgba(8, 9, 20, 0.98) 100%)',
        }}
      >
        {/* Drawer Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/[0.08] bg-white/[0.02]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-cyan-500/20">
              <FiMessageSquare size={16} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white leading-tight">
                Hộp thư Trực tiếp (Direct Messages)
              </h3>
              <p className="text-[11px] text-white/40">
                Nhắn tin riêng & trao đổi âm nhạc với các nghệ sĩ
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-white/40 hover:text-white hover:bg-white/[0.08] transition-colors"
          >
            <FiX size={18} />
          </button>
        </div>

        {/* Content: Split Pane or Single Thread */}
        <div className="flex-1 flex min-h-0">
          {/* Left Column: Conversations List (Visible on desktop or when no partner is selected) */}
          <div
            className={clsx(
              "w-full sm:w-60 border-r border-white/[0.06] flex flex-col bg-black/20",
              activePartner ? "hidden sm:flex" : "flex"
            )}
          >
            {/* Search conversations */}
            <div className="p-3 border-b border-white/[0.06]">
              <div className="relative">
                <FiSearch size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
                <input
                  type="text"
                  placeholder="Tìm trò chuyện..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-white/[0.04] text-xs text-white rounded-xl pl-8 pr-3 py-1.5 border border-white/[0.08] focus:outline-none focus:border-cyan-500/50"
                />
              </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto divide-y divide-white/[0.03] scrollbar-thin scrollbar-thumb-white/10">
              {filteredConversations.length > 0 ? (
                filteredConversations.map((item) => {
                  const partner = item.partner
                  const isSelected = activePartner?.id === partner.id
                  return (
                    <button
                      key={partner.id}
                      onClick={() => handleSelectConversation(partner)}
                      className={clsx(
                        "w-full px-3.5 py-3 text-left transition-colors flex items-center gap-3 relative",
                        isSelected
                          ? "bg-cyan-500/10 border-l-2 border-cyan-400"
                          : "hover:bg-white/[0.03]"
                      )}
                    >
                      <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-sm font-bold text-white shrink-0 overflow-hidden shadow-sm">
                        {partner.avatar ? (
                          <img src={partner.avatar} alt={partner.username} className="w-full h-full object-cover" />
                        ) : (
                          partner.username?.slice(0, 1).toUpperCase()
                        )}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-1">
                          <span className="text-xs font-bold text-white truncate">
                            {partner.username}
                          </span>
                          <span className="text-[10px] text-white/30 shrink-0">
                            {formatMessageTime(item.last_message?.created_at)}
                          </span>
                        </div>
                        <p className="text-[11px] text-white/50 truncate mt-0.5">
                          {item.last_message?.is_self ? 'Bạn: ' : ''}{item.last_message?.content}
                        </p>
                      </div>
                      {item.unread_count > 0 && (
                        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shrink-0" />
                      )}
                    </button>
                  )
                })
              ) : (
                <div className="p-6 text-center text-white/40 text-xs">
                  Chưa có cuộc trò chuyện nào.
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Active Conversation */}
          <div className={clsx("flex-1 flex flex-col min-w-0", !activePartner ? "hidden sm:flex" : "flex")}>
            {activePartner ? (
              <>
                {/* Active Partner Bar */}
                <div className="px-4 py-3 border-b border-white/[0.08] flex items-center justify-between bg-white/[0.02]">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <button
                      onClick={() => setActivePartner(null)}
                      className="sm:hidden p-1 text-white/50 hover:text-white mr-1"
                    >
                      ←
                    </button>
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-xs font-bold text-white shrink-0 overflow-hidden">
                      {activePartner.avatar ? (
                        <img src={activePartner.avatar} alt={activePartner.username} className="w-full h-full object-cover" />
                      ) : (
                        activePartner.username?.slice(0, 1).toUpperCase()
                      )}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-white truncate">
                          {activePartner.username}
                        </span>
                        {activePartner.is_artist && (
                          <span className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                            Nghệ sĩ
                          </span>
                        )}
                      </div>
                      <p className="text-[10px] text-emerald-400">Trực tuyến</p>
                    </div>
                  </div>
                </div>

                {/* Messages Body */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10">
                  {loadingHistory ? (
                    <div className="h-full flex items-center justify-center text-xs text-white/40">
                      Đang tải lịch sử tin nhắn...
                    </div>
                  ) : messages.length > 0 ? (
                    messages.map((msg, i) => {
                      const isMe = msg.sender?.id === currentUser?.id || msg.sender?.username === currentUser?.username
                      return (
                        <div
                          key={msg.id || i}
                          className={clsx("flex flex-col", isMe ? "items-end" : "items-start")}
                        >
                          <div
                            className={clsx(
                              "max-w-[78%] px-3.5 py-2 text-xs leading-relaxed break-words",
                              isMe
                                ? "bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-2xl rounded-tr-xs shadow-md shadow-cyan-600/20"
                                : "bg-white/[0.08] text-white/90 border border-white/10 rounded-2xl rounded-tl-xs"
                            )}
                          >
                            {msg.content}
                          </div>
                          <span className="text-[9px] text-white/30 mt-1 px-1">
                            {formatMessageTime(msg.created_at)}
                          </span>
                        </div>
                      )
                    })
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-center text-white/40 space-y-2">
                      <FiMessageSquare size={24} className="text-white/20" />
                      <p className="text-xs">Hãy gửi lời chào đầu tiên tới {activePartner.username}!</p>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Bar */}
                <form
                  onSubmit={handleSendMessage}
                  className="p-3 border-t border-white/[0.08] bg-white/[0.02] flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder={`Nhắn tin cho ${activePartner.username}...`}
                    className="flex-1 bg-white/[0.04] text-xs text-white rounded-xl px-3.5 py-2.5 border border-white/[0.08] focus:outline-none focus:border-cyan-500/50"
                  />
                  <button
                    type="submit"
                    disabled={!inputText.trim() || sending}
                    className={clsx(
                      "p-2.5 rounded-xl transition-all flex items-center justify-center shrink-0",
                      inputText.trim() && !sending
                        ? "bg-gradient-to-r from-cyan-500 to-indigo-600 text-white shadow-md shadow-cyan-500/20"
                        : "bg-white/[0.04] text-white/20 cursor-not-allowed"
                    )}
                  >
                    <FiSend size={15} />
                  </button>
                </form>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-white/40 space-y-2">
                <div className="w-12 h-12 rounded-2xl bg-white/[0.04] flex items-center justify-center text-white/30 border border-white/10">
                  <FiMessageSquare size={22} />
                </div>
                <h4 className="text-sm font-semibold text-white/70">Chọn cuộc trò chuyện</h4>
                <p className="text-xs text-white/40 max-w-[240px]">
                  Chọn người bạn muốn trao đổi từ danh sách bên trái hoặc nhắn tin từ trang nghệ sĩ.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
