import { useEffect, useRef } from 'react'

/**
 * RealtimeVisualizer
 * Sử dụng Web Audio API AnalyserNode & Canvas để vẽ sóng âm thanh nhảy theo nhịp điệu bass/treble thật.
 */
export default function RealtimeVisualizer({ analyserRef, isPlaying, barCount = 14, height = 24, width = 72 }) {
  const canvasRef = useRef(null)
  const animationFrameRef = useRef(null)
  const barsDataRef = useRef(new Array(barCount).fill(3))

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const dpr = window.devicePixelRatio || 1
    canvas.width = width * dpr
    canvas.height = height * dpr
    ctx.scale(dpr, dpr)

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      let freqData = null
      if (analyserRef?.current && isPlaying) {
        try {
          const bufferLength = analyserRef.current.frequencyBinCount
          const dataArray = new Uint8Array(bufferLength)
          analyserRef.current.getByteFrequencyData(dataArray)
          freqData = dataArray
        } catch {
          freqData = null
        }
      }

      const barWidth = Math.max(2, (width - (barCount - 1) * 2) / barCount)
      const maxH = height - 2

      for (let i = 0; i < barCount; i++) {
        let targetHeight = 3
        if (freqData && freqData.length > 0) {
          // Lấy dải tần số tương ứng (ưu tiên dải bass ở đầu và mid-treble)
          const binIndex = Math.min(freqData.length - 1, Math.floor((i / barCount) * (freqData.length * 0.75)))
          const val = freqData[binIndex] || 0
          // Chuẩn hóa và thêm non-linear boost cho visual sống động
          const norm = val / 255.0
          targetHeight = Math.max(3, norm * maxH)
        }

        // Làm mượt (lerp smoothing & decay)
        const currentH = barsDataRef.current[i] || 3
        const lerpFactor = targetHeight > currentH ? 0.35 : 0.15
        const newH = currentH + (targetHeight - currentH) * lerpFactor
        barsDataRef.current[i] = newH

        // Tọa độ vẽ cột sóng
        const x = i * (barWidth + 2)
        const y = height - newH

        // Tạo gradient màu Cyan -> Indigo -> Rose sáng bóng
        const grad = ctx.createLinearGradient(0, height, 0, 0)
        grad.addColorStop(0, '#06b6d4') // Cyan-500
        grad.addColorStop(0.6, '#6366f1') // Indigo-500
        grad.addColorStop(1, '#ec4899') // Rose-500

        ctx.fillStyle = grad
        ctx.beginPath()
        if (ctx.roundRect) {
          ctx.roundRect(x, y, barWidth, newH, [2, 2, 0, 0])
        } else {
          ctx.rect(x, y, barWidth, newH)
        }
        ctx.fill()
      }

      animationFrameRef.current = requestAnimationFrame(render)
    }

    render()

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
    }
  }, [analyserRef, isPlaying, barCount, height, width])

  return (
    <canvas
      ref={canvasRef}
      style={{ width: `${width}px`, height: `${height}px` }}
      className="shrink-0 pointer-events-none drop-shadow-[0_0_8px_rgba(6,182,212,0.4)]"
    />
  )
}
