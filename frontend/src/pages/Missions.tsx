import { Plus, Target, Play, Pause, MoreVertical } from 'lucide-react'

const MISSIONS = [
  {
    id: '1',
    title: 'Grow AnimusLab YouTube',
    goal: 'Grow AnimusLab YouTube to 5,000 subscribers',
    brand: 'AnimusLab',
    status: 'active',
    frequency: '3 Shorts/week',
    style: 'Professional',
    requires_approval: true,
    runs: 14,
    success_rate: 92,
  },
  {
    id: '2',
    title: 'LinkedIn Thought Leadership',
    goal: 'Post daily insights on AI engineering',
    brand: 'AnimusLab',
    status: 'paused',
    frequency: 'Daily',
    style: 'Conversational',
    requires_approval: false,
    runs: 7,
    success_rate: 85,
  },
]

export default function Missions() {
  return (
    <div className="page-enter p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Missions</h1>
          <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
            Define goals. Let the agents execute.
          </p>
        </div>
        <button
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 glow-brand"
          style={{ background: 'linear-gradient(135deg, #3b6bff, #9b59ff)' }}
        >
          <Plus size={16} />
          New Mission
        </button>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {MISSIONS.map(m => (
          <div key={m.id} className="glass rounded-xl p-6 agent-card">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ background: 'rgba(59,107,255,0.15)', border: '1px solid rgba(59,107,255,0.2)' }}
                >
                  <Target size={18} style={{ color: '#6090ff' }} />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">{m.title}</h3>
                  <p className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>{m.brand}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`badge badge-${m.status}`}>{m.status}</span>
                <button className="p-1 rounded hover:bg-white/10 transition-colors">
                  <MoreVertical size={14} style={{ color: 'rgba(255,255,255,0.4)' }} />
                </button>
              </div>
            </div>

            <p className="text-xs mb-4 leading-relaxed" style={{ color: 'rgba(255,255,255,0.5)' }}>
              {m.goal}
            </p>

            <div className="grid grid-cols-3 gap-3 mb-4">
              {[
                { label: 'Frequency', value: m.frequency },
                { label: 'Style', value: m.style },
                { label: 'Approval', value: m.requires_approval ? 'Required' : 'Auto' },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-lg p-2.5 text-center" style={{ background: 'rgba(255,255,255,0.04)' }}>
                  <p className="text-[10px] mb-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{label}</p>
                  <p className="text-xs font-medium text-white">{value}</p>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4 text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>
                <span>{m.runs} runs</span>
                <span className="text-emerald-400">{m.success_rate}% success</span>
              </div>
              <div className="flex gap-2">
                <button
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:scale-105"
                  style={{ background: 'rgba(0,229,160,0.12)', color: '#00e5a0', border: '1px solid rgba(0,229,160,0.2)' }}
                >
                  <Play size={11} /> Run
                </button>
                <button
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all hover:bg-white/5"
                  style={{ color: 'rgba(255,255,255,0.4)', border: '1px solid rgba(255,255,255,0.08)' }}
                >
                  <Pause size={11} /> Pause
                </button>
              </div>
            </div>
          </div>
        ))}

        {/* New Mission CTA */}
        <div
          className="rounded-xl p-6 flex flex-col items-center justify-center gap-3 cursor-pointer hover:bg-white/5 transition-all"
          style={{ border: '2px dashed rgba(255,255,255,0.08)', minHeight: 200 }}
        >
          <div
            className="w-12 h-12 rounded-full flex items-center justify-center"
            style={{ background: 'rgba(59,107,255,0.1)', border: '1px solid rgba(59,107,255,0.2)' }}
          >
            <Plus size={20} style={{ color: '#3b6bff' }} />
          </div>
          <p className="text-sm text-white font-medium">Create New Mission</p>
          <p className="text-xs text-center" style={{ color: 'rgba(255,255,255,0.3)', maxWidth: 200 }}>
            Define a goal and let the Executive Agent plan the workflow
          </p>
        </div>
      </div>
    </div>
  )
}
