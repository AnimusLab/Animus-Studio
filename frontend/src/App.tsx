import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import Dashboard from '@/pages/Dashboard'
import Missions from '@/pages/Missions'
import Agents from '@/pages/Agents'
import Brands from '@/pages/Brands'
import Analytics from '@/pages/Analytics'
import Knowledge from '@/pages/Knowledge'
import Settings from '@/pages/Settings'
import Calendar from '@/pages/Calendar'
import Doctor from '@/pages/Doctor'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 15_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="missions" element={<Missions />} />
            <Route path="agents" element={<Agents />} />
            <Route path="brands" element={<Brands />} />
            <Route path="calendar" element={<Calendar />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="knowledge" element={<Knowledge />} />
            <Route path="doctor" element={<Doctor />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
