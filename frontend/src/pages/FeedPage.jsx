import { useEffect, useState, useRef } from 'react'
import { Link } from 'react-router-dom'
import { FiHeart, FiMessageCircle, FiShare2, FiMoreHorizontal, FiImage, FiMusic, FiX, FiChevronDown } from 'react-icons/fi'
import { MdMusicNote } from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import { formatDistanceToNow } from 'date-fns'
import { vi } from 'date-fns/locale'
import clsx from 'clsx'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
]

function Avatar({ user }) {
  return (
    <div className="w-10 h-10 rounded-full overflow-hidden shrink-0 ring-2 ring-white/10">
      {user?.avatar_url
        ? <img src={user.avatar_url} className="w-full h-full object-cover" alt={user.username} />
        : <div className="w-full h-full bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center text-xs font-bold text-white">
          {user?.username?.[0]?.toUpperCase() || '?'}
        </div>
      }
    </div>
  )
}

function PostCard({ post, onDelete }) {
  const { isAuthenticated, user: me } = useAuthStore()
  const [liked, setLiked] = useState(post.is_liked)
  const [likesCount, setLikesCount] = useState(post.likes_count)
  const [showComments, setShowComments] = useState(false)
  const [comments, setComments] = useState(post.post_comments || [])
  const [commentsCount, setCommentsCount] = useState(post.comments_count)
  const [newComment, setNewComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const isOwner = me?.username === post.author?.username

  const handleLike = async () => {
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/social/posts/${post.id}/like/`)
      setLiked(data.liked); setLikesCount(data.likes_count)
    } catch { toast.error('Lỗi') }
  }

  const handleComment = async (e) => {
    e.preventDefault(); if (!newComment.trim() || submitting) return
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
    navigator.clipboard.writeText(`${window.location.origin}/feed`)
    toast.success('Đã copy link!')
  }

  const handleDelete = async () => {
    if (!window.confirm('Xóa bài đăng này?')) return
    try {
      await api.delete(`/social/posts/${post.id}/`)
      toast.success('Đã xóa bài đăng')
      onDelete?.(post.id)
    } catch { toast.error('Lỗi khi xóa') }
    setShowMenu(false)
  }

  const grad = COVER_GRADIENTS[(post.author?.username?.charCodeAt(0) || 0) % COVER_GRADIENTS.length]

  return (
    <article className="glass-card overflow-hidden hover:border-white/10 transition-all duration-300">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 pt-4 pb-3">
        <Link to={`/profile/${post.author?.username || ''}`}>
          <Avatar user={post.author} />
        </Link>
        <div className="flex-1 min-w-0">
          <Link to={`/profile/${post.author?.username || ''}`}
            className="text-sm font-bold text-white hover:text-violet-300 transition-colors">
            {post.author?.username || 'Ẩn danh'}
          </Link>
          {post.author?.is_artist && <span className="ml-1.5 badge badge-purple text-[9px]">Nghệ sĩ</span>}
          <p className="text-[11px] text-white/30">
            {formatDistanceToNow(new Date(post.created_at), { addSuffix: true, locale: vi })}
          </p>
        </div>
        {/* More menu */}
        <div className="relative">
          <button onClick={() => setShowMenu(!showMenu)}
            className="btn-icon w-7 h-7 text-white/25 hover:text-white/60">
            <FiMoreHorizontal size={15} />
          </button>
          {showMenu && (
            <div className="absolute right-0 top-8 z-10 bg-dark-700/95 border border-white/10 rounded-xl shadow-xl overflow-hidden min-w-[130px] backdrop-blur-sm">
              <button onClick={handleShare}
                className="w-full text-left px-4 py-2.5 text-sm text-white/60 hover:bg-white/5 hover:text-white transition-colors">
                Chia sẻ link
              </button>
              {isOwner && (
                <button onClick={handleDelete}
                  className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/10 transition-colors">
                  Xóa bài đăng
                </button>
              )}
              <button onClick={() => setShowMenu(false)}
                className="w-full text-left px-4 py-2.5 text-sm text-white/30 hover:bg-white/5 transition-colors">
                Đóng
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-3">
        <p className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap">{post.content}</p>
      </div>

      {/* Image */}
      {post.image_url && (
        <div className="mx-4 mb-3 rounded-xl overflow-hidden">
          <img src={post.image_url} className="w-full max-h-80 object-cover" alt="post" />
        </div>
      )}

      {/* Song attachment */}
      {post.song && (
        <div className="mx-4 mb-3">
          <Link to={`/songs/${post.song.id}`}
            className="flex items-center gap-3 p-3 bg-white/[0.04] hover:bg-white/[0.07] border border-white/[0.07] rounded-xl transition-all group">
            <div className="w-10 h-10 rounded-lg overflow-hidden shrink-0">
              {post.song.cover_image_url
                ? <img src={post.song.cover_image_url} className="w-full h-full object-cover" alt={post.song.title} />
                : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center`}>🎵</div>
              }
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-white truncate group-hover:text-indigo-300 transition-colors">{post.song.title}</p>
              <p className="text-[11px] text-white/35">{post.song.artist?.username}</p>
            </div>
            <MdMusicNote className="text-indigo-400 shrink-0" />
          </Link>
        </div>
      )}

      {/* Actions */}
      <div className="px-4 py-2.5 border-t border-white/[0.05] flex items-center gap-1">
        <button onClick={handleLike}
          className={clsx('flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl transition-all',
            liked ? 'text-pink-400 bg-pink-500/10' : 'text-white/35 hover:text-white hover:bg-white/[0.05]')}>
          <FiHeart size={14} className={liked ? 'fill-current' : ''} />
          {likesCount > 0 && <span>{likesCount}</span>}
          <span className="hidden sm:inline">Thích</span>
        </button>

        <button onClick={() => setShowComments(!showComments)}
          className={clsx('flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl transition-all',
            showComments ? 'text-indigo-400 bg-indigo-500/10' : 'text-white/35 hover:text-white hover:bg-white/[0.05]')}>
          <FiMessageCircle size={14} />
          {commentsCount > 0 && <span>{commentsCount}</span>}
          <span className="hidden sm:inline">Bình luận</span>
        </button>

        <button onClick={handleShare}
          className="flex items-center gap-1.5 text-xs font-semibold px-3 py-2 rounded-xl text-white/35 hover:text-white hover:bg-white/[0.05] transition-all ml-auto">
          <FiShare2 size={14} />
          <span className="hidden sm:inline">Chia sẻ</span>
        </button>
      </div>

      {/* Comments section */}
      {showComments && (
        <div className="px-4 pb-4 border-t border-white/[0.04] pt-3 space-y-2.5 animate-slide-up">
          {comments.slice(-5).map(c => (
            <div key={c.id} className="flex gap-2.5">
              <div className="w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0"
                style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
                {c.user?.username?.[0]?.toUpperCase()}
              </div>
              <div className="flex-1 bg-white/[0.03] rounded-xl px-3 py-2">
                <span className="text-[11px] font-bold text-indigo-300 mr-1.5">{c.user?.username}</span>
                <span className="text-xs text-white/60">{c.content}</span>
              </div>
            </div>
          ))}
          {comments.length === 0 && (
            <p className="text-xs text-white/25 text-center py-2">Chưa có bình luận nào</p>
          )}
          {isAuthenticated && (
            <form onSubmit={handleComment} className="flex gap-2 mt-2">
              <input className="input-field flex-1 text-xs py-2" placeholder="Viết bình luận..."
                value={newComment} onChange={e => setNewComment(e.target.value)} />
              <button type="submit" disabled={!newComment.trim() || submitting}
                className="btn-primary px-3 py-2 text-xs shrink-0">Gửi</button>
            </form>
          )}
        </div>
      )}
    </article>
  )
}

// ── Create Post Form ──────────────────────────────────────────────────────────
function CreatePostForm({ user, onPosted }) {
  const [content, setContent] = useState('')
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [songQuery, setSongQuery] = useState('')
  const [songResults, setSongResults] = useState([])
  const [selectedSong, setSelectedSong] = useState(null)
  const [showSongPicker, setShowSongPicker] = useState(false)
  const [posting, setPosting] = useState(false)
  const fileRef = useRef()
  const songTimerRef = useRef()

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
      setSelectedSong(null); setSongQuery(''); setSongResults([])
      toast.success('Đã đăng! 🎉')
    } catch { toast.error('Không thể đăng bài') }
    setPosting(false)
  }

  return (
    <div className="glass-card p-4">
      <form onSubmit={handlePost}>
        <div className="flex gap-3 mb-3">
          <Avatar user={user} />
          <textarea
            placeholder="Chia sẻ cảm nhận âm nhạc hôm nay..."
            value={content} onChange={e => setContent(e.target.value)}
            rows={2}
            className="input-field resize-none text-sm flex-1"
          />
        </div>

        {/* Image preview */}
        {imagePreview && (
          <div className="relative mb-3 ml-13 rounded-xl overflow-hidden border border-white/10 w-fit">
            <img src={imagePreview} alt="preview" className="max-h-48 rounded-xl object-cover" />
            <button type="button"
              onClick={() => { setImageFile(null); setImagePreview(null) }}
              className="absolute top-2 right-2 w-6 h-6 bg-black/70 rounded-full flex items-center justify-center text-white hover:bg-black/90 transition-colors">
              <FiX size={11} />
            </button>
          </div>
        )}

        {/* Selected song */}
        {selectedSong && (
          <div className="flex items-center gap-3 mb-3 p-2.5 bg-white/[0.04] border border-white/[0.07] rounded-xl">
            <MdMusicNote className="text-violet-400 shrink-0" size={16} />
            <span className="text-sm text-white/80 flex-1 truncate">{selectedSong.title} — {selectedSong.artist?.username}</span>
            <button type="button" onClick={() => setSelectedSong(null)}
              className="text-white/30 hover:text-white/70 transition-colors">
              <FiX size={14} />
            </button>
          </div>
        )}

        {/* Song search dropdown */}
        {showSongPicker && (
          <div className="mb-3 relative">
            <input
              className="input-field text-sm py-2"
              placeholder="Tìm bài hát để đính kèm..."
              value={songQuery}
              onChange={e => handleSongSearch(e.target.value)}
              autoFocus
            />
            {songResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 z-20 mt-1 bg-[rgba(18,18,36,0.98)] border border-white/10 rounded-xl overflow-hidden shadow-xl backdrop-blur-sm">
                {songResults.map(s => (
                  <button key={s.id} type="button"
                    onClick={() => { setSelectedSong(s); setShowSongPicker(false); setSongQuery(''); setSongResults([]) }}
                    className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/[0.05] transition-colors text-left">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shrink-0 overflow-hidden">
                      {s.cover_image_url
                        ? <img src={s.cover_image_url} className="w-full h-full object-cover" alt="" />
                        : <span className="text-xs">🎵</span>}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm text-white truncate">{s.title}</p>
                      <p className="text-xs text-white/35">{s.artist?.username}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Toolbar */}
        <div className="flex items-center justify-between">
          <div className="flex gap-1">
            {/* Image upload */}
            <button type="button"
              onClick={() => fileRef.current?.click()}
              className={clsx('btn-icon w-8 h-8 text-sm transition-colors',
                imageFile ? 'text-indigo-400' : 'text-white/35 hover:text-white/70')}>
              <FiImage size={14} />
            </button>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleImageChange} />

            {/* Song attach */}
            <button type="button"
              onClick={() => setShowSongPicker(!showSongPicker)}
              className={clsx('btn-icon w-8 h-8 text-sm transition-colors',
                selectedSong || showSongPicker ? 'text-indigo-400' : 'text-white/35 hover:text-white/70')}>
              <FiMusic size={14} />
            </button>
          </div>

          <button type="submit" disabled={!content.trim() || posting}
            className="btn-primary px-5 py-2 text-sm">
            {posting ? 'Đang đăng...' : 'Đăng'}
          </button>
        </div>
      </form>
    </div>
  )
}

// ── FeedPage ─────────────────────────────────────────────────────────────────
export default function FeedPage() {
  const { user, isAuthenticated } = useAuthStore()
  const [posts, setPosts] = useState([])
  const [allPosts, setAllPosts] = useState([])
  const [tab, setTab] = useState('all')
  const [loading, setLoading] = useState(true)
  // Pagination
  const [pageAll, setPageAll] = useState(1)
  const [pageFeed, setPageFeed] = useState(1)
  const [hasMoreAll, setHasMoreAll] = useState(false)
  const [hasMoreFeed, setHasMoreFeed] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  const loadInitial = async () => {
    setLoading(true)
    try {
      const [a, f] = await Promise.all([
        api.get('/social/posts/?page=1'),
        api.get('/social/posts/?feed=1&page=1'),
      ])
      const aData = Array.isArray(a.data?.results) ? a.data.results : (Array.isArray(a.data) ? a.data : [])
      const fData = Array.isArray(f.data?.results) ? f.data.results : (Array.isArray(f.data) ? f.data : [])
      setAllPosts(aData)
      setPosts(fData)
      setHasMoreAll(!!a.data?.next)
      setHasMoreFeed(!!f.data?.next)
      setPageAll(1); setPageFeed(1)
    } catch { toast.error('Không thể tải bảng tin') }
    setLoading(false)
  }

  useEffect(() => { loadInitial() }, [])

  const loadMore = async () => {
    if (loadingMore) return
    setLoadingMore(true)
    try {
      if (tab === 'all') {
        const nextPage = pageAll + 1
        const { data } = await api.get(`/social/posts/?page=${nextPage}`)
        const rawPosts = data?.results || data
        const newPosts = Array.isArray(rawPosts) ? rawPosts : []
        setAllPosts(p => [...p, ...newPosts])
        setHasMoreAll(!!data?.next)
        setPageAll(nextPage)
      } else {
        const nextPage = pageFeed + 1
        const { data } = await api.get(`/social/posts/?feed=1&page=${nextPage}`)
        const rawPosts = data?.results || data
        const newPosts = Array.isArray(rawPosts) ? rawPosts : []
        setPosts(p => [...p, ...newPosts])
        setHasMoreFeed(!!data?.next)
        setPageFeed(nextPage)
      }
    } catch { toast.error('Lỗi tải thêm bài') }
    setLoadingMore(false)
  }

  const handlePosted = (newPost) => {
    setAllPosts(p => [newPost, ...p])
    setPosts(p => [newPost, ...p])
  }

  const handleDelete = (postId) => {
    setAllPosts(p => p.filter(x => x.id !== postId))
    setPosts(p => p.filter(x => x.id !== postId))
  }

  const display = tab === 'feed' ? posts : allPosts
  const hasMore = tab === 'feed' ? hasMoreFeed : hasMoreAll

  return (
    <div className="p-6 max-w-2xl mx-auto animate-fade-in space-y-5">
      <h1 className="text-2xl font-black text-white">Bảng tin</h1>

      {/* Create post */}
      {isAuthenticated && user && (
        <CreatePostForm user={user} onPosted={handlePosted} />
      )}

      {/* Tabs */}
      <div className="flex gap-1.5 p-1 bg-white/[0.04] rounded-xl border border-white/[0.06] w-fit">
        {[['all', 'Tất cả'], ['feed', 'Đang theo dõi']].map(([k, l]) => (
          <button key={k} onClick={() => setTab(k)}
            className={clsx('px-4 py-2 rounded-lg text-sm font-semibold transition-all',
              tab === k ? 'bg-indigo-600 text-white shadow-sm' : 'text-white/40 hover:text-white')}>
            {l}
          </button>
        ))}
      </div>

      {/* Posts */}
      {loading
        ? [...Array(3)].map((_, i) => <div key={i} className="glass-card h-40 animate-shimmer" />)
        : display.length === 0
          ? <div className="text-center py-20">
            <p className="text-4xl mb-3">📭</p>
            <p className="text-white/40 font-semibold">
              {tab === 'feed' ? 'Theo dõi ai đó để xem bài của họ' : 'Chưa có bài đăng nào'}
            </p>
          </div>
          : <>
            {display.map(p => (
              <PostCard key={p.id} post={p} onDelete={handleDelete} />
            ))}

            {/* Load more */}
            {hasMore && (
              <div className="text-center pt-2">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="btn-ghost border border-white/10 flex items-center gap-2 mx-auto text-sm px-6 py-2.5">
                  {loadingMore
                    ? <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                    : <FiChevronDown size={16} />
                  }
                  {loadingMore ? 'Đang tải...' : 'Xem thêm'}
                </button>
              </div>
            )}
          </>
      }
    </div>
  )
}
