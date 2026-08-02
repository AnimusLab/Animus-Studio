import { Target, Bot, BarChart3, Zap, TrendingUp, Play, Clock, CheckCircle2 } from 'lucide-react'

const STATS = [
  { label: 'Active Missions',  value: '2',    delta: '+1 this week',   icon: Target,     color: '#3b6bff' },
  { label: 'Videos Published', value: '14',   delta: '+3 this week',   icon: Play,       color: '#00e5a0' },
  { label: 'Agent Runs',       value: '47',   delta: 'last 30 days',   icon: Bot,        color: '#9b59ff' },
  { label: 'Avg CTR',          value: '4.2%', delta: '↑ 0.8% vs last', icon: TrendingUp, color: '#ffb347' },
]

const RECENT_JOBS = [
  { id: '1', title: 'AI Coding Tools Roundup', status: 'completed', agent: 'daily_content', time: '2h ago' },
  { id: '2', title: 'LLM Context Windows Explained', status: 'running',   agent: 'daily_content', time: '10m ago' },
  { id: '3', title: 'Weekly Analytics Review',       status: 'pending',   agent: 'weekly_review', time: 'Scheduled' },
]

const PIPELINE_STEPS = [
  'Research', 'Script', 'Review', 'Voice', 'Video', 'Thumbnail', 'Publish', 'Analytics'
]

const STATUS_COLOR: Record<string, string> = {
  completed: 'badge-active',
  running:   'badge-running',
  pending:   'badge-pending',
  failed:    'badge-failed',
}

export default function Dashboard() {
  return (
    <div className="page-enter p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Command Center</h1>
        <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Your autonomous media OS — Project Hermes
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        {STATS.map(({ label, value, delta, icon: Icon, color }) => (
          <div key={label} className="glass rounded-xl p-5 agent-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium mb-2" style={{ color: 'rgba(255,255,255,0.4)' }}>
                  {label}
                </p>
                <p className="text-3xl font-bold text-white">{value}</p>
                <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.3)' }}>{delta}</p>
              </div>
              <div
                className="w-10 h-10 rounded-lg flex items-center justify-center"
                style={{ background: `${color}18`, border: `1px solid ${color}30` }}
              >
                <Icon size={18} style={{ color }} />
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Active Pipeline */}
        <div className="col-span-2 glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-semibold text-white">Active Pipeline</h2>
            <span className="badge badge-running">
              <span className="pulse-dot" style={{ background: '#6090ff' }} />
              Running
            </span>
          </div>

          {/* Current job info */}
          <p className="text-xs mb-4" style={{ color: 'rgba(255,255,255,0.4)' }}>
            LLM Context Windows Explained — daily_content workflow
          </p>

          {/* Pipeline steps */}
          <div className="flex items-center gap-2 flex-wrap">
            {PIPELINE_STEPS.map((step, i) => {
              const done = i < 2
              const active = i === 2
              return (
                <div
                  key={step}
                  className={`pipeline-step flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                    done
                      ? 'border-emerald-500/30 text-emerald-400'
                      : active
                      ? 'border-brand-500/50 text-brand-400 glow-brand'
                      : 'border-white/5 text-white/20'
                  }`}
                  style={
                    done
                      ? { background: 'rgba(0,229,160,0.08)' }
                      : active
                      ? { background: 'rgba(59,107,255,0.12)' }
                      : { background: 'rgba(255,255,255,0.02)' }
                  }
                >
                  {done && <CheckCircle2 size={10} />}
                  {active && <span className="pulse-dot" style={{ background: '#6090ff' }} />}
                  {step}
                </div>
              )
            })}
          </div>

          {/* Progress bar */}
          <div className="mt-5">
            <div className="flex justify-between text-xs mb-2" style={{ color: 'rgba(255,255,255,0.3)' }}>
              <span>Progress</span>
              <span>25%</span>
            </div>
            <div className="h-1.5 rounded-full" style={{ background: 'rgba(255,255,255,0.06)' }}>
              <div
                className="h-full rounded-full glow-brand transition-all duration-500"
                style={{ width: '25%', background: 'linear-gradient(90deg, #3b6bff, #9b59ff)' }}
              />
            </div>
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="glass rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-white">Recent Jobs</h2>
            <Clock size={14} style={{ color: 'rgba(255,255,255,0.3)' }} />
          </div>
          <div className="space-y-3">
            {RECENT_JOBS.map(job => (
              <div
                key={job.id}
                className="flex flex-col gap-1 p-3 rounded-lg cursor-pointer hover:bg-white/5 transition-colors"
                style={{ border: '1px solid rgba(255,255,255,0.04)' }}
              >
                <p className="text-xs font-medium text-white truncate">{job.title}</p>
                <div className="flex items-center justify-between">
                  <span className={`badge ${STATUS_COLOR[job.status]}`}>{job.status}</span>
                  <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.25)' }}>{job.time}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Launch */}
      <div className="glass rounded-xl p-6">
        <h2 className="text-sm font-semibold text-white mb-4">Quick Launch</h2>
        <div className="flex gap-3">
          {['Daily Content', 'Breaking News', 'Weekly Review'].map(w => (
            <button
              key={w}
              className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium text-white transition-all hover:scale-105 active:scale-95"
              style={{
                background: 'linear-gradient(135deg, rgba(59,107,255,0.2), rgba(155,89,255,0.2))',
                border: '1px solid rgba(59,107,255,0.3)',
              }}
            >
              <Zap size={14} style={{ color: '#6090ff' }} />
              {w}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
