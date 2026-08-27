import { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { Activity, Stethoscope, CalendarDays, UsersRound, RefreshCw } from 'lucide-react'
import './styles.css'

type Doctor = { doctor_id?: string; id?: string; name?: string; department?: string; specialization?: string; is_available?: boolean }
type ApiResponse<T> = { success: boolean; data: T; message?: string; error_code?: string }
const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api/v1'

function App() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('Loading doctors from the backend...')
  const [selectedDoctorId, setSelectedDoctorId] = useState('')
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))
  const [slots, setSlots] = useState<any[]>([])
  const [availabilityMessage, setAvailabilityMessage] = useState('')

  async function request<T>(path: string): Promise<ApiResponse<T>> {
    const response = await fetch(`${API_BASE}${path}`)
    const body = await response.json()
    if (!response.ok) throw new Error(body?.message || 'Request failed')
    return body
  }

  async function loadDoctors() {
    setLoading(true)
    try {
      const result = await request<Doctor[]>('/doctors')
      if (!result.success) throw new Error(result.message || 'Failed to load doctors')
      const list = result.data || []
      setDoctors(list)
      setSelectedDoctorId(current => current || (list[0]?.doctor_id || list[0]?.id || ''))
      setMessage(`${list.length} doctor(s) loaded.`)
    } catch (error: any) {
      setDoctors([])
      setMessage(error.message || 'Could not connect to backend.')
    } finally { setLoading(false) }
  }

  async function checkAvailability() {
    if (!selectedDoctorId) { setAvailabilityMessage('Select a doctor first.'); return }
    setLoading(true)
    try {
      const result = await request<any>(`/doctors/${encodeURIComponent(selectedDoctorId)}/availability?date=${encodeURIComponent(date)}`)
      if (!result.success) throw new Error(result.message || 'Availability check failed')
      setSlots(result.data?.slots || [])
      setAvailabilityMessage(result.message || 'Availability loaded.')
    } catch (error: any) {
      setSlots([])
      setAvailabilityMessage(error.message || 'Could not load availability.')
    } finally { setLoading(false) }
  }

  useEffect(() => { loadDoctors() }, [])
  const availableSlots = slots.filter((slot: any) => slot?.available)

  return <div className="min-h-screen bg-slate-950 text-slate-100">
    <header className="border-b border-slate-800 bg-slate-900/70 px-6 py-5"><div className="mx-auto flex max-w-6xl items-center justify-between"><div><h1 className="text-2xl font-bold">Hospital Admin Portal</h1><p className="mt-1 text-sm text-slate-400">Operational access powered by the existing backend</p></div><span className="rounded-full bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400">Connected API</span></div></header>
    <main className="mx-auto max-w-6xl space-y-6 p-6">
      <section className="grid gap-4 md:grid-cols-3"><Stat icon={<Stethoscope size={20}/>} label="Doctors" value={doctors.length.toString()} /><Stat icon={<CalendarDays size={20}/>} label="Available slots" value={availableSlots.length.toString()} /><Stat icon={<Activity size={20}/>} label="System status" value={loading ? 'Loading' : 'Ready'} /></section>
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5"><div className="mb-4 flex items-center justify-between"><div className="flex items-center gap-2"><UsersRound size={20}/><h2 className="font-semibold">Doctors</h2></div><button className="button" onClick={loadDoctors} disabled={loading}><RefreshCw size={16}/> Refresh</button></div><p className="mb-3 text-sm text-slate-400">{message}</p><div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-slate-400"><tr><th className="p-3">Doctor</th><th className="p-3">Department</th><th className="p-3">Status</th></tr></thead><tbody>{doctors.map((doctor,index)=><tr key={doctor.doctor_id || doctor.id || index} className="border-t border-slate-800"><td className="p-3">{doctor.name || '—'}</td><td className="p-3">{doctor.department || doctor.specialization || '—'}</td><td className="p-3">{doctor.is_available === false ? 'Unavailable' : 'Active'}</td></tr>)}{doctors.length===0 && <tr><td colSpan={3} className="p-5 text-center text-slate-500">No doctors available.</td></tr>}</tbody></table></div></section>
      <section className="rounded-xl border border-slate-800 bg-slate-900 p-5"><div className="mb-4 flex items-center gap-2"><CalendarDays size={20}/><h2 className="font-semibold">Doctor Availability</h2></div><div className="grid gap-3 md:grid-cols-3"><select className="input" value={selectedDoctorId} onChange={e=>setSelectedDoctorId(e.target.value)}><option value="">Select doctor</option>{doctors.map((doctor,index)=>{ const id=doctor.doctor_id || doctor.id || ''; return <option key={id || index} value={id}>{doctor.name || 'Unnamed doctor'}{doctor.department ? ` — ${doctor.department}` : ''}</option> })}</select><input className="input" type="date" value={date} onChange={e=>setDate(e.target.value)}/><button className="button" onClick={checkAvailability} disabled={loading}><RefreshCw size={16}/> Check availability</button></div>{availabilityMessage && <p className="mt-3 text-sm text-slate-400">{availabilityMessage}</p>}<div className="mt-4 flex flex-wrap gap-2">{slots.map((slot:any,index)=><span key={index} className={`rounded-lg px-3 py-2 text-sm ${slot.available ? 'bg-emerald-500/15 text-emerald-300' : 'bg-slate-800 text-slate-500'}`}>{slot.time || slot.slot || 'Unknown'} {slot.available ? 'Available' : 'Booked'}</span>)}{slots.length===0 && <span className="text-sm text-slate-500">Select a doctor and check availability.</span>}</div></section>
    </main>
  </div>
}
function Stat({icon,label,value}:{icon:any,label:string,value:string}) { return <div className="rounded-xl border border-slate-800 bg-slate-900 p-5"><div className="mb-3 text-cyan-400">{icon}</div><p className="text-sm text-slate-400">{label}</p><p className="mt-1 text-2xl font-bold">{value}</p></div> }
createRoot(document.getElementById('root')!).render(<App />)
