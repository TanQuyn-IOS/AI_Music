import { create } from 'zustand'

const usePlayerStore = create((set, get) => ({
  currentSong: null,
  queue: [],
  originalQueue: [],  // lưu queue gốc để tắt shuffle
  isPlaying: false,
  volume: 0.8,
  currentTime: 0,
  shuffle: false,
  repeat: 'none',     // 'none' | 'all' | 'one'

  playSong: (song, queue = []) => {
    const { shuffle } = get()
    let finalQueue = [...queue]
    if (shuffle && finalQueue.length > 1) {
      const without = finalQueue.filter(s => s.id !== song.id)
      for (let i = without.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [without[i], without[j]] = [without[j], without[i]]
      }
      finalQueue = [song, ...without]
    }
    set({ currentSong: song, queue: finalQueue, originalQueue: queue, isPlaying: true })
  },

  togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),

  playNext: () => {
    const { queue, currentSong, repeat } = get()
    if (!queue.length) return
    if (repeat === 'one') {
      // repeat=one: Player.jsx xử lý restart trực tiếp trên audio element
      set({ isPlaying: true })
      return
    }
    const idx = queue.findIndex(s => s.id === currentSong?.id)
    const isLast = idx === queue.length - 1
    if (isLast && repeat === 'none') {
      set({ isPlaying: false })
      return
    }
    const next = queue[idx + 1] || queue[0]
    set({ currentSong: next, isPlaying: true })
  },

  playPrev: () => {
    const { queue, currentSong } = get()
    if (!queue.length) return
    // Restart bài hiện tại nếu đang phát > 3s — được xử lý ở Player.jsx (handlePrev)
    const idx = queue.findIndex(s => s.id === currentSong?.id)
    const prev = queue[idx - 1] || queue[queue.length - 1]
    set({ currentSong: prev, isPlaying: true })
  },

  toggleShuffle: () => {
    const { shuffle, originalQueue, currentSong } = get()
    if (!shuffle) {
      // Bật shuffle: xáo trộn queue, giữ bài hiện tại đầu tiên
      const without = originalQueue.filter(s => s.id !== currentSong?.id)
      for (let i = without.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [without[i], without[j]] = [without[j], without[i]]
      }
      const shuffled = currentSong ? [currentSong, ...without] : without
      set({ shuffle: true, queue: shuffled })
    } else {
      // Tắt shuffle: khôi phục queue gốc
      set({ shuffle: false, queue: [...get().originalQueue] })
    }
  },

  cycleRepeat: () => {
    const { repeat } = get()
    const next = repeat === 'none' ? 'all' : repeat === 'all' ? 'one' : 'none'
    set({ repeat: next })
  },

  // Nhảy đến bài trong queue hiện tại — không re-shuffle, không reset originalQueue
  jumpToSong: (song) => set({ currentSong: song, isPlaying: true }),

  setVolume: (volume) => set({ volume }),
  setCurrentTime: (t) => set({ currentTime: t }),
  clearPlayer: () => set({ currentSong: null, isPlaying: false, queue: [], originalQueue: [] }),
}))

export default usePlayerStore
