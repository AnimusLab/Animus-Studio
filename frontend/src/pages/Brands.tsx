export default function Brands() {
  return (
    <div className="page-enter p-8">
      <h1 className="text-2xl font-bold text-white">Brands</h1>
      <p className="text-sm mt-1" style={{ color: 'rgba(255,255,255,0.4)' }}>
        Manage brand identities, tone, and voice profiles.
      </p>
      <div className="glass rounded-xl p-8 mt-6 flex flex-col items-center justify-center gap-3" style={{ minHeight: 200 }}>
        <p className="text-sm text-white font-medium">Brand management — Coming in Phase 2</p>
        <p className="text-xs text-center" style={{ color: 'rgba(255,255,255,0.3)', maxWidth: 300 }}>
          Each brand stores tone, vocabulary, target audience, voice profiles, and knowledge memories.
        </p>
      </div>
    </div>
  )
}
