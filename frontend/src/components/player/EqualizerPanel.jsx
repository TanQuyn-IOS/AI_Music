import { useState } from 'react'
import { FiX, FiSliders, FiVolume2, FiCheck } from 'react-icons/fi'
import { MdGraphicEq, MdSpeed } from 'react-icons/md'
import clsx from 'clsx'

export const EQ_PRESETS = {
  studio: {
    id: 'studio',
    name: 'Phòng Thu Studio HD',
    icon: '🎧',
    desc: 'Cân bằng, bass chắc nịch, mid ấm mượt, treble trong suốt',
    bass: 3.5,
    mid: 1.0,
    presence: 2.5,
    treble: 3.0,
    gain: 1.05,
    compressor: true,
  },
  bass: {
    id: 'bass',
    name: 'Siêu Trầm Uy Lực (Bass Boost)',
    icon: '🔊',
    desc: 'Tăng cường dải siêu trầm 80Hz sâu, dày và bốc lửa cho EDM/Pop/Hip-Hop',
    bass: 7.0,
    mid: -0.5,
    presence: 1.0,
    treble: 1.5,
    gain: 1.0,
    compressor: true,
  },
  vocal: {
    id: 'vocal',
    name: 'Giọng Hát Rõ Lời (Vocal Clarity)',
    icon: '🎙️',
    desc: 'Tối ưu dải ngữ âm 3.2kHz, giúp lời hát tròn vành rõ chữ, tách bạch khỏi beat',
    bass: 0.5,
    mid: 1.5,
    presence: 5.0,
    treble: 3.5,
    gain: 1.0,
    compressor: true,
  },
  spatial: {
    id: 'spatial',
    name: 'Không Gian 3D (Spatial Audio)',
    icon: '🌌',
    desc: 'Mở rộng trường âm thanh nổi, tạo cảm giác âm thanh bao quanh như khán phòng',
    bass: 2.5,
    mid: 0.5,
    presence: 3.0,
    treble: 4.5,
    gain: 1.08,
    compressor: true,
  },
  flat: {
    id: 'flat',
    name: 'Tự Nhiên (Flat / Bypass)',
    icon: '🍃',
    desc: 'Giữ nguyên 100% âm sắc gốc của bản thu không qua bộ lọc',
    bass: 0.0,
    mid: 0.0,
    presence: 0.0,
    treble: 0.0,
    gain: 1.0,
    compressor: false,
  },
}

export default function EqualizerPanel({
  onClose,
  currentPreset,
  onSelectPreset,
  customSettings,
  onChangeCustom,
}) {
  const [activeTab, setActiveTab] = useState('presets') // 'presets' | 'sliders'

  return (
    <div
      className="fixed bottom-20 right-4 sm:right-8 z-50 w-80 sm:w-96 animate-slide-up select-none shadow-[0_12px_40px_rgba(0,0,0,0.8)] border border-cyan-500/20"
      style={{
        background: 'rgba(10, 12, 26, 0.96)',
        borderRadius: '22px',
        backdropFilter: 'blur(24px)',
      }}>
      
      {/* ── Header ── */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08]">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md">
            <MdGraphicEq size={16} />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white tracking-wide">Bộ Tối Ưu Âm Thanh HD</h3>
            <p className="text-[10px] text-cyan-400 font-medium">Audiophile DSP Engine</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white/40 hover:text-white p-1 rounded-lg hover:bg-white/[0.06] transition-colors"
          title="Đóng bảng">
          <FiX size={16} />
        </button>
      </div>

      {/* ── Mode Tabs ── */}
      <div className="flex px-4 pt-3 gap-2">
        <button
          onClick={() => setActiveTab('presets')}
          className={clsx(
            'flex-1 py-1.5 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-1.5',
            activeTab === 'presets'
              ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 border border-cyan-500/40 text-cyan-300 shadow-sm'
              : 'text-white/40 hover:text-white/80 hover:bg-white/[0.04]'
          )}>
          <span>Chế độ mẫu</span>
        </button>
        <button
          onClick={() => setActiveTab('sliders')}
          className={clsx(
            'flex-1 py-1.5 text-xs font-semibold rounded-xl transition-all flex items-center justify-center gap-1.5',
            activeTab === 'sliders'
              ? 'bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 border border-cyan-500/40 text-cyan-300 shadow-sm'
              : 'text-white/40 hover:text-white/80 hover:bg-white/[0.04]'
          )}>
          <FiSliders size={12} />
          <span>Tinh chỉnh EQ</span>
        </button>
      </div>

      {/* ── Tab Content ── */}
      <div className="p-3.5 max-h-80 overflow-y-auto space-y-2">
        {activeTab === 'presets' ? (
          <div className="space-y-2">
            {Object.values(EQ_PRESETS).map((p) => {
              const isSelected = currentPreset === p.id
              return (
                <button
                  key={p.id}
                  onClick={() => onSelectPreset(p.id)}
                  className={clsx(
                    'w-full flex items-start gap-3 p-2.5 rounded-xl text-left transition-all border group',
                    isSelected
                      ? 'bg-gradient-to-r from-cyan-500/15 to-indigo-500/15 border-cyan-400/40 text-white shadow-[0_0_15px_rgba(34,211,238,0.15)]'
                      : 'border-white/[0.05] hover:border-white/[0.12] hover:bg-white/[0.03] text-white/70'
                  )}>
                  <span className="text-xl shrink-0 mt-0.5">{p.icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className={clsx('text-xs font-bold', isSelected ? 'text-cyan-300' : 'text-white')}>
                        {p.name}
                      </span>
                      {isSelected && (
                        <span className="w-4 h-4 rounded-full bg-cyan-400 text-black flex items-center justify-center">
                          <FiCheck size={11} className="stroke-[3]" />
                        </span>
                      )}
                    </div>
                    <p className="text-[10px] text-white/45 mt-0.5 line-clamp-2 leading-relaxed">
                      {p.desc}
                    </p>
                  </div>
                </button>
              )
            })}
          </div>
        ) : (
          <div className="space-y-4 px-1 py-2">
            {/* Bass Slider */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-white/70 flex items-center gap-1.5">
                  <span className="text-cyan-400 font-bold">🔊</span> Âm Trầm (Bass 80Hz)
                </span>
                <span className="text-cyan-300 font-mono text-[11px] font-bold">
                  {customSettings.bass > 0 ? `+${customSettings.bass.toFixed(1)}` : customSettings.bass.toFixed(1)} dB
                </span>
              </div>
              <input
                type="range"
                min="-6"
                max="10"
                step="0.5"
                value={customSettings.bass}
                onChange={(e) => onChangeCustom('bass', parseFloat(e.target.value))}
                className="w-full accent-cyan-400 h-1.5 bg-white/10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Mid Slider */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-white/70 flex items-center gap-1.5">
                  <span className="text-indigo-400 font-bold">🎹</span> Âm Trung & Lời (Mid 1.2kHz)
                </span>
                <span className="text-indigo-300 font-mono text-[11px] font-bold">
                  {customSettings.mid > 0 ? `+${customSettings.mid.toFixed(1)}` : customSettings.mid.toFixed(1)} dB
                </span>
              </div>
              <input
                type="range"
                min="-6"
                max="8"
                step="0.5"
                value={customSettings.mid}
                onChange={(e) => onChangeCustom('mid', parseFloat(e.target.value))}
                className="w-full accent-indigo-400 h-1.5 bg-white/10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Treble Slider */}
            <div>
              <div className="flex justify-between text-xs mb-1.5 font-medium">
                <span className="text-white/70 flex items-center gap-1.5">
                  <span className="text-purple-400 font-bold">✨</span> Âm Cao & Không Khí (Treble 12kHz)
                </span>
                <span className="text-purple-300 font-mono text-[11px] font-bold">
                  {customSettings.treble > 0 ? `+${customSettings.treble.toFixed(1)}` : customSettings.treble.toFixed(1)} dB
                </span>
              </div>
              <input
                type="range"
                min="-6"
                max="10"
                step="0.5"
                value={customSettings.treble}
                onChange={(e) => onChangeCustom('treble', parseFloat(e.target.value))}
                className="w-full accent-purple-400 h-1.5 bg-white/10 rounded-lg cursor-pointer"
              />
            </div>

            {/* Quick Reset Button */}
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => onSelectPreset('studio')}
                className="text-[11px] text-cyan-400/80 hover:text-cyan-300 underline underline-offset-2">
                Đặt lại về chuẩn Studio HD
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── Footer Info ── */}
      <div className="px-4 py-2.5 bg-white/[0.02] border-t border-white/[0.05] rounded-b-[22px] flex items-center justify-between text-[10px] text-white/40">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          DSP Realtime Web Audio 24-bit
        </span>
        <span className="font-mono text-cyan-400">Zero Latency</span>
      </div>
    </div>
  )
}
