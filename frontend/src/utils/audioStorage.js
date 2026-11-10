const DB_NAME = 'SonaviaAudioDB'
const DB_VERSION = 1
const STORE_NAME = 'tracks'

function openDB() {
  return new Promise((resolve, reject) => {
    if (typeof window === 'undefined' || !window.indexedDB) {
      return reject(new Error('IndexedDB not supported'))
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION)
    request.onupgradeneeded = (e) => {
      const db = e.target.result
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' })
      }
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error)
  })
}

/**
 * Lưu Audio Blob vào IndexedDB để bài hát không bị mất khi reload hoặc mở lại web
 */
export async function saveTrackAudioBlob(id, blob) {
  try {
    const db = await openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const request = store.put({ id: String(id), blob, savedAt: Date.now() })
      request.onsuccess = () => resolve(true)
      request.onerror = () => reject(request.error)
    })
  } catch (err) {
    console.warn('saveTrackAudioBlob failed:', err)
    return false
  }
}

/**
 * Lấy Audio Blob từ IndexedDB
 */
export async function getTrackAudioBlob(id) {
  try {
    const db = await openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readonly')
      const store = tx.objectStore(STORE_NAME)
      const request = store.get(String(id))
      request.onsuccess = () => {
        resolve(request.result?.blob || null)
      }
      request.onerror = () => reject(request.error)
    })
  } catch (err) {
    console.warn('getTrackAudioBlob failed:', err)
    return null
  }
}

/**
 * Xóa Audio Blob khỏi IndexedDB khi người dùng bấm xóa bài hát
 */
export async function deleteTrackAudioBlob(id) {
  try {
    const db = await openDB()
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, 'readwrite')
      const store = tx.objectStore(STORE_NAME)
      const request = store.delete(String(id))
      request.onsuccess = () => resolve(true)
      request.onerror = () => reject(request.error)
    })
  } catch (err) {
    console.warn('deleteTrackAudioBlob failed:', err)
    return false
  }
}
