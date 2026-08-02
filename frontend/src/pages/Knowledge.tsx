import { Brain, FileText, Users, Play, Layers } from 'lucide-react'

const MEMORIES = [
  { type: 'Brand',    icon: Layers,   label: 'AnimusLab Brand Memory',     desc: 'Tone: professional. Avoid: clickbait. Target: software engineers.',  color: '#9b59ff' },
  { type: 'Creator',  icon: Users,    label: 'Creator Voice Memory',        desc: 'Vocabulary, sentence patterns, fill words, and speech cadence.',    color: '#3b6bff' },
  { type: 'Video',    icon: Play,     label: '14 Video Memories',           desc: 'Successful formats, failed angles, top hooks, and CTA performance.', color: '#00e5a0' },
  { type: 'Research', icon: FileText, label: '47 Research Entries',         desc: 'Indexed topics, sources, angles, and competitive analysis.',         color: '#00d4ff' },
]

export default function Knowledge() {
  return (
    <div className="page-enter p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Knowledge Engine</h1>
        <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
          PostgreSQL + pgvector memory for all agents. Semantic search enabled.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-5">
        {MEMORIES.map(({ type, icon: Icon, label, desc, color }) => (
          <div key={type} className="glass rounded-xl p-6 agent-card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-lg flex items-center justify-center" style={{ background: `${color}15`, border: `1px solid ${color}25` }}>
                <Icon size={18} style={{ color }} />
              </div>
              <div>
                <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: color }}>{type}</p>
                <p className="text-sm font-semibold text-white">{label}</p>
              </div>
            </div>
            <p className="text-xs leading-relaxed" style={{ color: 'rgba(255,255,255,0.45)' }}>{desc}</p>
          </div>
        ))}
      </div>

      <div className="glass rounded-xl p-6">
        <div className="flex items-center gap-3 mb-4">
          <Brain size={18} style={{ color: '#9b59ff' }} />
          <h2 className="text-sm font-semibold text-white">Semantic Search</h2>
        </div>
        <div className="flex gap-3">
          <input
            type="text"
            placeholder="Search across all memories..."
            className="flex-1 px-4 py-2.5 rounded-lg text-sm text-white placeholder:text-white/25 outline-none focus:ring-1 focus:ring-brand-500"
            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
          />
          <button
            className="px-4 py-2.5 rounded-lg text-sm font-medium text-white"
            style={{ background: 'rgba(59,107,255,0.2)', border: '1px solid rgba(59,107,255,0.3)' }}
          >
            Search
          </button>
        </div>
      </div>
    </div>
  )
}
