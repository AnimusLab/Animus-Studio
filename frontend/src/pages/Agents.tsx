import { Bot, Activity, CheckCircle2, Clock } from 'lucide-react'

const DEPARTMENTS = [
  {
    dept: 'Executive',
    agents: [
      { name: 'Executive Agent', status: 'idle', role: 'CEO — coordinates all departments', runs: 14, color: '#9b59ff' },
    ],
  },
  {
    dept: 'Research',
    agents: [
      { name: 'Research Agent', status: 'idle', role: 'Trends, news, competitor analysis', runs: 14, color: '#00d4ff' },
    ],
  },
  {
    dept: 'Creative',
    agents: [
      { name: 'Script Agent',  status: 'idle',    role: 'Title, hook, script, CTA',        runs: 14, color: '#3b6bff' },
      { name: 'Review Agent',  status: 'running', role: 'Grammar, facts, tone, copyright',  runs: 14, color: '#ffb347' },
    ],
  },
  {
    dept: 'Media',
    agents: [
      { name: 'Voice Agent',     status: 'idle', role: 'ElevenLabs TTS voiceover',   runs: 14, color: '#00e5a0' },
      { name: 'Editor Agent',    status: 'idle', role: 'FFmpeg video assembly',       runs: 12, color: '#00e5a0' },
      { name: 'Thumbnail Agent', status: 'idle', role: 'CTR-optimized thumbnails',   runs: 12, color: '#00e5a0' },
    ],
  },
  {
    dept: 'Publishing',
    agents: [
      { name: 'Publisher Agent', status: 'idle', role: 'YouTube, Instagram, LinkedIn, X', runs: 14, color: '#ff6b9d' },
    ],
  },
  {
    dept: 'Analytics',
    agents: [
      { name: 'Analytics Agent', status: 'idle', role: 'CTR, retention, revenue, RPM', runs: 7, color: '#ffb347' },
    ],
  },
]

const STATUS_ICON = {
  idle:    <Clock size={12} style={{ color: 'rgba(255,255,255,0.3)' }} />,
  running: <Activity size={12} style={{ color: '#6090ff' }} />,
  done:    <CheckCircle2 size={12} style={{ color: '#00e5a0' }} />,
}

export default function Agents() {
  return (
    <div className="page-enter p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Agent Departments</h1>
        <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Specialists organized into departments — each with a single clear responsibility.
        </p>
      </div>

      <div className="space-y-6">
        {DEPARTMENTS.map(({ dept, agents }) => (
          <div key={dept}>
            <p className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'rgba(255,255,255,0.3)' }}>
              {dept} Department
            </p>
            <div className="grid grid-cols-3 gap-4">
              {agents.map(agent => (
                <div key={agent.name} className="glass rounded-xl p-5 agent-card">
                  <div className="flex items-start gap-3 mb-3">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
                      style={{ background: `${agent.color}18`, border: `1px solid ${agent.color}30` }}
                    >
                      <Bot size={16} style={{ color: agent.color }} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate">{agent.name}</p>
                      <p className="text-[11px] leading-relaxed mt-0.5" style={{ color: 'rgba(255,255,255,0.4)' }}>
                        {agent.role}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5 text-xs" style={{ color: 'rgba(255,255,255,0.3)' }}>
                      {STATUS_ICON[agent.status as keyof typeof STATUS_ICON]}
                      <span className="capitalize">{agent.status}</span>
                    </div>
                    <span className="text-xs" style={{ color: 'rgba(255,255,255,0.3)' }}>
                      {agent.runs} runs
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
