import { useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import {
  Activity,
  BedDouble,
  CalendarDays,
  CheckCircle2,
  ClipboardList,
  Clock3,
  Hospital,
  LayoutDashboard,
  RefreshCw,
  Search,
  Stethoscope,
  UserRound,
  XCircle,
} from 'lucide-react'
import './styles.css'

type Doctor = {
  doctor_id: string
  name?: string
  department?: string
  specialization?: string
  is_available?: boolean
}

type Appointment = {
  id: string
  patient_id?: string
  doctor_id?: string
  appointment_date?: string
  appointment_time?: string
  status?: string
  reason?: string | null
}

type Token = {
  token_id: string
  token_number: number
  patient_id?: string
  appointment_id?: string
  doctor_id?: string
  token_date?: string
  status: string
  people_ahead?: number
  estimated_wait_minutes?: number
  created_at?: string
}

type Bed = {
  id?: string
  bed_number?: string | number
  bed_type?: string
  status?: string
  ward_name?: string
  ward_type?: string
}

type ApiResponse<T> = {
  success: boolean
  data: T
  message?: string
  error_code?: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

async function api<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok || body.success === false) {
    throw new Error(body.message || body.error_code || 'Request failed')
  }
  return body
}

function App() {
  const [view, setView] = useState<'dashboard' | 'appointments' | 'opd' | 'beds'>('dashboard')
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [beds, setBeds] = useState<Bed[]>([])
  const [loadingDashboard, setLoadingDashboard] = useState(true)
  const [notice, setNotice] = useState('')

  const [appointmentId, setAppointmentId] = useState('')
  const [appointment, setAppointment] = useState<Appointment | null>(null)
  const [appointmentLoading, setAppointmentLoading] = useState(false)
  const [rescheduleDate, setRescheduleDate] = useState('')
  const [rescheduleTime, setRescheduleTime] = useState('')

  const [tokenId, setTokenId] = useState('')
  const [token, setToken] = useState<Token | null>(null)
  const [tokenLoading, setTokenLoading] = useState(false)
  const [queueDoctorId, setQueueDoctorId] = useState('')
  const [queueDate, setQueueDate] = useState(new Date().toISOString().slice(0, 10))

  const [bedFilter, setBedFilter] = useState('')
  const [bedLoading, setBedLoading] = useState(false)

  const activeDoctors = useMemo(() => doctors.filter((d) => d.is_available !== false).length, [doctors])
  const availableBeds = useMemo(() => beds.filter((b) => b.status === 'AVAILABLE').length, [beds])

  async function loadDashboard() {
    setLoadingDashboard(true)
    setNotice('')
    const [doctorResult, bedResult] = await Promise.allSettled([
      api<Doctor[]>('/doctors'),
      api<any>('/beds/availability'),
    ])
    if (doctorResult.status === 'fulfilled') {
      setDoctors(doctorResult.value.data || [])
      setQueueDoctorId((current) => current || doctorResult.value.data?.[0]?.doctor_id || '')
    } else setNotice(doctorResult.reason?.message || 'Unable to load doctors.')
    if (bedResult.status === 'fulfilled') setBeds(bedResult.value.data?.beds || [])
    else setNotice((current) => current || bedResult.reason?.message || 'Unable to load bed availability.')
    setLoadingDashboard(false)
  }

  async function lookupAppointment() {
    if (!appointmentId.trim()) return
    setAppointmentLoading(true)
    setNotice('')
    try {
      const result = await api<Appointment>(`/appointments/${encodeURIComponent(appointmentId.trim())}`)
      setAppointment(result.data)
    } catch (error: any) {
      setAppointment(null)
      setNotice(error.message || 'Appointment not found.')
    } finally {
      setAppointmentLoading(false)
    }
  }

  async function cancelAppointment() {
    if (!appointment) return
    setAppointmentLoading(true)
    try {
      const result = await api<Appointment>(`/appointments/${encodeURIComponent(appointment.id)}/cancel`, { method: 'PATCH' })
      setAppointment(result.data)
      setNotice(result.message || 'Appointment cancelled.')
    } catch (error: any) { setNotice(error.message || 'Could not cancel appointment.') }
    finally { setAppointmentLoading(false) }
  }

  async function rescheduleAppointment() {
    if (!appointment || !rescheduleDate || !rescheduleTime) return
    setAppointmentLoading(true)
    try {
      const result = await api<Appointment>(`/appointments/${encodeURIComponent(appointment.id)}/reschedule`, {
        method: 'PATCH',
        body: JSON.stringify({ appointment_date: rescheduleDate, appointment_time: rescheduleTime }),
      })
      setAppointment(result.data)
      setNotice(result.message || 'Appointment rescheduled.')
    } catch (error: any) { setNotice(error.message || 'Could not reschedule appointment.') }
    finally { setAppointmentLoading(false) }
  }

  async function lookupToken() {
    if (!tokenId.trim()) return
    setTokenLoading(true)
    setNotice('')
    try {
      const result = await api<Token>(`/tokens/${encodeURIComponent(tokenId.trim())}`)
      setToken(result.data)
    } catch (error: any) {
      setToken(null)
      setNotice(error.message || 'Token not found.')
    } finally { setTokenLoading(false) }
  }

  async function transitionToken(action: 'call' | 'skip' | 'complete') {
    if (!token) return
    setTokenLoading(true)
    try {
      const result = await api<Token>(`/tokens/${encodeURIComponent(token.token_id)}/${action}`, { method: 'PATCH' })
      setToken(result.data)
      setNotice(result.message || 'Token updated.')
    } catch (error: any) { setNotice(error.message || 'Token action failed.') }
    finally { setTokenLoading(false) }
  }

  async function loadBeds() {
    setBedLoading(true)
    try {
      const filter = bedFilter.trim() ? `?ward=${encodeURIComponent(bedFilter.trim())}` : ''
      const result = await api<any>(`/beds/availability${filter}`)
      setBeds(result.data?.beds || [])
    } catch (error: any) { setNotice(error.message || 'Could not load beds.') }
    finally { setBedLoading(false) }
  }

  useEffect(() => { loadDashboard() }, [])

  return <div className="min-h-screen bg-slate-100 text-slate-800">
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
        <div className="border-b border-slate-100 px-5 py-6"><div className="flex items-center gap-3"><div className="rounded-xl bg-cyan-700 p-2.5 text-white"><Hospital size={22}/></div><div><div className="font-bold text-slate-900">MediFlow</div><div className="text-xs text-slate-500">Hospital Administration</div></div></div></div>
        <nav className="space-y-1 p-4">
          <NavButton active={view==='dashboard'} icon={<LayoutDashboard size={18}/>} label="Dashboard" onClick={()=>setView('dashboard')}/>
          <NavButton active={view==='appointments'} icon={<CalendarDays size={18}/>} label="Appointments" onClick={()=>setView('appointments')}/>
          <NavButton active={view==='opd'} icon={<ClipboardList size={18}/>} label="OPD Queue" onClick={()=>setView('opd')}/>
          <NavButton active={view==='beds'} icon={<BedDouble size={18}/>} label="Bed Availability" onClick={()=>setView('beds')}/>
        </nav>
      </aside>

      <main className="min-w-0 flex-1">
        <header className="border-b border-slate-200 bg-white px-5 py-5 sm:px-7"><div className="mx-auto flex max-w-7xl items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-700">Hospital operations</p><h1 className="mt-1 text-2xl font-bold text-slate-900">{view === 'dashboard' ? 'Operations Dashboard' : view === 'appointments' ? 'Appointments' : view === 'opd' ? 'OPD Queue' : 'Bed Availability'}</h1></div><button className="button-secondary" onClick={loadDashboard}><RefreshCw size={16}/> Refresh</button></div></header>
        <div className="mx-auto max-w-7xl space-y-6 p-5 sm:p-7">
          {notice && <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800"><XCircle size={17}/>{notice}</div>}

          {view === 'dashboard' && <>
            <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3"><Metric icon={<Stethoscope size={20}/>} label="Active doctors" value={loadingDashboard ? '…' : String(activeDoctors)} /><Metric icon={<BedDouble size={20}/>} label="Available beds" value={loadingDashboard ? '…' : String(availableBeds)} /><Metric icon={<Activity size={20}/>} label="API status" value={loadingDashboard ? 'Loading' : 'Connected'} /></section>
            <section className="grid gap-6 xl:grid-cols-[1.3fr_.7fr]">
              <div className="card overflow-hidden"><div className="border-b border-slate-100 px-5 py-4"><h2 className="font-semibold text-slate-900">Doctors on duty</h2><p className="mt-1 text-sm text-slate-500">Live doctor records from the existing backend.</p></div><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Doctor</th><th className="px-5 py-3">Department</th><th className="px-5 py-3">Status</th></tr></thead><tbody>{doctors.map(d=><tr key={d.doctor_id} className="border-t border-slate-100"><td className="px-5 py-4 font-medium">{d.name || 'Unnamed doctor'}</td><td className="px-5 py-4 text-slate-600">{d.department || d.specialization || '—'}</td><td className="px-5 py-4"><StatusPill active={d.is_available !== false}>{d.is_available === false ? 'Unavailable' : 'Available'}</StatusPill></td></tr>)}{!loadingDashboard && doctors.length===0 && <tr><td colSpan={3} className="px-5 py-10 text-center text-slate-400">No doctors returned.</td></tr>}</tbody></table></div></div>
              <div className="card p-5"><h2 className="font-semibold text-slate-900">Quick operations</h2><div className="mt-4 space-y-3"><QuickAction title="Appointment lookup" text="Open an appointment by ID" onClick={()=>setView('appointments')}/><QuickAction title="OPD queue" text="Manage a live token" onClick={()=>setView('opd')}/><QuickAction title="Bed availability" text="Review current bed status" onClick={()=>setView('beds')}/></div></div>
            </section>
          </>}

          {view === 'appointments' && <section className="card p-5"><div className="mb-5"><h2 className="font-semibold text-slate-900">Appointment operations</h2><p className="mt-1 text-sm text-slate-500">Uses the existing appointment API. No new admin endpoint is required.</p></div><div className="flex flex-col gap-3 sm:flex-row"><input className="input" value={appointmentId} onChange={e=>setAppointmentId(e.target.value)} placeholder="Enter appointment ID"/><button className="button" disabled={!appointmentId.trim() || appointmentLoading} onClick={lookupAppointment}><Search size={16}/> Find appointment</button></div>{appointment && <div className="mt-6 rounded-2xl border border-slate-100 bg-slate-50 p-5"><div className="grid gap-4 sm:grid-cols-2"><Info label="Date" value={appointment.appointment_date || '—'}/><Info label="Time" value={appointment.appointment_time || '—'}/><Info label="Status" value={appointment.status || '—'}/><Info label="Reason" value={appointment.reason || 'Not provided'}/></div><div className="mt-5 flex flex-wrap gap-2"><button className="button-secondary" disabled={appointmentLoading || appointment.status === 'CANCELLED'} onClick={cancelAppointment}><XCircle size={16}/> Cancel</button></div><div className="mt-6 border-t border-slate-200 pt-5"><h3 className="font-medium text-slate-800">Reschedule</h3><div className="mt-3 grid gap-3 sm:grid-cols-3"><input className="input" type="date" value={rescheduleDate} onChange={e=>setRescheduleDate(e.target.value)}/><input className="input" type="time" value={rescheduleTime} onChange={e=>setRescheduleTime(e.target.value)}/><button className="button" disabled={appointmentLoading || !rescheduleDate || !rescheduleTime} onClick={rescheduleAppointment}>Reschedule</button></div></div></div>}</section>}

          {view === 'opd' && <section className="card p-5"><div className="mb-5"><h2 className="font-semibold text-slate-900">OPD token control</h2><p className="mt-1 text-sm text-slate-500">Find a token and perform the backend-supported state transitions.</p></div><div className="flex flex-col gap-3 sm:flex-row"><input className="input" value={tokenId} onChange={e=>setTokenId(e.target.value)} placeholder="Enter token ID"/><button className="button" disabled={!tokenId.trim() || tokenLoading} onClick={lookupToken}><Search size={16}/> Find token</button></div>{token && <div className="mt-6 grid gap-6 xl:grid-cols-[.8fr_1.2fr]"><div className="rounded-2xl bg-cyan-50 p-6"><p className="text-sm font-medium text-cyan-800">Token number</p><p className="mt-1 text-5xl font-bold text-cyan-950">{token.token_number}</p><div className="mt-5 space-y-2 text-sm text-cyan-900"><div className="flex justify-between"><span>Status</span><strong>{token.status}</strong></div><div className="flex justify-between"><span>People ahead</span><strong>{token.people_ahead ?? 0}</strong></div><div className="flex justify-between"><span>Estimated wait</span><strong>{token.estimated_wait_minutes ?? 0} min</strong></div></div></div><div><div className="grid gap-3 sm:grid-cols-3"><button className="action-button" disabled={tokenLoading} onClick={()=>transitionToken('call')}><UserRound size={17}/> Call</button><button className="action-button" disabled={tokenLoading} onClick={()=>transitionToken('skip')}><Clock3 size={17}/> Skip</button><button className="action-button" disabled={tokenLoading} onClick={()=>transitionToken('complete')}><CheckCircle2 size={17}/> Complete</button></div><p className="mt-4 text-sm text-slate-500">Doctor/date filters are intentionally omitted because the current queue endpoints do not expose a real queue listing yet.</p></div></div>}</section>}

          {view === 'beds' && <section className="card p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="font-semibold text-slate-900">Bed availability</h2><p className="mt-1 text-sm text-slate-500">Live inventory returned by the existing database-backed bed service.</p></div><div className="flex gap-2"><input className="input min-w-0" value={bedFilter} onChange={e=>setBedFilter(e.target.value)} placeholder="Ward (optional)"/><button className="button" onClick={loadBeds} disabled={bedLoading}><RefreshCw size={16}/> Load</button></div></div><div className="mt-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Metric icon={<BedDouble size={20}/>} label="Total" value={String(beds.length)} /><Metric icon={<CheckCircle2 size={20}/>} label="Available" value={String(availableBeds)} /><Metric icon={<Activity size={20}/>} label="Occupied" value={String(beds.filter(b=>b.status==='OCCUPIED').length)} /><Metric icon={<XCircle size={20}/>} label="Maintenance" value={String(beds.filter(b=>b.status==='MAINTENANCE').length)} /></div><div className="mt-6 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Bed</th><th className="px-5 py-3">Ward</th><th className="px-5 py-3">Type</th><th className="px-5 py-3">Status</th></tr></thead><tbody>{beds.map((b,i)=><tr key={String(b.id || i)} className="border-t border-slate-100"><td className="px-5 py-4 font-medium">{b.bed_number ?? '—'}</td><td className="px-5 py-4">{b.ward_name || b.ward_type || '—'}</td><td className="px-5 py-4 text-slate-600">{b.bed_type || '—'}</td><td className="px-5 py-4"><StatusPill active={b.status==='AVAILABLE'}>{b.status || 'UNKNOWN'}</StatusPill></td></tr>)}{beds.length===0 && <tr><td colSpan={4} className="px-5 py-10 text-center text-slate-400">No bed records returned.</td></tr>}</tbody></table></div></section>}
        </div>
      </main>
    </div>
  </div>
}

function NavButton({active,icon,label,onClick}:{active:boolean;icon:any;label:string;onClick:()=>void}) { return <button onClick={onClick} className={`nav-item ${active ? 'nav-item-active' : ''}`}>{icon}<span>{label}</span></button> }
function Metric({icon,label,value}:{icon:any;label:string;value:string}) { return <div className="card p-5"><div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700">{icon}</div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-slate-900">{value}</p></div> }
function StatusPill({active,children}:{active:boolean;children:string}) { return <span className={active ? 'rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700' : 'rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500'}>{children}</span> }
function QuickAction({title,text,onClick}:{title:string;text:string;onClick:()=>void}) { return <button onClick={onClick} className="flex w-full items-center justify-between rounded-xl border border-slate-100 bg-slate-50 p-4 text-left transition hover:border-cyan-100 hover:bg-cyan-50"><div><p className="font-medium text-slate-800">{title}</p><p className="mt-1 text-xs text-slate-500">{text}</p></div><span className="text-cyan-700">→</span></button> }
function Info({label,value}:{label:string;value:string}) { return <div><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p><p className="mt-1 font-medium text-slate-800">{value}</p></div> }
createRoot(document.getElementById('root')!).render(<App />)
