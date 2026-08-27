import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, BedDouble, CalendarDays, ChevronRight, Clock3, Hospital, LayoutDashboard, RefreshCw, Stethoscope, UsersRound } from 'lucide-react'
import './styles.css'

type Doctor = { doctor_id: string; name?: string; department?: string; specialization?: string; is_available?: boolean }
type Slot = { time?: string; available?: boolean }
type ApiResponse<T> = { success: boolean; data: T; message?: string; error_code?: string }
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api/v1'

async function api<T>(path: string): Promise<ApiResponse<T>> {
  const response = await fetch(`${API_BASE}${path}`)
  const body = await response.json().catch(() => ({}))
  if (!response.ok || body.success === false) throw new Error(body.message || 'Backend request failed')
  return body
}

function App() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [bedData, setBedData] = useState<any>(null)
  const [selectedDoctorId, setSelectedDoctorId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [slots, setSlots] = useState<Slot[]>([])
  const [loading, setLoading] = useState(true)
  const [notice, setNotice] = useState('')
  const [availabilityMessage, setAvailabilityMessage] = useState('')

  async function loadDashboard() {
    setLoading(true); setNotice('')
    const results = await Promise.allSettled([api<Doctor[]>('/doctors'), api<any>('/beds/availability')])
    const doctorsResult = results[0]
    const bedsResult = results[1]
    if (doctorsResult.status === 'fulfilled') {
      const list = doctorsResult.value.data || []
      setDoctors(list)
      setSelectedDoctorId(current => current || list[0]?.doctor_id || '')
    } else setNotice(doctorsResult.reason?.message || 'Could not load doctors.')
    if (bedsResult.status === 'fulfilled') setBedData(bedsResult.value.data)
    else setNotice(current => current || bedsResult.reason?.message || 'Could not load bed availability.')
    setLoading(false)
  }

  async function checkAvailability() {
    if (!selectedDoctorId) return setAvailabilityMessage('Select a doctor first.')
    setAvailabilityMessage('Loading availability...')
    try {
      const result = await api<any>(`/doctors/${encodeURIComponent(selectedDoctorId)}/availability?date=${encodeURIComponent(date)}`)
      setSlots(result.data?.slots || [])
      setAvailabilityMessage(result.message || 'Availability loaded.')
    } catch (error: any) {
      setSlots([]); setAvailabilityMessage(error.message || 'Could not load availability.')
    }
  }

  useEffect(() => { loadDashboard() }, [])
  const availableSlots = slots.filter(slot => slot.available).length
  const activeDoctors = doctors.filter(doctor => doctor.is_available !== false).length
  const bedSummary = bedData?.available_beds ?? bedData?.available ?? bedData?.total_available ?? '—'

  return <div className="min-h-screen bg-slate-100">
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white p-5 lg:block">
        <div className="mb-10 flex items-center gap-3"><div className="rounded-xl bg-cyan-700 p-2.5 text-white"><Hospital size={22}/></div><div><p className="font-bold text-slate-900">MediFlow</p><p className="text-xs text-slate-500">Hospital Administration</p></div></div>
        <nav className="space-y-2"><button className="nav-item nav-item-active"><LayoutDashboard size={18}/> Overview</button><button className="nav-item"><UsersRound size={18}/> Clinical Staff</button><button className="nav-item"><CalendarDays size={18}/> Appointments</button><button className="nav-item"><BedDouble size={18}/> Bed Operations</button></nav>
        <div className="mt-10 rounded-2xl bg-slate-50 p-4"><p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Data source</p><p className="mt-2 text-sm font-medium text-slate-700">Existing Flask API</p><p className="mt-1 text-xs text-slate-500">Operational data is read through the current backend.</p></div>
      </aside>
      <main className="min-w-0 flex-1">
        <header className="border-b border-slate-200 bg-white px-6 py-5"><div className="mx-auto flex max-w-7xl items-center justify-between"><div><p className="text-sm font-medium text-cyan-700">Administration</p><h1 className="text-2xl font-bold tracking-tight text-slate-900">Hospital Operations Dashboard</h1></div><button className="button" onClick={loadDashboard} disabled={loading}><RefreshCw size={16} className={loading ? 'animate-spin' : ''}/> Refresh data</button></div></header>
        <div className="mx-auto max-w-7xl space-y-6 p-6">
          {notice && <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">{notice}</div>}
          <section className="grid gap-4 md:grid-cols-3">
            <Metric icon={<Stethoscope size={21}/>} label="Active Doctors" value={loading ? '…' : String(activeDoctors)} note="From current doctors API" />
            <Metric icon={<BedDouble size={21}/>} label="Bed Availability" value={loading ? '…' : String(bedSummary)} note="From current bed availability API" />
            <Metric icon={<Clock3 size={21}/>} label="Available Consultation Slots" value={slots.length ? String(availableSlots) : '—'} note={slots.length ? `For selected doctor on ${date}` : 'Select doctor and date'} />
          </section>
          <section className="grid gap-6 xl:grid-cols-[1.25fr_.75fr]">
            <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 px-5 py-4"><div><h2 className="font-semibold text-slate-900">Clinical Staff</h2><p className="mt-1 text-sm text-slate-500">Live records returned by the doctors service.</p></div><span className="rounded-full bg-cyan-50 px-3 py-1 text-xs font-semibold text-cyan-700">{doctors.length} records</span></div><div className="overflow-x-auto"><table className="w-full min-w-[560px] text-left text-sm"><thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">Doctor</th><th className="px-5 py-3">Department</th><th className="px-5 py-3">Availability</th></tr></thead><tbody>{doctors.map(doctor => <tr key={doctor.doctor_id} className="border-t border-slate-100"><td className="px-5 py-4 font-medium text-slate-800">{doctor.name || 'Unnamed clinician'}</td><td className="px-5 py-4 text-slate-600">{doctor.department || doctor.specialization || '—'}</td><td className="px-5 py-4"><span className={doctor.is_available === false ? 'rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500' : 'rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700'}>{doctor.is_available === false ? 'Unavailable' : 'Available'}</span></td></tr>)}{!loading && doctors.length === 0 && <tr><td colSpan={3} className="px-5 py-10 text-center text-slate-400">No doctor records returned.</td></tr>}</tbody></table></div></div>
            <div className="card p-5"><div className="mb-5"><h2 className="font-semibold text-slate-900">Consultation Availability</h2><p className="mt-1 text-sm text-slate-500">Check real availability from the existing scheduling service.</p></div><div className="space-y-3"><select className="input" value={selectedDoctorId} onChange={e => setSelectedDoctorId(e.target.value)}><option value="">Select a clinician</option>{doctors.map(doctor => <option key={doctor.doctor_id} value={doctor.doctor_id}>{doctor.name || 'Unnamed clinician'}{doctor.department ? ` — ${doctor.department}` : ''}</option>)}</select><input className="input" type="date" value={date} onChange={e => setDate(e.target.value)}/><button className="button w-full" onClick={checkAvailability}><CalendarDays size={16}/> Check availability</button></div>{availabilityMessage && <p className="mt-4 text-sm text-slate-500">{availabilityMessage}</p>}<div className="mt-5 space-y-2">{slots.map((slot,index) => <div key={`${slot.time}-${index}`} className="flex items-center justify-between rounded-xl border border-slate-100 px-3.5 py-3"><span className="font-medium text-slate-700">{slot.time || 'Time unavailable'}</span><span className={slot.available ? 'text-xs font-semibold text-emerald-700' : 'text-xs font-semibold text-slate-400'}>{slot.available ? 'Available' : 'Unavailable'}</span></div>)}{slots.length === 0 && <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">No availability has been requested yet.</div>}</div></div>
          </section>
          <section className="card p-5"><div className="mb-4 flex items-center gap-2"><Activity size={19} className="text-cyan-700"/><h2 className="font-semibold text-slate-900">Operational Integration</h2></div><div className="grid gap-3 md:grid-cols-3 text-sm"><Integration title="Doctors" text="GET /api/v1/doctors"/><Integration title="Availability" text="GET /api/v1/doctors/:doctor_id/availability"/><Integration title="Beds" text="GET /api/v1/beds/availability"/></div><p className="mt-4 text-xs text-slate-400">The browser calls the existing Flask API. The backend remains responsible for database access and business logic.</p></section>
        </div>
      </main>
    </div>
  </div>
}
function Metric({icon,label,value,note}:{icon:any;label:string;value:string;note:string}) { return <div className="card p-5"><div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700">{icon}</div><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-1 text-3xl font-bold tracking-tight text-slate-900">{value}</p><p className="mt-2 text-xs text-slate-400">{note}</p></div> }
function Integration({title,text}:{title:string;text:string}) { return <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3"><div><p className="font-medium text-slate-700">{title}</p><p className="mt-1 text-xs text-slate-500">{text}</p></div><ChevronRight size={16} className="text-slate-400"/></div> }
createRoot(document.getElementById('root')!).render(<App />)
