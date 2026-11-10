import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  FiHeart, FiMessageCircle, FiShare2, FiMoreHorizontal,
  FiImage, FiMusic, FiX, FiTrendingUp, FiUsers,
  FiHash, FiChevronDown, FiSend, FiUserPlus, FiUserCheck,
  FiZap, FiGlobe, FiRss,
} from 'react-icons/fi'
import { MdMusicNote, MdAutoAwesome, MdLocalFireDepartment } from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import usePlayerStore from '../store/playerStore'
import toast from 'react-hot-toast'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'
import clsx from 'clsx'

// ─── Helpers ─────────────────────────────────────────────────────────────────

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
  'from-blue-700 to-indigo-600', 'from-cyan-600 to-blue-600',
]

function gradOf(str = '') {
  return COVER_GRADIENTS[(str.charCodeAt(0) || 0) % COVER_GRADIENTS.length]
}

function Avatar({ user, size = 'md', online = false }) {
  const sz = { sm: 'w-7 h-7 text-[10px]', md: 'w-10 h-10 text-xs', lg: 'w-12 h-12 text-sm' }[size]
  return (
    <div className={`${sz} rounded-full overflow-hidden shrink-0 relative ring-2 ring-white/10`}>
      {user?.avatar_url
        ? <img src={user.avatar_url} className="w-full h-full object-cover" alt={user.username} />
        : <div className={`w-full h-full bg-gradient-to-br ${gradOf(user?.username)} flex items-center justify-center font-bold text-white`}>
          {user?.username?.[0]?.toUpperCase() || '?'}
        </div>
      }
      {online && <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-400 rounded-full border-2 border-[#070711]" />}
    </div>
  )
}

// ─── Stats Banner ─────────────────────────────────────────────────────────────

function StatsBanner({ stats }) {
  if (!stats) return null
  const items = [
    { icon: FiUsers, label: 'Thành viên', value: stats.total_users?.toLocaleString(), color: 'text-indigo-400' },
    { icon: MdMusicNote, label: 'Bài hát', value: stats.total_songs?.toLocaleString(), color: 'text-cyan-400' },
    { icon: FiMessageCircle, label: 'Bài đăng', value: stats.total_posts?.toLocaleString(), color: 'text-blue-400' },
    { icon: FiZap, label: 'Nghệ sĩ', value: stats.total_artists?.toLocaleString(), color: 'text-amber-400' },
  ]
  return (
    <div className="grid grid-cols-4 gap-3 mb-6">
      {items.map(({ icon: Icon, label, value, color }) => (
        <div key={label} className="glass-card p-3 text-center">
          <Icon size={16} className={`${color} mx-auto mb-1`} />
          <p className={`text-lg font-black ${color}`}>{value || '0'}</p>
          <p className="text-[10px] text-white/30">{label}</p>
        </div>
      ))}
    </div>
  )
}

// ─── Trending Tags ────────────────────────────────────────────────────────────

function TrendingTags({ tags, onTagClick, activeTag }) {
  if (!tags?.length) return null
  return (
    <div className="glass-card p-4 mb-4">
      <div className="flex items-center gap-2 mb-3">
        <FiHash size={13} className="text-indigo-400" />
        <p className="text-xs font-bold text-white/70 uppercase tracking-wider">Trending Tags</p>
      </div>
      <div className="space-y-1">
        {tags.slice(0, 8).map(({ tag, count }) => (
          <button key={tag} onClick={() => onTagClick(tag)}
            className={clsx(
              'w-full flex items-center justify-between px-3 py-2 rounded-xl text-sm transition-all',
              activeTag === tag
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                : 'text-white/50 hover:bg-white/[0.05] hover:text-white'
            )}>
            <span className="font-medium">#{tag}</span>
            <span className="text-[10px] text-white/25 bg-white/[0.05] px-1.5 py-0.5 rounded-full">{count}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

// ─── Suggested User Card ──────────────────────────────────────────────────────

function SuggestedUserCard({ user, compact = false }) {
  const { isAuthenticated } = useAuthStore()
  const [following, setFollowing] = useState(user.is_following)

  const handleFollow = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/auth/users/${user.username}/follow/`)
      setFollowing(data.following)
      toast.success(data.following ? `Đang theo dõi @${user.username}` : 'Đã bỏ theo dõi')
    } catch { toast.error('Lỗi') }
  }

  if (compact) return (
    <div className="flex items-center gap-3 py-2">
      <Link to={`/profile/${user.username}`}><Avatar user={user} online /></Link>
      <div className="flex-1 min-w-0">
        <Link to={`/profile/${user.username}`}
          className="text-sm font-semibold text-white hover:text-indigo-300 transition-colors truncate block">
          {user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.username}
        </Link>
        <p className="text-[10px] text-white/30 truncate">
          {user.is_artist ? '🎤 Nghệ sĩ' : '🎧 Người nghe'} · {user.followers_count || 0} followers
        </p>
      </div>
      <button onClick={handleFollow}
        className={clsx('shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all',
          following
            ? 'bg-white/5 border border-white/10 text-white/40 hover:bg-red-500/10 hover:text-red-400'
            : 'btn-primary py-1.5 px-3')}>
        {following ? <FiUserCheck size={12} /> : <><FiUserPlus size={11} className="inline mr-1" />Follow</>}
      </button>
    </div>
  )

  return (
    <div className="glass-card p-4 text-center hover:border-white/10 transition-all group">
      <div className="relative w-16 h-16 mx-auto mb-3">
        <div className={`absolute inset-0 bg-gradient-to-br ${gradOf(user.username)} rounded-full blur-md opacity-40 group-hover:opacity-60 transition-opacity`} />
        <Link to={`/profile/${user.username}`}>
          <Avatar user={user} size="lg" online />
        </Link>
      </div>
      <Link to={`/profile/${user.username}`}
        className="text-sm font-bold text-white hover:text-indigo-300 transition-colors block truncate">
        {user.first_name ? `${user.first_name} ${user.last_name}`.trim() : user.username}
      </Link>
      <p className="text-[10px] text-white/30 mb-1">@{user.username}</p>
      {user.is_artist && <span className="badge badge-purple text-[9px] mb-2 inline-block">🎤 Nghệ sĩ</span>}
      <p className="text-[10px] text-white/25 mb-3">{user.followers_count || 0} followers</p>
      <button onClick={handleFollow}
        className={clsx('w-full py-1.5 rounded-xl text-xs font-semibold transition-all',
          following
            ? 'bg-white/5 border border-white/10 text-white/40'
            : 'btn-primary')}>
        {following ? 'Đang theo dõi' : 'Theo dõi'}
      </button>
    </div>
  )
}

// ─── PostCard nâng cấp ────────────────────────────────────────────────────────

function PostCard({ post, onDelete, highlighted = false }) {
  const { isAuthenticated, user: me } = useAuthStore()
  const { playSong } = usePlayerStore()
  const [liked, setLiked] = useState(post.is_liked)
  const [likesCount, setLikesCount] = useState(post.likes_count)
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState(post.post_comments || [])
  const [commentsCount, setCommentsCount] = useState(post.comments_count)
  const [newComment, setNewComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const isOwner = me?.username === post.author?.username
  const grad = gradOf(post.author?.username)

  const handleLike = async () => {
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    const wasLiked = liked
    setLiked(!wasLiked)
    setLikesCount(c => wasLiked ? c - 1 : c + 1)
    try {
      const { data } = await api.post(`/social/posts/${post.id}/like/`)
      setLiked(data.liked)
      setLikesCount(data.likes_count)
    } catch {
      setLiked(wasLiked)
      setLikesCount(c => wasLiked ? c + 1 : c - 1)
    }
  }

  const handleComment = async (e) => {
    e.preventDefault()
    if (!newComment.trim() || submitting) return
    setSubmitting(true)
    try {
      const { data } = await api.post(`/social/posts/${post.id}/comment/`, { content: newComment })
      setComments(prev => [...prev, data])
      setCommentsCount(c => c + 1)
      setNewComment('')
    } catch { toast.error('Lỗi khi bình luận') }
    setSubmitting(false)
  }

  const handleShare = () => {
    const url = `${window.location.origin}/community`
    navigator.clipboard.writeText(url)
    toast.success('Đã copy link!')
    setShowMenu(false)
  }

  const handleDelete = async () => {
    if (!window.confirm('Xóa bài đăng này?')) return
    try {
      await api.delete(`/social/posts/${post.id}/`)
      toast.success('Đã xóa')
      onDelete?.(post.id)
    } catch { toast.error('Lỗi') }
    setShowMenu(false)
  }

  // Tách hashtag trong nội dung thành links
  const renderContent = (text) => {
    if (!text) return null
    const parts = text.split(/(#\w+)/g)
    return parts.map((part, i) =>
      part.startsWith('#')
        ? <Link key={i} to={`/community?tag=${part.slice(1)}`}
          className="text-indigo-400 hover:text-indigo-300 font-medium transition-colors">
          {part}
        </Link>
        : <span key={i}>{part}</span>
    )
  }

  return (
    <article className={clsx(
      'glass-card overflow-hidden transition-all duration-300 hover:border-white/10',
      highlighted && 'border-indigo-500/30 bg-indigo-500/[0.03]'
    )}>
      {/* Header */}
      <div className="flex items-center gap-3 px-5 pt-4 pb-3">
        <Link to={`/profile/${post.author.username}`}>
          <Avatar user={post.author} online />
        </Link>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <Link to={`/profile/${post.author.username}`}
              className="text-sm font-bold text-white hover:text-indigo-300 transition-colors leading-none">
              {post.author.first_name
                ? `${post.author.first_name} ${post.author.last_name}`.trim()
                : post.author.username}
            </Link>
            <span className="text-white/25 text-xs">@{post.author.username}</span>
            {post.author.is_artist && (
              <span className="badge badge-purple text-[9px]">🎤 Nghệ sĩ</span>
            )}
          </div>
          <p className="text-[11px] text-white/30 mt-0.5">
            {formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: vi })}
          </p>
        </div>

        {/* More menu */}
        <div className="relative shrink-0">
          <button onClick={() => setShowMenu(!showMenu)}
            className="btn-icon w-7 h-7 text-white/25 hover:text-white/60">
            <FiMoreHorizontal size={15} />
          </button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-10" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-8 z-20 bg-[rgba(14,14,28,0.98)] border border-white/10 rounded-xl shadow-2xl overflow-hidden min-w-[140px] backdrop-blur-sm">
                <button onClick={handleShare}
                  className="w-full text-left px-4 py-2.5 text-sm text-white/60 hover:bg-white/5 hover:text-white transition-colors flex items-center gap-2">
                  <FiShare2 size={13} /> Chia sẻ
                </button>
                {isOwner && (
                  <button onClick={handleDelete}
                    className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors">
                    Xóa bài
                  </button>
                )}
                <button onClick={() => setShowMenu(false)}
                  className="w-full text-left px-4 py-2.5 text-sm text-white/25 hover:bg-white/5 transition-colors">
                  Đóng
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-5 pb-3">
        <p className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">
          {renderContent(post.content)}
        </p>
      </div>

      {/* Image */}
      {post.image_url && (
        <div className="mx-5 mb-3 rounded-2xl overflow-hidden border border-white/[0.07]">
          <img src={post.image_url} className="w-full max-h-96 object-cover" alt="post" />
        </div>
      )}

      {/* Song attachment */}
      {post.song && (
        <div className="mx-5 mb-3">
          <div className="flex items-center gap-3 p-3 bg-white/[0.04] border border-white/[0.07] rounded-2xl group">
            <button
              onClick={() => playSong(post.song, [post.song])}
              className="w-10 h-10 rounded-xl overflow-hidden shrink-0 relative hover:scale-105 transition-transform">
              {post.song.cover_image_url
                ? <img src={post.song.cover_image_url} className="w-full h-full object-cover" alt={post.song.title} />
                : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-sm`}>🎵</div>
              }
              <div className="absolute inset-0 bg-black/30 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <span className="text-white text-xs">▶</span>
              </div>
            </button>
            <div className="min-w-0 flex-1">
              <Link to={`/songs/${post.song.id}`}
                className="text-sm font-semibold text-white truncate block hover:text-indigo-300 transition-colors">
                {post.song.title}
              </Link>
              <p className="text-[11px] text-white/35 truncate">{post.song.artist?.username}</p>
            </div>
            <div className="flex items-center gap-1.5 shrink-0">
              {post.song.genre && <span className="badge badge-purple text-[9px]">{post.song.genre}</span>}
              <MdMusicNote className="text-indigo-400" size={14} />
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="px-5 py-2.5 border-t border-white/[0.05] flex items-center gap-1">
        {/* Like */}
        <button onClick={handleLike}
          className={clsx(
            'flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl transition-all',
            liked ? 'text-pink-400 bg-pink-500/10' : 'text-white/35 hover:text-pink-400 hover:bg-pink-500/10'
          )}>
          <FiHeart size={14} className={liked ? 'fill-current' : ''} />
          <span>{likesCount > 0 ? likesCount : ''}</span>
          <span className="hidden sm:inline">Thích</span>
        </button>

        {/* Comment */}
        <button onClick={() => setShowComments(!showComments)}
          className={clsx(
            'flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl transition-all',
            showComments ? 'text-indigo-400 bg-indigo-500/10' : 'text-white/35 hover:text-indigo-400 hover:bg-indigo-500/10'
          )}>
          <FiMessageCircle size={14} />
          <span>{commentsCount > 0 ? commentsCount : ''}</span>
          <span className="hidden sm:inline">Bình luận</span>
        </button>

        {/* Share */}
        <button onClick={handleShare}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl text-white/35 hover:text-white hover:bg-white/[0.05] transition-all ml-auto">
          <FiShare2 size={14} />
          <span className="hidden sm:inline">Chia sẻ</span>
        </button>
      </div>

      {/* Comments */}
      {showComments && (
        <div className="px-5 pb-4 border-t border-white/[0.04] pt-3 animate-slide-up">
          {/* Existing comments */}
          <div className="space-y-3 mb-3">
            {comments.length === 0
              ? <p className="text-xs text-white/25 text-center py-2">Chưa có bình luận. Hãy là người đầu tiên!</p>
              : comments.map(c => (
                <div key={c.id} className="flex gap-2.5 group">
                  <div className={`w-7 h-7 rounded-full bg-gradient-to-br ${gradOf(c.user?.username)} flex items-center justify-center text-[10px] font-bold text-white shrink-0`}>
                    {c.user?.username?.[0]?.toUpperCase()}
                  </div>
                  <div className="flex-1 bg-white/[0.04] rounded-2xl px-3.5 py-2.5">
                    <div className="flex items-center gap-2 mb-1">
                      <Link to={`/profile/${c.user?.username}`}
                        className="text-xs font-bold text-indigo-300 hover:text-indigo-200 transition-colors">
                        @{c.user?.username}
                      </Link>
                      <span className="text-[10px] text-white/20">
                        {formatDistanceToNow(new Date(c.created_at), { addSuffix: true, locale: vi })}
                      </span>
                    </div>
                    <p className="text-xs text-white/70 leading-relaxed">{c.content}</p>
                  </div>
                </div>
              ))
            }
          </div>

          {/* New comment input */}
          {isAuthenticated ? (
            <form onSubmit={handleComment} className="flex gap-2">
              <input
                className="input-field flex-1 text-xs py-2.5"
                placeholder="Viết bình luận của bạn..."
                value={newComment}
                onChange={e => setNewComment(e.target.value)}
              />
              <button type="submit" disabled={!newComment.trim() || submitting}
                className="btn-primary px-3 py-2 text-xs shrink-0 flex items-center gap-1">
                <FiSend size={11} />
              </button>
            </form>
          ) : (
            <p className="text-xs text-white/30 text-center py-2">
              <Link to="/login" className="text-indigo-400 hover:underline">Đăng nhập</Link> để bình luận
            </p>
          )}
        </div>
      )}
    </article>
  )
}

// ─── Create Post Form ─────────────────────────────────────────────────────────

function CreatePostForm({ user, onPosted }) {
  const [content, setContent] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [songQuery, setSongQuery] = useState('')
  const [songResults, setSongResults] = useState([])
  const [selectedSong, setSelectedSong] = useState(null)
  const [showSongPicker, setShowSongPicker] = useState(false)
  const [posting, setPosting] = useState(false)
  const [focused, setFocused] = useState(false)
  const fileRef = useRef()
  const songTimerRef = useRef()
  const textareaRef = useRef()

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) { toast.error('Ảnh tối đa 5MB'); return }
    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
  }

  const handleSongSearch = (q) => {
    setSongQuery(q)
    clearTimeout(songTimerRef.current)
    if (!q.trim()) { setSongResults([]); return }
    songTimerRef.current = setTimeout(async () => {
      try {
        const { data } = await api.get(`/music/songs/?search=${encodeURIComponent(q)}&page_size=5`)
        setSongResults((data.results || data).slice(0, 5))
      } catch { }
    }, 300)
  }

  const handlePost = async (e) => {
    e.preventDefault()
    if (!content.trim() || posting) return
    setPosting(true)
    try {
      const fd = new FormData()
      fd.append('content', content)
      if (imageFile) fd.append('image', imageFile)
      if (selectedSong) {
        fd.append('song_id', selectedSong.id)
        fd.append('song', selectedSong.id)
      }
      const { data } = await api.post('/social/posts/', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      onPosted(data)
      setContent(''); setImageFile(null); setImagePreview(null)
      setSelectedSong(null); setSongQuery(''); setFocused(false)
      toast.success('Đã đăng! 🎉')
    } catch { toast.error('Không thể đăng bài') }
    setPosting(false)
  }

  return (
    <div className={clsx(
      'glass-card overflow-hidden transition-all duration-300',
      focused ? 'border-indigo-500/30 shadow-lg shadow-indigo-500/5' : ''
    )}>
      <div className="p-4">
        <div className="flex gap-3">
          <Avatar user={user} online />
          <textarea
            ref={textareaRef}
            placeholder="Chia sẻ cảm nhận âm nhạc, bài hát yêu thích hoặc dùng #tag..."
            value={content}
            onChange={e => setContent(e.target.value)}
            onFocus={() => setFocused(true)}
            rows={focused ? 3 : 2}
            className="input-field resize-none text-sm flex-1 transition-all"
          />
        </div>

        {/* Image preview */}
        {imagePreview && (
          <div className="relative mt-3 ml-13 w-fit">
            <img src={imagePreview} alt="preview" className="max-h-48 rounded-xl object-cover border border-white/10" />
            <button type="button"
              onClick={() => { setImageFile(null); setImagePreview(null) }}
              className="absolute -top-2 -right-2 w-6 h-6 bg-black/80 rounded-full flex items-center justify-center text-white hover:bg-red-600 transition-colors">
              <FiX size={11} />
            </button>
          </div>
        )}

        {/* Selected song */}
        {selectedSong && (
          <div className="flex items-center gap-3 mt-3 p-2.5 bg-white/[0.04] border border-indigo-500/20 rounded-xl">
            <MdMusicNote className="text-indigo-400 shrink-0" size={15} />
            <span className="text-xs text-white/80 flex-1 truncate font-medium">
              {selectedSong.title} — {selectedSong.artist?.username}
            </span>
            <button type="button" onClick={() => setSelectedSong(null)}
              className="text-white/30 hover:text-white/70 transition-colors">
              <FiX size={13} />
            </button>
          </div>
        )}

        {/* Song picker */}
        {showSongPicker && (
          <div className="mt-3 relative">
            <input
              className="input-field text-sm py-2"
              placeholder="Tìm bài hát để đính kèm..."
              value={songQuery}
              onChange={e => handleSongSearch(e.target.value)}
              autoFocus
            />
            {songResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-[rgba(14,14,28,0.98)] border border-white/10 rounded-xl overflow-hidden shadow-2xl backdrop-blur-sm">
                {songResults.map(s => (
                  <button key={s.id} type="button"
                    onClick={() => { setSelectedSong(s); setShowSongPicker(false); setSongQuery(''); setSongResults([]) }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.05] transition-colors text-left">
                    <div className="w-8 h-8 rounded-lg overflow-hidden shrink-0">
                      {s.cover_image_url
                        ? <img src={s.cover_image_url} className="w-full h-full object-cover" alt="" />
                        : <div className={`w-full h-full bg-gradient-to-br ${gradOf(s.artist?.username)} flex items-center justify-center text-xs`}>🎵</div>
                      }
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-white font-medium truncate">{s.title}</p>
                      <p className="text-xs text-white/35">{s.artist?.username}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Bottom toolbar */}
        {(focused || content) && (
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/[0.05] animate-slide-up">
            <div className="flex gap-1">
              <button type="button" title="Đính kèm ảnh"
                onClick={() => fileRef.current?.click()}
                className={clsx('btn-icon w-8 h-8 text-sm', imageFile ? 'text-indigo-400' : 'text-white/35 hover:text-indigo-400')}>
                <FiImage size={14} />
              </button>
              <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageChange} />
              <button type="button" title="Đính kèm bài hát"
                onClick={() => setShowSongPicker(!showSongPicker)}
                className={clsx('btn-icon w-8 h-8 text-sm', selectedSong || showSongPicker ? 'text-indigo-400' : 'text-white/35 hover:text-indigo-400')}>
                <FiMusic size={14} />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className={clsx('text-[10px]', content.length > 450 ? 'text-red-400' : 'text-white/20')}>
                {content.length}/500
              </span>
              <button
                onClick={handlePost}
                disabled={!content.trim() || posting || content.length > 500}
                className="btn-primary px-5 py-2 text-sm flex items-center gap-1.5">
                {posting
                  ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  : <FiSend size={13} />
                }
                {posting ? 'Đăng...' : 'Đăng'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Main CommunityPage ───────────────────────────────────────────────────────

export default function CommunityPage() {
  const { user, isAuthenticated } = useAuthStore()
  const [posts, setPosts] = useState([])
  const [trendingPosts, setTrendingPosts] = useState([])
  const [suggestedUsers, setSuggestedUsers] = useState([])
  const [tags, setTags] = useState([])
  const [stats, setStats] = useState(null)
  const [activeTab, setActiveTab] = useState('all')   // 'all' | 'following' | 'trending'
  const [activeTag, setActiveTag] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)

  // Load sidebar data
  useEffect(() => {
    const loadSidebar = async () => {
      try {
        const [tagsRes, sugRes, statsRes] = await Promise.all([
          api.get('/social/trending/tags/'),
          api.get('/social/users/suggested/?limit=6'),
          api.get('/social/stats/'),
        ])
        setTags(tagsRes.data || [])
        setSuggestedUsers(sugRes.data || [])
        setStats(statsRes.data)
      } catch { }
    }
    loadSidebar()
  }, [])

  // Load posts theo tab/tag
  const loadPosts = useCallback(async (reset = true) => {
    if (reset) setLoading(true)
    else setLoadingMore(true)
    try {
      const p = reset ? 1 : page + 1
      let url = '/social/posts/?'
      if (activeTab === 'following' && isAuthenticated) url += 'feed=1&'
      if (activeTab === 'trending') {
        const { data } = await api.get('/social/trending/posts/')
        setTrendingPosts(data.results || data)
        setPosts(data.results || data)
        setHasMore(false)
        if (reset) setLoading(false)
        else setLoadingMore(false)
        return
      }
      url += `page=${p}`
      const { data } = await api.get(url)
      let results = data.results || data
      if (activeTag) results = results.filter(p => p.content?.includes(`#${activeTag}`))
      if (reset) { setPosts(results); setPage(1) }
      else { setPosts(prev => [...prev, ...results]); setPage(p) }
      setHasMore(!!data.next && !activeTag)
    } catch { toast.error('Không thể tải bài đăng') }
    if (reset) setLoading(false)
    else setLoadingMore(false)
  }, [activeTab, activeTag, isAuthenticated, page])

  useEffect(() => { loadPosts(true) }, [activeTab, activeTag])

  const handleTagClick = (tag) => {
    setActiveTag(prev => prev === tag ? null : tag)
    setActiveTab('all')
  }

  const handlePosted = (newPost) => {
    setPosts(prev => [newPost, ...prev])
  }

  const handleDelete = (postId) => {
    setPosts(prev => prev.filter(p => p.id !== postId))
  }

  return (
    <div className="animate-fade-in min-h-full">
      {/* ── Hero Header ── */}
      <div className="relative overflow-hidden px-6 pt-7 pb-6 border-b border-white/[0.05]">
        <div className="absolute -top-10 left-1/3 w-64 h-64 rounded-full blur-[60px] pointer-events-none"
          style={{ background: 'rgba(99,102,241,0.12)' }} />
        <div className="absolute -top-5 right-1/4 w-48 h-48 rounded-full blur-[50px] pointer-events-none"
          style={{ background: 'rgba(34,211,238,0.07)' }} />
        <div className="relative max-w-screen-xl mx-auto">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center"
              style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
              <FiUsers size={18} className="text-white" />
            </div>
            <h1 className="text-2xl font-black text-white">Cộng đồng</h1>
            <span className="badge badge-purple text-[10px] animate-pulse">LIVE</span>
          </div>
          <p className="text-white/40 text-sm ml-12">
            Kết nối với những người yêu âm nhạc, chia sẻ cảm xúc và khám phá nhạc mới
          </p>
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-4 py-6">
        {/* Stats */}
        <StatsBanner stats={stats} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* ── LEFT SIDEBAR ── */}
          <aside className="hidden lg:block lg:col-span-3 space-y-4">
            {/* Navigation */}
            <div className="glass-card p-3 space-y-1">
              {[
                { key: 'all', icon: FiGlobe, label: 'Tất cả bài đăng' },
                { key: 'following', icon: FiRss, label: 'Đang theo dõi' },
                { key: 'trending', icon: MdLocalFireDepartment, label: 'Nổi bật' },
              ].map(({ key, icon: Icon, label }) => (
                <button key={key} onClick={() => { setActiveTab(key); setActiveTag(null) }}
                  className={clsx(
                    'w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all text-left',
                    activeTab === key && !activeTag
                      ? 'bg-gradient-to-r from-indigo-500/20 via-purple-500/15 to-cyan-500/10 text-white border border-indigo-500/30 shadow-[0_0_15px_rgba(99,102,241,0.15)]'
                      : 'text-white/45 hover:text-white hover:bg-white/[0.04]'
                  )}>
                  <Icon size={15} className={activeTab === key && !activeTag ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(34,211,238,0.6)]' : ''} />
                  {label}
                </button>
              ))}
            </div>

            {/* Trending tags */}
            <TrendingTags tags={tags} onTagClick={handleTagClick} activeTag={activeTag} />

            {/* Link to people page */}
            <Link to="/people"
              className="glass-card-hover p-4 flex items-center gap-3 group">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
                <FiUsers size={16} className="text-white" />
              </div>
              <div>
                <p className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">Khám phá mọi người</p>
                <p className="text-[11px] text-white/35">Tìm và kết nối với cộng đồng</p>
              </div>
            </Link>
          </aside>

          {/* ── CENTER FEED ── */}
          <main className="lg:col-span-6 space-y-4">
            {/* Mobile tab switcher */}
            <div className="flex lg:hidden gap-1 p-1 bg-white/[0.04] rounded-xl border border-white/[0.06]">
              {[['all', 'Tất cả'], ['following', 'Theo dõi'], ['trending', '🔥 Nổi bật']].map(([k, l]) => (
                <button key={k} onClick={() => { setActiveTab(k); setActiveTag(null) }}
                  className={clsx('flex-1 py-2 rounded-lg text-xs font-semibold transition-all',
                    activeTab === k && !activeTag ? 'bg-indigo-600 text-white' : 'text-white/40 hover:text-white')}>
                  {l}
                </button>
              ))}
            </div>

            {/* Active tag filter */}
            {activeTag && (
              <div className="flex items-center gap-2 p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl animate-slide-up">
                <FiHash size={14} className="text-indigo-400" />
                <span className="text-sm font-semibold text-indigo-300">#{activeTag}</span>
                <button onClick={() => setActiveTag(null)}
                  className="ml-auto text-white/40 hover:text-white transition-colors">
                  <FiX size={14} />
                </button>
              </div>
            )}

            {/* Create post */}
            {isAuthenticated && user && (
              <CreatePostForm user={user} onPosted={handlePosted} />
            )}

            {/* Posts list */}
            {loading
              ? [...Array(3)].map((_, i) => (
                <div key={i} className="glass-card overflow-hidden animate-pulse">
                  <div className="p-5 flex gap-3">
                    <div className="w-10 h-10 rounded-full skeleton shrink-0" />
                    <div className="flex-1 space-y-2 pt-1">
                      <div className="h-3 skeleton rounded w-1/3" />
                      <div className="h-3 skeleton rounded w-full" />
                      <div className="h-3 skeleton rounded w-2/3" />
                    </div>
                  </div>
                </div>
              ))
              : posts.length === 0
                ? (
                  <div className="glass-card p-12 text-center">
                    <div className="text-5xl mb-4">📭</div>
                    <p className="text-white/50 font-bold text-lg mb-1">
                      {activeTab === 'following' ? 'Chưa có bài từ người bạn follow' : 'Chưa có bài đăng nào'}
                    </p>
                    <p className="text-white/25 text-sm">
                      {activeTab === 'following'
                        ? 'Theo dõi thêm người dùng để xem bài của họ tại đây'
                        : 'Hãy là người đầu tiên chia sẻ cảm nhận âm nhạc!'
                      }
                    </p>
                    {activeTab === 'following' && (
                      <Link to="/people" className="btn-primary mt-4 inline-flex items-center gap-2 text-sm">
                        <FiUsers size={14} /> Khám phá mọi người
                      </Link>
                    )}
                  </div>
                )
                : posts.map(p => (
                  <PostCard key={p.id} post={p} onDelete={handleDelete} />
                ))
            }

            {/* Load more */}
            {hasMore && !loading && (
              <div className="text-center pt-2">
                <button onClick={() => loadPosts(false)} disabled={loadingMore}
                  className="btn-ghost border border-white/10 flex items-center gap-2 mx-auto text-sm px-6 py-2.5">
                  {loadingMore
                    ? <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                    : <FiChevronDown size={16} />
                  }
                  {loadingMore ? 'Đang tải...' : 'Xem thêm'}
                </button>
              </div>
            )}
          </main>

          {/* ── RIGHT SIDEBAR ── */}
          <aside className="hidden lg:block lg:col-span-3 space-y-4">
            {/* Suggested users */}
            <div className="glass-card p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <MdAutoAwesome size={14} className="text-indigo-400" />
                  <p className="text-xs font-bold text-white/70 uppercase tracking-wider">Gợi ý theo dõi</p>
                </div>
                <Link to="/people" className="text-[10px] text-indigo-400 hover:text-indigo-300 transition-colors">
                  Xem tất cả
                </Link>
              </div>
              <div className="divide-y divide-white/[0.05]">
                {suggestedUsers.length === 0
                  ? [...Array(4)].map((_, i) => (
                    <div key={i} className="py-2 flex gap-3 animate-pulse">
                      <div className="w-10 h-10 rounded-full skeleton shrink-0" />
                      <div className="flex-1 space-y-1.5 pt-1">
                        <div className="h-3 skeleton rounded w-2/3" />
                        <div className="h-2 skeleton rounded w-1/2" />
                      </div>
                    </div>
                  ))
                  : suggestedUsers.map(u => (
                    <SuggestedUserCard key={u.id} user={u} compact />
                  ))
                }
              </div>
            </div>

            {/* Active musicians */}
            <div className="glass-card p-4">
              <div className="flex items-center gap-2 mb-3">
                <FiTrendingUp size={13} className="text-cyan-400" />
                <p className="text-xs font-bold text-white/70 uppercase tracking-wider">Nghệ sĩ nổi bật</p>
              </div>
              {suggestedUsers.filter(u => u.is_artist).slice(0, 4).map((u, i) => (
                <Link key={u.id} to={`/profile/${u.username}`}
                  className="flex items-center gap-3 py-2 hover:bg-white/[0.03] rounded-xl px-1 transition-colors group">
                  <span className="text-xs text-white/20 w-4 text-center tabular-nums">{i + 1}</span>
                  <Avatar user={u} size="sm" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-white/80 truncate group-hover:text-indigo-300 transition-colors">
                      {u.username}
                    </p>
                    <p className="text-[10px] text-white/30">{u.followers_count || 0} followers</p>
                  </div>
                </Link>
              ))}
              {suggestedUsers.filter(u => u.is_artist).length === 0 && (
                <p className="text-xs text-white/25 text-center py-3">Chưa có nghệ sĩ</p>
              )}
            </div>

            {/* Quick links */}
            <div className="glass-card p-4 space-y-2">
              <p className="text-xs font-bold text-white/30 uppercase tracking-wider mb-3">Khám phá thêm</p>
              {[
                { to: '/explore', icon: '🎵', label: 'Khám phá nhạc' },
                { to: '/create', icon: '🤖', label: 'AI Sáng tác' },
                { to: '/community', icon: '🌐', label: 'Cộng đồng' },
                { to: '/upload', icon: '⬆️', label: 'Đăng bài hát' },
              ].map(({ to, icon, label }) => (
                <Link key={to} to={to}
                  className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm text-white/45 hover:text-white hover:bg-white/[0.05] transition-all">
                  <span>{icon}</span>
                  <span className="font-medium">{label}</span>
                </Link>
              ))}
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
