import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  FiSearch, FiUserPlus, FiUserCheck, FiMusic,
  FiUsers, FiTrendingUp,
} from 'react-icons/fi'
import { MdAutoAwesome } from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
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

// ─── UserCard ─────────────────────────────────────────────────────────────────

function UserCard({ user: initialUser }) {
  const { isAuthenticated, user: me } = useAuthStore()
  const [user, setUser] = useState(initialUser)
  const [following, setFollowing] = useState(initialUser.is_following)
  const [loading, setLoading] = useState(false)
  const isMe = me?.username === user.username

  const handleFollow = async () => {
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    if (isMe) return
    setLoading(true)
    try {
      const { data } = await api.post(`/auth/users/${user.username}/follow/`)
      setFollowing(data.following)
      setUser(prev => ({
        ...prev,
        followers_count: data.followers_count,
      }))
      toast.success(data.following ? `✅ Đang theo dõi @${user.username}` : 'Đã bỏ theo dõi')
    } catch { toast.error('Lỗi') }
    setLoading(false)
  }

  const grad = gradOf(user.username)
  const displayName = (user.first_name || user.last_name)
    ? `${user.first_name || ''} ${user.last_name || ''}`.trim()
    : user.username

  return (
    <div className="glass-card overflow-hidden hover:border-white/10 transition-all duration-300 group flex flex-col">
      {/* Cover strip */}
      <div className="relative h-20 overflow-hidden">
        {user.cover_image_url
          ? <img src={user.cover_image_url} className="w-full h-full object-cover scale-105 group-hover:scale-110 transition-transform duration-500" alt="" />
          : <div className={`w-full h-full bg-gradient-to-br ${grad} opacity-50`} />
        }
        <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#070711]" />
      </div>

      {/* Avatar overlapping cover */}
      <div className="px-4 -mt-7 flex items-end justify-between mb-3">
        <Link to={`/profile/${user.username}`} className="relative shrink-0">
          <div className={`absolute inset-0 bg-gradient-to-br ${grad} rounded-2xl blur-md opacity-50 scale-110 group-hover:opacity-70 transition-opacity`} />
          <div className="relative w-14 h-14 rounded-2xl overflow-hidden border-3 border-[#070711] ring-2 ring-white/10">
            {user.avatar_url
              ? <img src={user.avatar_url} className="w-full h-full object-cover" alt={user.username} />
              : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-xl font-black text-white`}>
                {user.username?.[0]?.toUpperCase()}
              </div>
            }
          </div>
          {/* Online indicator */}
          <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-emerald-400 rounded-full border-2 border-[#070711]" />
        </Link>

        {/* Follow button */}
        {!isMe && (
          <button
            onClick={handleFollow}
            disabled={loading}
            className={clsx(
              'flex items-center gap-1.5 px-4 py-1.5 rounded-xl text-xs font-bold transition-all',
              following
                ? 'bg-white/5 border border-white/10 text-white/40 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20'
                : 'btn-primary'
            )}>
            {loading
              ? <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : following
                ? <><FiUserCheck size={11} /> Đang theo dõi</>
                : <><FiUserPlus size={11} /> Theo dõi</>
            }
          </button>
        )}
        {isMe && (
          <Link to="/settings"
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white/5 border border-white/10 text-white/40 hover:text-white transition-colors">
            Chỉnh sửa
          </Link>
        )}
      </div>

      {/* Info */}
      <div className="px-4 pb-4 flex-1 flex flex-col">
        <Link to={`/profile/${user.username}`}>
          <h3 className="font-black text-white text-sm truncate hover:text-violet-300 transition-colors leading-tight">
            {displayName}
          </h3>
        </Link>
        <p className="text-[11px] text-white/30 mb-2">@{user.username}</p>

        {/* Badges */}
        <div className="flex gap-1.5 flex-wrap mb-3">
          {user.is_artist && <span className="badge badge-purple text-[9px]">🎤 Nghệ sĩ</span>}
          {(user.followers_count || 0) >= 100 && (
            <span className="badge bg-amber-500/15 text-amber-300 border border-amber-500/25 text-[9px]">⭐ Nổi bật</span>
          )}
        </div>

        {/* Bio */}
        {user.bio && (
          <p className="text-[11px] text-white/40 leading-relaxed line-clamp-2 mb-3 flex-1">{user.bio}</p>
        )}

        {/* Stats */}
        <div className="flex gap-4 pt-2 border-t border-white/[0.05]">
          {[
            { label: 'followers', value: user.followers_count || 0 },
            { label: 'following', value: user.following_count || 0 },
          ].map(({ label, value }) => (
            <div key={label}>
              <span className="text-sm font-black text-white">{value.toLocaleString()}</span>
              <span className="text-[10px] text-white/30 ml-1">{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function UserCardSkeleton() {
  return (
    <div className="glass-card overflow-hidden animate-pulse">
      <div className="h-20 skeleton" />
      <div className="px-4 -mt-7 mb-3 flex items-end justify-between">
        <div className="w-14 h-14 skeleton rounded-2xl" />
        <div className="w-20 h-7 skeleton rounded-xl" />
      </div>
      <div className="px-4 pb-4 space-y-2">
        <div className="h-3 skeleton rounded w-2/3" />
        <div className="h-2 skeleton rounded w-1/3" />
        <div className="h-8 skeleton rounded" />
        <div className="h-2 skeleton rounded w-1/2" />
      </div>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const FILTERS = [
  { key: 'all', label: 'Tất cả', icon: FiUsers },
  { key: 'artists', label: 'Nghệ sĩ', icon: FiMusic },
  { key: 'suggested', label: 'Gợi ý', icon: MdAutoAwesome },
  { key: 'trending', label: 'Nổi bật', icon: FiTrendingUp },
]

export default function PeoplePage() {
  const { isAuthenticated } = useAuthStore()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const searchTimerRef = useRef()

  const fetchUsers = async (reset = true, searchVal = search, filterVal = filter) => {
    if (reset) setLoading(true)
    else setLoadingMore(true)

    try {
      const p = reset ? 1 : page + 1
      let url = ''

      if (filterVal === 'suggested' && isAuthenticated) {
        url = `/social/users/suggested/?limit=20`
      } else if (filterVal === 'trending') {
        url = `/social/users/active/`
      } else {
        const params = new URLSearchParams()
        if (searchVal) params.set('search', searchVal)
        if (filterVal === 'artists') params.set('is_artist', '1')
        params.set('page', p)
        url = `/auth/users/?${params}`
      }

      const { data } = await api.get(url)
      const results = data.results || data
      const count = data.count ?? results.length

      if (reset) {
        setUsers(results)
        setPage(1)
      } else {
        setUsers(prev => [...prev, ...results])
        setPage(p)
      }
      setHasMore(!!data.next)
      setTotalCount(count)
    } catch { toast.error('Không thể tải danh sách') }

    if (reset) setLoading(false)
    else setLoadingMore(false)
  }

  // Initial load & filter change
  useEffect(() => { fetchUsers(true, search, filter) }, [filter, isAuthenticated])

  // Debounced search
  useEffect(() => {
    clearTimeout(searchTimerRef.current)
    searchTimerRef.current = setTimeout(() => {
      fetchUsers(true, search, filter)
    }, 400)
    return () => clearTimeout(searchTimerRef.current)
  }, [search])

  return (
    <div className="animate-fade-in min-h-full">
      {/* ── Hero ── */}
      <div className="relative overflow-hidden px-6 pt-7 pb-6 border-b border-white/[0.05]">
        <div className="absolute -top-10 left-1/4 w-72 h-72 bg-fuchsia-600/10 rounded-full blur-[70px] pointer-events-none" />
        <div className="relative max-w-screen-xl mx-auto">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 bg-gradient-to-br from-fuchsia-500 to-pink-500 rounded-xl flex items-center justify-center">
              <FiUsers size={18} className="text-white" />
            </div>
            <h1 className="text-2xl font-black text-white">Mọi người</h1>
          </div>
          <p className="text-white/40 text-sm ml-12">
            Khám phá và kết nối với cộng đồng âm nhạc
          </p>
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-6 py-6">
        {/* ── Search + Filter ── */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-white/25 text-sm" />
            <input
              type="text"
              placeholder="Tìm theo tên, username..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input-field pl-9 text-sm w-full"
            />
            {search && (
              <button onClick={() => setSearch('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white transition-colors text-sm">
                ✕
              </button>
            )}
          </div>

          {/* Filter pills */}
          <div className="flex gap-2 flex-wrap">
            {FILTERS.map(({ key, label, icon: Icon }) => (
              <button key={key} onClick={() => setFilter(key)}
                className={clsx(
                  'flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold border transition-all',
                  filter === key
                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-900/30'
                    : 'bg-white/[0.04] border-white/[0.07] text-white/45 hover:text-white hover:border-white/15'
                )}>
                <Icon size={12} />
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Result count */}
        {!loading && users.length > 0 && (
          <p className="text-xs text-white/25 mb-4 font-medium">
            {totalCount > 0 ? `${totalCount.toLocaleString()} người dùng` : `${users.length} kết quả`}
            {search && <span className="text-indigo-400"> cho "{search}"</span>}
          </p>
        )}

        {/* ── User Grid ── */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => <UserCardSkeleton key={i} />)}
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-24">
            <div className="text-6xl mb-4">
              {search ? '🔍' : filter === 'suggested' ? '💡' : '👥'}
            </div>
            <p className="text-white/50 font-bold text-lg mb-2">
              {search
                ? `Không tìm thấy "${search}"`
                : filter === 'suggested'
                  ? 'Đăng nhập để xem gợi ý'
                  : 'Chưa có người dùng nào'
              }
            </p>
            <p className="text-white/25 text-sm">
              {!isAuthenticated && filter === 'suggested'
                ? 'Đăng nhập để nhận gợi ý follow phù hợp với bạn'
                : 'Thử tìm kiếm với từ khoá khác'
              }
            </p>
            {!isAuthenticated && (
              <Link to="/login" className="btn-primary mt-5 inline-flex items-center gap-2 text-sm">
                Đăng nhập ngay
              </Link>
            )}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {users.map(u => <UserCard key={u.id} user={u} />)}
            </div>

            {/* Load more */}
            {hasMore && (
              <div className="text-center mt-8">
                <button onClick={() => fetchUsers(false)} disabled={loadingMore}
                  className="btn-ghost border border-white/10 px-8 py-2.5 text-sm flex items-center gap-2 mx-auto">
                  {loadingMore
                    ? <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
                    : <FiUsers size={14} />
                  }
                  {loadingMore ? 'Đang tải...' : 'Xem thêm'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
