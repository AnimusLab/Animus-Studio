export default function Calendar() {
  return (
    <div className="page-enter p-8">
      <h1 className="text-2xl font-bold text-white">Content Calendar</h1>
      <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
        Scheduled videos, publishing queue, and content planning.
      </p>
      <div className="glass rounded-xl p-8 mt-6 flex flex-col items-center justify-center gap-3" style={{ minHeight: 300 }}>
        <p className="text-sm text-white font-medium">Calendar — Coming in Phase 3</p>
        <p className="text-xs text-center" style={{ color: 'rgba(255,255,255,0.3)', maxWidth: 300 }}>
          Visual calendar showing scheduled uploads, publishing windows, and content pipeline status.
        </p>
      </div>
    </div>
  )
}
