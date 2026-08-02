import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from 'recharts'
import { TrendingUp, Eye, ThumbsUp, MousePointer } from 'lucide-react'

const WEEKLY_VIEWS = [
  { day: 'Mon', views: 1200 }, { day: 'Tue', views: 2100 }, { day: 'Wed', views: 800 },
  { day: 'Thu', views: 3400 }, { day: 'Fri', views: 2700 }, { day: 'Sat', views: 1900 },
  { day: 'Sun', views: 2200 },
]

const CTR_TREND = [
  { week: 'W1', ctr: 3.1 }, { week: 'W2', ctr: 3.4 }, { week: 'W3', ctr: 3.9 },
  { week: 'W4', ctr: 4.2 },
]

const METRICS = [
  { label: 'Total Views',    value: '14.3K', icon: Eye,          color: '#3b6bff' },
  { label: 'Avg CTR',        value: '4.2%',  icon: MousePointer, color: '#00d4ff' },
  { label: 'Total Likes',    value: '892',   icon: ThumbsUp,     color: '#00e5a0' },
  { label: 'Sub Growth',     value: '+127',  icon: TrendingUp,   color: '#9b59ff' },
]

export default function Analytics() {
  return (
    <div className="page-enter p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Analytics</h1>
        <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Performance metrics across all platforms and videos.
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {METRICS.map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="glass rounded-xl p-5 agent-card">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
                <Icon size={15} style={{ color }} />
              </div>
              <p className="text-xs" style={{ color: 'rgba(255,255,255,0.4)' }}>{label}</p>
            </div>
            <p className="text-2xl font-bold text-white">{value}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="glass rounded-xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">Weekly Views</h2>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={WEEKLY_VIEWS} barSize={24}>
              <XAxis dataKey="day" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#18181f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8 }}
                labelStyle={{ color: 'white', fontSize: 12 }}
                itemStyle={{ color: '#6090ff', fontSize: 12 }}
              />
              <Bar dataKey="views" fill="url(#barGrad)" radius={[4, 4, 0, 0]} />
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b6bff" />
                  <stop offset="100%" stopColor="#9b59ff" />
                </linearGradient>
              </defs>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass rounded-xl p-6">
          <h2 className="text-sm font-semibold text-white mb-4">CTR Trend</h2>
          <ResponsiveContainer width="100%" height={180}>
            <LineChart data={CTR_TREND}>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="week" tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: 'rgba(255,255,255,0.3)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip
                contentStyle={{ background: '#18181f', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8 }}
                labelStyle={{ color: 'white', fontSize: 12 }}
                itemStyle={{ color: '#00e5a0', fontSize: 12 }}
              />
              <Line type="monotone" dataKey="ctr" stroke="#00e5a0" strokeWidth={2} dot={{ fill: '#00e5a0', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
