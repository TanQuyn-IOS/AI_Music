import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiUploadCloud, FiMusic, FiImage, FiCheck } from 'react-icons/fi'
import api from '../api/axios'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const GENRES = ['vpop', 'ballad', 'lofi', 'acoustic', 'bolero', 'kpop', 'jpop', 'cpop', 'pop', 'rock', 'jazz', 'classical', 'hip_hop', 'r&b', 'electronic', 'country', 'folk', 'metal', 'indie', 'blues', 'latin', 'other']
const GENRE_LABELS = { vpop: 'V-Pop', ballad: 'Ballad', lofi: 'Lo-Fi', acoustic: 'Acoustic', bolero: 'Bolero', kpop: 'K-Pop', jpop: 'J-Pop', cpop: 'C-Pop', pop: 'Pop', rock: 'Rock', jazz: 'Jazz', classical: 'Classical', hip_hop: 'Hip Hop', 'r&b': 'R&B', electronic: 'Electronic', country: 'Country', folk: 'Folk', metal: 'Metal', indie: 'Indie', blues: 'Blues', latin: 'Latin', other: 'Khác' }
const MOODS = ['happy', 'sad', 'energetic', 'calm', 'romantic', 'angry', 'melancholic', 'uplifting']
const MOOD_LABELS = { happy: '😄 Vui vẻ', sad: '😢 Buồn', energetic: '⚡ Năng động', calm: '🌿 Thư giãn', romantic: '💕 Lãng mạn', angry: '🔥 Mạnh mẽ', melancholic: '🌙 Hoài niệm', uplifting: '🌟 Phấn khởi' }

export default function UploadPage() {
  const [form, setForm] = useState({ title: '', genre: 'other', mood: '', tempo: '', duration: '', description: '', lyrics: '', audio_url: '', is_published: true })
  const [audioFile, setAudioFile] = useState(null)
  const [coverImage, setCoverImage] = useState(null)
  const [coverPreview, setCoverPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const navigate = useNavigate()

  const handleCover = (file) => { setCoverImage(file); setCoverPreview(URL.createObjectURL(file)) }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.title.trim()) return toast.error('Nhập tên bài hát')
    if (!audioFile && !form.audio_url.trim()) return toast.error('Thêm file nhạc hoặc URL')
    setLoading(true)
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => {
      if (v === '' || v === null || v === undefined) return
      // is_published phải gửi là string '1'/'0' vì FormData không hỗ trợ boolean
      if (k === 'is_published') {
        fd.append(k, v ? 'true' : 'false')
      } else {
        fd.append(k, v)
      }
    })
    if (audioFile) fd.append('audio_file', audioFile)
    if (coverImage) fd.append('cover_image', coverImage)
    try {
      const { data } = await api.post('/music/songs/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      toast.success('Đã đăng bài thành công! 🎉')
      navigate(`/songs/${data.id}`)
    } catch (err) {
      const msg = !err.response
        ? 'Không thể kết nối đến máy chủ backend (Port 8000). Vui lòng kiểm tra server!'
        : (err.response?.data ? Object.values(err.response.data).flat()[0] : 'Lỗi khi đăng bài')
      toast.error(msg)
    }
    setLoading(false)
  }

  return (
    <div className="p-6 max-w-2xl mx-auto animate-fade-in">
      <div className="mb-7">
        <h1 className="text-2xl font-black text-white flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, #4f46e5, #22d3ee)' }}>
            <FiUploadCloud className="text-white" size={16} />
          </div>
          Đăng bài hát
        </h1>
        <p className="text-white/35 text-sm mt-1.5">Chia sẻ âm nhạc của bạn với cộng đồng</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Cover + title */}
        <div className="glass-card p-5 flex gap-5 items-start">
          <label className="cursor-pointer shrink-0">
            <div className={clsx(
              'w-32 h-32 rounded-2xl overflow-hidden border-2 border-dashed transition-all',
              coverPreview ? 'border-transparent' : 'border-white/10 hover:border-indigo-500/50 bg-white/[0.03]'
            )}>
              {coverPreview
                ? <img src={coverPreview} className="w-full h-full object-cover" alt="cover" />
                : <div className="w-full h-full flex flex-col items-center justify-center gap-2 text-white/30 hover:text-indigo-400 transition-colors">
                  <FiImage size={24} /><span className="text-[10px]">Ảnh bìa</span>
                </div>
              }
            </div>
            <input type="file" accept="image/*" onChange={e => e.target.files[0] && handleCover(e.target.files[0])} className="hidden" />
          </label>

          <div className="flex-1 space-y-3">
            <div>
              <label className="text-xs text-white/40 mb-1.5 block font-medium">Tên bài hát *</label>
              <input className="input-field" placeholder="Nhập tên bài hát..."
                value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block font-medium">Mô tả</label>
              <input className="input-field text-sm" placeholder="Mô tả ngắn..."
                value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
            </div>
          </div>
        </div>

        {/* Audio upload */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-bold text-white">🎵 File nhạc</h3>

          {/* Drop zone */}
          <label
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f?.type.startsWith('audio')) setAudioFile(f) }}
            className={clsx(
              'flex flex-col items-center gap-2 p-6 rounded-xl border-2 border-dashed cursor-pointer transition-all',
              dragOver ? 'border-indigo-500 bg-indigo-500/10' : audioFile ? 'border-emerald-500/40 bg-emerald-500/5' : 'border-white/10 hover:border-indigo-500/40 hover:bg-white/[0.02]'
            )}>
            {audioFile
              ? <><FiCheck size={24} className="text-emerald-400" /><p className="text-sm text-emerald-400 font-medium">{audioFile.name}</p><p className="text-xs text-white/30">Nhấn để đổi file</p></>
              : <><FiUploadCloud size={24} className="text-white/25" /><p className="text-sm text-white/60 font-medium">Kéo thả hoặc nhấn để chọn file</p><p className="text-xs text-white/25">MP3, WAV, FLAC (max 50MB)</p></>
            }
            <input type="file" accept="audio/*" onChange={e => setAudioFile(e.target.files[0])} className="hidden" />
          </label>

          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-white/[0.06]" />
            <span className="text-xs text-white/25 shrink-0">hoặc dùng URL</span>
            <div className="flex-1 h-px bg-white/[0.06]" />
          </div>
          <input className="input-field text-sm" placeholder="https://example.com/song.mp3"
            value={form.audio_url} onChange={e => setForm({ ...form, audio_url: e.target.value })} />
        </div>

        {/* Genre + Mood */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-bold text-white">📋 Thể loại & Tâm trạng</h3>
          <div>
            <label className="text-xs text-white/40 mb-2 block">Thể loại</label>
            <div className="flex flex-wrap gap-2">
              {GENRES.map(g => (
                <button type="button" key={g} onClick={() => setForm({ ...form, genre: g })}
                  className={clsx('px-3 py-1.5 rounded-full text-xs font-medium transition-all border',
                    form.genre === g ? 'bg-indigo-600 text-white border-indigo-500' : 'border-white/[0.07] text-white/40 hover:text-white hover:border-white/15')}>
                  {GENRE_LABELS[g]}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="text-xs text-white/40 mb-2 block">Tâm trạng bài hát</label>
            <div className="grid grid-cols-4 gap-2">
              {MOODS.map(m => (
                <button type="button" key={m} onClick={() => setForm({ ...form, mood: form.mood === m ? '' : m })}
                  className={clsx('py-2 rounded-xl text-xs font-medium transition-all border text-center',
                    form.mood === m ? 'bg-fuchsia-600/20 border-fuchsia-500/40 text-fuchsia-300' : 'border-white/[0.06] text-white/40 hover:border-white/10 hover:text-white')}>
                  {MOOD_LABELS[m]}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="glass-card p-5 space-y-4">
          <h3 className="text-sm font-bold text-white">🔢 Thông tin kỹ thuật</h3>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Tempo (BPM)</label>
              <input type="number" className="input-field text-sm" placeholder="120"
                value={form.tempo} onChange={e => setForm({ ...form, tempo: e.target.value })} />
            </div>
            <div>
              <label className="text-xs text-white/40 mb-1.5 block">Thời lượng (giây)</label>
              <input type="number" className="input-field text-sm" placeholder="240"
                value={form.duration} onChange={e => setForm({ ...form, duration: e.target.value })} />
            </div>
          </div>
          <div>
            <label className="text-xs text-white/40 mb-1.5 block">Lời bài hát</label>
            <textarea className="input-field resize-none text-sm" rows={5}
              placeholder="Nhập lời bài hát..."
              value={form.lyrics} onChange={e => setForm({ ...form, lyrics: e.target.value })} />
          </div>

          <label className="flex items-center gap-3 cursor-pointer group">
            <div onClick={() => setForm({ ...form, is_published: !form.is_published })}
              className={clsx('w-11 h-6 rounded-full transition-all relative', form.is_published ? 'bg-indigo-600' : 'bg-white/10')}>
              <div className={clsx('absolute top-1 w-4 h-4 bg-white rounded-full shadow transition-all', form.is_published ? 'left-6' : 'left-1')} />
            </div>
            <div>
              <p className="text-sm font-medium text-white/80">Công khai bài hát</p>
              <p className="text-xs text-white/30">{form.is_published ? 'Mọi người có thể nghe' : 'Chỉ mình bạn thấy'}</p>
            </div>
          </label>
        </div>

        <button type="submit" disabled={loading}
          className="btn-primary w-full py-3.5 text-base flex items-center justify-center gap-2">
          {loading
            ? <><span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Đang đăng bài...</>
            : <><FiUploadCloud size={18} />Đăng bài hát</>
          }
        </button>
      </form>
    </div>
  )
}
