import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { FiUserPlus, FiUserCheck, FiEdit2, FiMusic, FiList, FiMessageSquare } from 'react-icons/fi'
import { MdAutoAwesome } from 'react-icons/md'
import api from '../api/axios'
import useAuthStore from '../store/authStore'
import SongCard from '../components/music/SongCard'
import EditProfileModal from '../components/user/EditProfileModal'
import MessagesDrawer from '../components/social/MessagesDrawer'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const COVER_GRADIENTS = [
  'from-indigo-600 to-violet-600', 'from-blue-600 to-cyan-500',
  'from-violet-600 to-indigo-500', 'from-teal-600 to-cyan-600',
]

const TABS = [
  { key: 'songs', label: 'Bài hát', icon: FiMusic },
  { key: 'playlists', label: 'Playlist', icon: FiList },
  { key: 'profile', label: 'Hồ sơ AI', icon: MdAutoAwesome, onlyMe: true },
]

export default function ProfilePage() {
  const { username } = useParams()
  const { user: me, isAuthenticated } = useAuthStore()
  const [profile, setProfile] = useState(null)
  const [songs, setSongs] = useState([])
  const [playlists, setPlaylists] = useState([])
  const [musicProfile, setMusicProfile] = useState(null)
  const [tab, setTab] = useState('songs')
  const [following, setFollowing] = useState(false)
  const [followersCount, setFollowersCount] = useState(0)
  const [showEdit, setShowEdit] = useState(false)
  const [showMessages, setShowMessages] = useState(false)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)

  const isMe = me?.username === username
  const grad = COVER_GRADIENTS[(username?.charCodeAt(0) || 0) % COVER_GRADIENTS.length]

  useEffect(() => {
    setTab('songs')
    setLoading(true)
    setNotFound(false)
    const loadAll = async () => {
      try {
        const [pRes, sRes, plRes] = await Promise.all([
          api.get(`/auth/users/${username}/`),
          api.get(`/music/songs/?artist__username=${username}`),
          api.get(`/music/playlists/?user=${username}`),
        ])
        setProfile(pRes.data)
        setFollowing(pRes.data.is_following)
        setFollowersCount(pRes.data.followers_count)
        const sList = sRes.data?.results || sRes.data
        const plList = plRes.data?.results || plRes.data
        setSongs(Array.isArray(sList) ? sList : [])
        setPlaylists(Array.isArray(plList) ? plList : [])
      } catch (err) {
        if (err.response?.status === 404) {
          setNotFound(true)
        } else if (!err.response) {
          toast.error('Không thể kết nối đến máy chủ backend (Port 8000)')
        } else {
          toast.error('Không thể tải hồ sơ người dùng')
        }
      } finally {
        setLoading(false)
      }
    }
    loadAll()
    if (isMe) api.get('/ai/profile/').then(r => setMusicProfile(r.data)).catch(() => { })
  }, [username, isMe])

  const handleFollow = async () => {
    if (!isAuthenticated) return toast.error('Vui lòng đăng nhập')
    try {
      const { data } = await api.post(`/auth/users/${username}/follow/`)
      setFollowing(data.following)
      setFollowersCount(data.followers_count)
      toast.success(data.following ? '✅ Đang theo dõi' : 'Đã bỏ theo dõi')
    } catch { toast.error('Lỗi') }
  }

  if (loading) return (
    <div className="animate-pulse">
      <div className="h-56 skeleton" />
      <div className="px-6 -mt-16 flex gap-4">
        <div className="w-28 h-28 rounded-3xl skeleton" />
        <div className="flex-1 pt-20 space-y-2">
          <div className="h-6 skeleton rounded w-1/3" />
          <div className="h-4 skeleton rounded w-1/5" />
        </div>
      </div>
    </div>
  )

  if (notFound || !profile) return (
    <div className="p-12 text-center max-w-md mx-auto my-12 glass-card rounded-3xl animate-fade-in">
      <div className="w-16 h-16 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-3xl mb-4">
        👤
      </div>
      <h2 className="text-xl font-bold text-white mb-2">Không tìm thấy người dùng</h2>
      <p className="text-white/40 text-sm mb-6">
        Người dùng <span className="text-indigo-400 font-semibold">@{username}</span> không tồn tại hoặc đã thay đổi tên tài khoản.
      </p>
      <Link to="/" className="btn-primary inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold">
        Quay lại Trang chủ
      </Link>
    </div>
  )

  return (
    <div className="animate-fade-in">
      {showEdit && (
        <EditProfileModal
          onClose={() => setShowEdit(false)}
          onUpdated={(updated) => setProfile(prev => ({ ...prev, ...updated }))}
        />
      )}
      {showMessages && (
        <MessagesDrawer
          isOpen={showMessages}
          onClose={() => setShowMessages(false)}
          initialTargetUsername={profile.username}
        />
      )}

      {/* ── Cover ── */}
      <div className="relative h-56 overflow-hidden">
        {profile.cover_image_url
          ? <img src={profile.cover_image_url} className="w-full h-full object-cover" alt="cover" />
          : <div className={`w-full h-full bg-gradient-to-br ${grad} opacity-40`} />
        }
        {/* Purple tint overlay */}
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#070711]/30 to-[#070711]" />
        {/* Subtle blob */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30">
          <div className={`w-96 h-96 bg-gradient-to-br ${grad} rounded-full blur-3xl`} />
        </div>
      </div>

      {/* ── Profile header ── */}
      <div className="px-6 pb-0">
        <div className="flex items-end gap-5 -mt-16 mb-4">
          {/* Avatar */}
          <div className="relative shrink-0">
            <div className={`absolute inset-0 bg-gradient-to-br ${grad} rounded-3xl blur-md opacity-60 scale-110`} />
            <div className="relative w-28 h-28 rounded-3xl overflow-hidden border-4 border-[#070711]">
              {profile.avatar_url
                ? <img src={profile.avatar_url} alt={profile.username} className="w-full h-full object-cover" />
                : <div className={`w-full h-full bg-gradient-to-br ${grad} flex items-center justify-center text-4xl font-black text-white`}>
                  {profile.username?.[0]?.toUpperCase() || '?'}
                </div>
              }
            </div>
            {/* Online dot */}
            <div className="absolute bottom-2 right-2 w-4 h-4 bg-emerald-400 rounded-full border-2 border-[#070711]" />
          </div>

          {/* Name + actions */}
          <div className="flex-1 min-w-0 pb-1">
            <div className="flex items-start justify-between flex-wrap gap-3">
              <div>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <h1 className="text-2xl font-black text-white leading-none">
                    {(profile.first_name || profile.last_name)
                      ? `${profile.first_name} ${profile.last_name}`.trim()
                      : profile.username}
                  </h1>
                  {profile.is_artist && (
                    <span className="badge badge-purple">🎤 Nghệ sĩ</span>
                  )}
                </div>
                <p className="text-sm text-white/35 mt-1">@{profile.username}</p>
              </div>

              {isMe ? (
                <button onClick={() => setShowEdit(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-white/70 hover:text-white text-sm font-medium transition-all">
                  <FiEdit2 size={13} /> Chỉnh sửa
                </button>
              ) : (
                <div className="flex items-center gap-2.5">
                  <button onClick={handleFollow}
                    className={clsx('flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all',
                      following
                        ? 'bg-white/5 border border-white/10 text-white/60 hover:bg-red-500/10 hover:text-red-400 hover:border-red-500/20'
                        : 'btn-primary')}>
                    {following ? <><FiUserCheck size={14} /> Đang theo dõi</> : <><FiUserPlus size={14} /> Theo dõi</>}
                  </button>

                  {/* Nút Nhắn tin riêng (Direct Messaging) */}
                  {isAuthenticated && (
                    <button
                      onClick={() => setShowMessages(true)}
                      className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 text-cyan-300 text-sm font-semibold transition-all shadow-md shadow-cyan-500/10"
                    >
                      <FiMessageSquare size={14} />
                      <span>Nhắn tin</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Bio */}
        {profile.bio && (
          <p className="text-sm text-white/50 mb-4 max-w-xl leading-relaxed">{profile.bio}</p>
        )}

        {/* Stats bar */}
        <div className="flex items-center gap-6 py-4 border-y border-white/[0.06] text-sm mb-6 flex-wrap">
          <div>
            <span className="font-bold text-white text-base">{followersCount}</span>
            <span className="text-white/40 ml-1.5 text-xs">người theo dõi</span>
          </div>
          <div className="w-px h-4 bg-white/10" />
          <div>
            <span className="font-bold text-white text-base">{profile.following_count ?? 0}</span>
            <span className="text-white/40 ml-1.5 text-xs">đang theo dõi</span>
          </div>
          <div className="w-px h-4 bg-white/10" />
          <div>
            <span className="font-bold text-white text-base">{songs.length}</span>
            <span className="text-white/40 ml-1.5 text-xs">bài hát</span>
          </div>
          <div className="w-px h-4 bg-white/10" />
          <div>
            <span className="font-bold text-white text-base">{playlists.length}</span>
            <span className="text-white/40 ml-1.5 text-xs">playlist</span>
          </div>
        </div>

        {/* Favorite genres */}
        {profile.favorite_genres?.length > 0 && (
          <div className="flex items-center gap-2 mb-6 flex-wrap">
            <span className="text-xs text-white/30">Thể loại yêu thích:</span>
            {profile.favorite_genres.map(g => (
              <span key={g} className="badge badge-purple">{g}</span>
            ))}
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 border-b border-white/[0.06] mb-6">
          {TABS.filter(t => !t.onlyMe || isMe).map(t => {
            const Icon = t.icon
            return (
              <button key={t.key} onClick={() => setTab(t.key)}
                className={clsx('flex items-center gap-2 pb-3.5 px-3 text-sm font-semibold border-b-2 transition-all',
                  tab === t.key
                    ? 'border-indigo-500 text-white'
                    : 'border-transparent text-white/40 hover:text-white/70'
                )}>
                <Icon size={15} />
                {t.label}
                {t.key === 'songs' && <span className="text-xs text-white/30 font-normal">({songs.length})</span>}
                {t.key === 'playlists' && <span className="text-xs text-white/30 font-normal">({playlists.length})</span>}
              </button>
            )
          })}
        </div>

        {/* Tab content */}
        {tab === 'songs' && (
          <div>
            {songs.length === 0 ? (
              <div className="text-center py-16 text-white/30">
                <FiMusic size={40} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Chưa có bài hát nào</p>
                {isMe && (
                  <Link to="/upload" className="btn-primary inline-block mt-4 text-xs">
                    Tải lên bài hát đầu tiên
                  </Link>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 pb-12">
                {songs.map(song => (
                  <SongCard key={song.id} song={song} queue={songs} />
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'playlists' && (
          <div>
            {playlists.length === 0 ? (
              <div className="text-center py-16 text-white/30">
                <FiList size={40} className="mx-auto mb-3 opacity-30" />
                <p className="text-sm">Chưa có playlist nào</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4 pb-12">
                {playlists.map(pl => (
                  <Link key={pl.id} to={`/playlists/${pl.id}`}
                    className="glass-card-hover rounded-2xl p-4 block group">
                    <div className="aspect-square rounded-xl bg-gradient-to-br from-indigo-900/60 to-purple-900/60 flex items-center justify-center text-3xl mb-3 overflow-hidden">
                      {pl.cover_image
                        ? <img src={pl.cover_image} alt={pl.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                        : '📑'
                      }
                    </div>
                    <p className="font-bold text-white text-sm truncate group-hover:text-indigo-300 transition-colors">{pl.name}</p>
                    <p className="text-xs text-white/40 mt-0.5">{pl.songs_count ?? 0} bài hát</p>
                  </Link>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === 'profile' && isMe && (
          <div className="max-w-xl pb-12">
            <h3 className="font-bold text-white text-base mb-2">Hồ sơ Âm nhạc AI của bạn</h3>
            <p className="text-xs text-white/40 mb-6">
              Dựa trên lịch sử nghe của bạn, AI tự động phân tích và tối ưu gợi ý phù hợp nhất.
            </p>
            {musicProfile ? (
              <MusicProfileCard data={musicProfile} />
            ) : (
              <div className="text-center py-8 text-white/30 text-sm glass-card rounded-2xl">
                Chưa có dữ liệu nghe nhạc. Hãy nghe vài bài hát để AI phân tích gu âm nhạc của bạn!
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function MusicProfileCard({ data }) {
  return (
    <div className="glass-card rounded-2xl p-6 space-y-6">
      <div>
        <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">Thể loại yêu thích hàng đầu</h4>
        <div className="space-y-2">
          {data.top_genres?.slice(0, 5).map(({ genre, count }) => {
            const max = data.top_genres[0]?.count || 1
            const pct = Math.round((count / max) * 100)
            return (
              <div key={genre} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-white uppercase">{genre}</span>
                  <span className="text-white/40">{count} lượt nghe</span>
                </div>
                <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { label: 'Bài đã nghe', value: data.total_songs_listened, color: 'text-indigo-400' },
          { label: 'Tempo TB', value: `${data.avg_tempo} BPM`, color: 'text-cyan-400' },
        ].map(s => (
          <div key={s.label} className="bg-white/[0.04] rounded-xl p-4 text-center border border-white/[0.05]">
            <p className={`text-2xl font-black ${s.color}`}>{s.value}</p>
            <p className="text-[11px] text-white/30 mt-1">{s.label}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
