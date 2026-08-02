import { Key, Bot, Mic, Globe } from 'lucide-react'

const SECTIONS = [
  {
    icon: Bot,
    title: 'LLM Configuration',
    color: '#3b6bff',
    fields: [
      { label: 'Default Model', type: 'select', value: 'openai/gpt-4o', options: ['openai/gpt-4o', 'anthropic/claude-3-5-sonnet', 'openai/gpt-4o-mini'] },
      { label: 'Temperature', type: 'range', value: '0.7' },
    ],
  },
  {
    icon: Mic,
    title: 'Voice Settings',
    color: '#9b59ff',
    fields: [
      { label: 'TTS Provider', type: 'select', value: 'elevenlabs', options: ['elevenlabs', 'cartesia'] },
      { label: 'Default Voice ID', type: 'text', value: '' },
    ],
  },
  {
    icon: Key,
    title: 'API Keys',
    color: '#00d4ff',
    fields: [
      { label: 'OpenAI', type: 'password', value: '' },
      { label: 'Anthropic', type: 'password', value: '' },
      { label: 'ElevenLabs', type: 'password', value: '' },
    ],
  },
  {
    icon: Globe,
    title: 'Platform Connections',
    color: '#00e5a0',
    fields: [
      { label: 'YouTube', type: 'status', value: 'Not connected' },
      { label: 'Instagram', type: 'status', value: 'Not connected' },
      { label: 'LinkedIn', type: 'status', value: 'Not connected' },
    ],
  },
]

export default function Settings() {
  return (
    <div className="page-enter p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
          Configure LLMs, voice providers, API keys, and platform integrations.
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        {SECTIONS.map(({ icon: Icon, title, color, fields }) => (
          <div key={title} className="glass rounded-xl p-6">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${color}15` }}>
                <Icon size={16} style={{ color }} />
              </div>
              <h2 className="text-sm font-semibold text-white">{title}</h2>
            </div>

            <div className="space-y-4">
              {fields.map(f => (
                <div key={f.label}>
                  <label className="block text-xs mb-1.5" style={{ color: 'rgba(255,255,255,0.4)' }}>
                    {f.label}
                  </label>
                  {f.type === 'status' ? (
                    <div className="flex items-center justify-between">
                      <span className="text-xs" style={{ color: 'rgba(255,255,255,0.3)' }}>{f.value}</span>
                      <button
                        className="text-xs px-3 py-1.5 rounded-lg font-medium"
                        style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
                      >
                        Connect
                      </button>
                    </div>
                  ) : f.type === 'select' ? (
                    <select
                      className="w-full px-3 py-2 rounded-lg text-sm text-white outline-none"
                      style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                      defaultValue={f.value}
                    >
                      {f.options?.map(o => <option key={o} value={o} style={{ background: '#18181f' }}>{o}</option>)}
                    </select>
                  ) : (
                    <input
                      type={f.type}
                      placeholder={f.type === 'password' ? '••••••••' : f.label}
                      defaultValue={f.value}
                      className="w-full px-3 py-2 rounded-lg text-sm text-white placeholder:text-white/20 outline-none focus:ring-1 focus:ring-brand-500"
                      style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    />
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end">
        <button
          className="px-6 py-2.5 rounded-lg text-sm font-semibold text-white transition-all hover:scale-105 glow-brand"
          style={{ background: 'linear-gradient(135deg, #3b6bff, #9b59ff)' }}
        >
          Save Settings
        </button>
      </div>
    </div>
  )
}
