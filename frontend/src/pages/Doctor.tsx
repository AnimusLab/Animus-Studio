import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Stethoscope, CheckCircle2, AlertTriangle, XCircle, RefreshCw,
  Cpu, Mic, Search, Share2, Server, Terminal, Copy, Check
} from 'lucide-react'

interface DoctorItem {
  name: string
  status: 'ok' | 'warning' | 'error' | 'downloading'
  detail: string
  suggestion: string
}

interface DoctorSection {
  name: string
  items: DoctorItem[]
}

interface DoctorReport {
  status: 'ok' | 'warning' | 'error'
  summary: {
    passed: number
    warnings: number
    errors: number
  }
  sections: DoctorSection[]
}

const SECTION_ICONS: Record<string, any> = {
  Models: Cpu,
  Voice: Mic,
  Search: Search,
  Publishing: Share2,
  Infrastructure: Server,
}

export default function Doctor() {
  const [copiedCmd, setCopiedCmd] = useState<string | null>(null)

  const { data: report, isLoading, isFetching, refetch } = useQuery<DoctorReport>({
    queryKey: ['doctor-report'],
    queryFn: async () => {
      const res = await fetch('/api/v1/doctor')
      if (!res.ok) {
        throw new Error('Failed to fetch doctor report')
      }
      return res.json()
    },
    refetchInterval: 15_000,
  })

  const copyToClipboard = (cmd: string) => {
    navigator.clipboard.writeText(cmd)
    setCopiedCmd(cmd)
    setTimeout(() => setCopiedCmd(null), 2000)
  }

  const getStatusIcon = (status: DoctorItem['status']) => {
    switch (status) {
      case 'ok':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />
      case 'downloading':
        return <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />
      case 'error':
        return <XCircle className="w-5 h-5 text-rose-500" />
    }
  }

  const getStatusBadge = (status: DoctorItem['status']) => {
    switch (status) {
      case 'ok':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            Active
          </span>
        )
      case 'downloading':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
            Downloading
          </span>
        )
      case 'warning':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            Missing / Unconfigured
          </span>
        )
      case 'error':
        return (
          <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            Offline / Error
          </span>
        )
    }
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <div
              className="p-2.5 rounded-xl glow-brand"
              style={{ background: 'linear-gradient(135deg, #3b6bff, #9b59ff)' }}
            >
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Runtime Doctor</h1>
              <p className="text-sm text-gray-400 mt-0.5">
                Real-time capability matrix, model availability, and infrastructure health
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 text-white disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
            <span>Re-run Diagnostics</span>
          </button>
        </div>
      </div>

      {/* ── Overview Summary Cards ────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl border border-white/5 bg-surface-800/80 backdrop-blur-md flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-gray-400 font-semibold">Overall System Status</p>
            <p className="text-xl font-bold mt-1 text-white flex items-center gap-2">
              {report?.status === 'ok' ? (
                <span className="text-emerald-400">All Systems Operational</span>
              ) : report?.status === 'warning' ? (
                <span className="text-amber-400">Degraded / Missing Options</span>
              ) : (
                <span className="text-rose-400">Critical Error</span>
              )}
            </p>
          </div>
          <span className={`w-3 h-3 rounded-full ${
            report?.status === 'ok' ? 'bg-emerald-400 shadow-[0_0_12px_#10b981]' :
            report?.status === 'warning' ? 'bg-amber-400 shadow-[0_0_12px_#f59e0b]' :
            'bg-rose-500 shadow-[0_0_12px_#ef4444]'
          }`} />
        </div>

        <div className="p-5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-emerald-400/80 font-semibold">Active Capabilities</p>
            <p className="text-2xl font-bold mt-1 text-emerald-400">
              {isLoading ? '...' : report?.summary.passed ?? 0}
            </p>
          </div>
          <CheckCircle2 className="w-8 h-8 text-emerald-400/40" />
        </div>

        <div className="p-5 rounded-2xl border border-amber-500/20 bg-amber-500/5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-amber-400/80 font-semibold">Warnings / Optional</p>
            <p className="text-2xl font-bold mt-1 text-amber-400">
              {isLoading ? '...' : report?.summary.warnings ?? 0}
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-amber-400/40" />
        </div>

        <div className="p-5 rounded-2xl border border-rose-500/20 bg-rose-500/5 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-rose-400/80 font-semibold">Errors / Required</p>
            <p className="text-2xl font-bold mt-1 text-rose-400">
              {isLoading ? '...' : report?.summary.errors ?? 0}
            </p>
          </div>
          <XCircle className="w-8 h-8 text-rose-400/40" />
        </div>
      </div>

      {/* ── Terminal Banner Box ──────────────────────────────────── */}
      <div className="rounded-2xl border border-white/10 bg-black/70 overflow-hidden font-mono text-xs shadow-2xl">
        <div className="px-4 py-2.5 bg-white/5 border-b border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-purple-400" />
            <span className="text-gray-300 font-semibold">CLI Output — python -m runtime.doctor</span>
          </div>
          <span className="text-[10px] text-gray-500">Auto-refreshes every 15s</span>
        </div>
        <div className="p-6 text-gray-300 space-y-1 select-all overflow-x-auto">
          <p className="text-purple-400 font-bold">════════════ Runtime Doctor ════════════</p>
          {report?.sections.map((sec) => (
            <div key={sec.name} className="py-2">
              <p className="text-gray-400 font-semibold tracking-wide border-b border-white/10 pb-1 mb-2">
                {sec.name}
              </p>
              {sec.items.map((item) => (
                <div key={item.name} className="flex items-center gap-3 py-0.5">
                  <span className="w-4 text-center">
                    {item.status === 'ok' ? (
                      <span className="text-emerald-400">✓</span>
                    ) : item.status === 'downloading' ? (
                      <span className="text-amber-400 font-bold">⏳</span>
                    ) : item.status === 'warning' ? (
                      <span className="text-amber-400">⚠️</span>
                    ) : (
                      <span className="text-rose-500">✕</span>
                    )}
                  </span>
                  <span className="w-44 text-white font-medium">{item.name}</span>
                  <span className="text-gray-400 flex-1">{item.detail}</span>
                  {item.suggestion && (
                    <span className="text-purple-300/80 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-800/30">
                      {item.suggestion}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ── Category Cards Grid ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {report?.sections.map((section) => {
          const Icon = SECTION_ICONS[section.name] || Server
          return (
            <div
              key={section.name}
              className="rounded-2xl border border-white/5 bg-surface-800/60 backdrop-blur-md p-6 space-y-4 shadow-xl"
            >
              <div className="flex items-center justify-between border-b border-white/5 pb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-white/5 text-purple-400 border border-white/10">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h2 className="text-lg font-bold text-white tracking-tight">{section.name}</h2>
                </div>
                <span className="text-xs text-gray-400 font-medium">
                  {section.items.filter((i) => i.status === 'ok').length} / {section.items.length} Ready
                </span>
              </div>

              <div className="space-y-3">
                {section.items.map((item) => (
                  <div
                    key={item.name}
                    className="p-3.5 rounded-xl border border-white/5 bg-black/20 hover:bg-black/40 transition-colors space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(item.status)}
                        <span className="font-semibold text-white text-sm">{item.name}</span>
                      </div>
                      {getStatusBadge(item.status)}
                    </div>

                    <div className="flex items-center justify-between text-xs text-gray-400 pl-8">
                      <span>{item.detail}</span>
                    </div>

                    {item.suggestion && (
                      <div className="mt-2 pt-2 border-t border-white/5 flex items-center justify-between bg-black/40 px-3 py-2 rounded-lg text-xs">
                        <span className="font-mono text-purple-300 font-medium truncate">{item.suggestion}</span>
                        <button
                          onClick={() => copyToClipboard(item.suggestion)}
                          className="flex items-center gap-1 px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-colors cursor-pointer"
                          title="Copy command"
                        >
                          {copiedCmd === item.suggestion ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-emerald-400" />
                              <span className="text-emerald-400 text-[10px]">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span className="text-[10px]">Copy</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
