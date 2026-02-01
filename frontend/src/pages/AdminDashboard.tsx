import { useState, useEffect, useCallback } from 'react'

interface DepartmentStatus {
  department: string
  code: string
  current_queue: number
  capacity: number
  crowd_level: string
  avg_wait_minutes: number
  utilization_percent: number
  active_doctors: number
  spare_doctors_assigned: number
}

interface SpareDoctor {
  doctor_id: number
  name: string
  specialty: string
  hospital_origin: string
  status: string
  assigned_department: string | null
  assigned_at: string | null
  patients_seen: number
  max_patients: number
  supports_teleconsult: boolean
  available_slots: number
}

interface OverrideLog {
  timestamp: string
  entry_id: string
  patient_name: string
  old_severity: string
  new_severity: string
  reason: string
  authorized_by: string
}

interface ActivityLog {
  log_id: string
  activity_type: string
  timestamp: string
  title: string
  description: string
  details: Record<string, any>
  severity_score: number | null
  severity_label: string
  department: string | null
  actor: string
}

interface ActivityStats {
  total_logs: number
  by_type: Record<string, number>
  checkin_severity: Record<string, number>
  total_checkins: number
  total_doctor_assignments: number
  total_ai_decisions: number
  total_overrides: number
}

interface SystemMetrics {
  total_checkins_today: number
  total_served_today: number
  avg_triage_score: number
  teleconsult_redirects: number
  emergency_overrides: number
  peak_hour: string
}

interface LoadSuggestion {
  suggestion: string
  from_department: string
  to_department: string
  reason: string
}

export default function AdminDashboard() {
  const [departmentStatus, setDepartmentStatus] = useState<DepartmentStatus[]>([])
  const [spareDoctors, setSpareDoctors] = useState<SpareDoctor[]>([])
  const [overrideLogs, setOverrideLogs] = useState<OverrideLog[]>([])
  const [activityLogs, setActivityLogs] = useState<ActivityLog[]>([])
  const [activityStats, setActivityStats] = useState<ActivityStats | null>(null)
  const [loadSuggestions, setLoadSuggestions] = useState<LoadSuggestion[]>([])
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'overview' | 'doctors' | 'ai' | 'logs' | 'audit'>('overview')
  const [aiInsights, setAiInsights] = useState<any>(null)
  const [aiLoading, setAiLoading] = useState(false)
  const [waitProtection, setWaitProtection] = useState<any>(null)
  const [logFilter, setLogFilter] = useState<string>('all')

  const API_BASE = '/api/v1/smartqueue'

  const fetchData = useCallback(async () => {
    try {
      const [deptRes, doctorsRes, logsRes, suggestionsRes, activityRes] = await Promise.all([
        fetch(`${API_BASE}/crowd/status`),
        fetch(`${API_BASE}/doctors/spare`),
        fetch(`${API_BASE}/emergency/logs`),
        fetch(`${API_BASE}/crowd/suggestions`),
        fetch(`${API_BASE}/activity/logs?limit=100`)
      ])

      if (deptRes.ok) {
        const deptData = await deptRes.json()
        setDepartmentStatus(deptData.departments || [])
      }

      if (doctorsRes.ok) {
        const doctorData = await doctorsRes.json()
        setSpareDoctors(doctorData.doctors || [])
      }

      if (logsRes.ok) {
        const logData = await logsRes.json()
        setOverrideLogs(logData.logs || [])
      }

      if (suggestionsRes.ok) {
        const suggestionData = await suggestionsRes.json()
        setLoadSuggestions(suggestionData.suggestions || [])
      }

      if (activityRes.ok) {
        const activityData = await activityRes.json()
        setActivityLogs(activityData.logs || [])
        setActivityStats(activityData.stats || null)
      }

      // Mock metrics for demo (would come from analytics endpoint)
      setMetrics({
        total_checkins_today: Math.floor(Math.random() * 150) + 50,
        total_served_today: Math.floor(Math.random() * 120) + 40,
        avg_triage_score: parseFloat((Math.random() * 30 + 40).toFixed(1)),
        teleconsult_redirects: Math.floor(Math.random() * 20) + 5,
        emergency_overrides: overrideLogs.length,
        peak_hour: '10:00 AM - 11:00 AM'
      })

      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 15000) // Refresh every 15 seconds
    return () => clearInterval(interval)
  }, [fetchData])

  const assignDoctorToDepartment = async (doctorId: number, department: string) => {
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE}/doctors/spare/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctor_id: doctorId, department, reason: 'Manual assignment from admin dashboard' })
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Assignment failed')
      }
      fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Assignment failed')
    } finally {
      setActionLoading(false)
    }
  }

  const releaseDoctor = async (doctorId: number) => {
    setActionLoading(true)
    try {
      const res = await fetch(`${API_BASE}/doctors/spare/release`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctor_id: doctorId, reason: 'Manual release from admin dashboard' })
      })
      if (!res.ok) throw new Error('Release failed')
      fetchData()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Release failed')
    } finally {
      setActionLoading(false)
    }
  }

  const fetchAiInsights = async () => {
    setAiLoading(true)
    try {
      const res = await fetch(`${API_BASE}/ai/insights`)
      if (res.ok) {
        const data = await res.json()
        setAiInsights(data)
      }
    } catch (err) {
      console.error('Failed to fetch AI insights:', err)
    } finally {
      setAiLoading(false)
    }
  }

  const runAiAutoAllocate = async () => {
    setAiLoading(true)
    try {
      const res = await fetch(`${API_BASE}/ai/auto-allocate`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        alert(`AI Allocation Complete!\n${data.actions_taken} actions taken across ${data.departments_analyzed} departments.`)
        fetchData()
        fetchAiInsights()
      }
    } catch (err) {
      setError('AI auto-allocation failed')
    } finally {
      setAiLoading(false)
    }
  }

  const runAiForDepartment = async (department: string) => {
    setAiLoading(true)
    try {
      const res = await fetch(`${API_BASE}/ai/auto-allocate/${department}`, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        if (data.executed) {
          alert(`AI Action: ${data.decision.action}\n${data.decision.reason}`)
        } else {
          alert(`AI Recommendation: ${data.decision.reason}\nConfidence: ${(data.decision.confidence * 100).toFixed(0)}%`)
        }
        fetchData()
        fetchAiInsights()
      }
    } catch (err) {
      setError(`AI analysis failed for ${department}`)
    } finally {
      setAiLoading(false)
    }
  }

  const fetchWaitProtectionStatus = async (department: string) => {
    try {
      const res = await fetch(`${API_BASE}/ai/wait-impact/${department}`)
      if (res.ok) {
        const data = await res.json()
        setWaitProtection(data)
      }
    } catch (err) {
      console.error('Failed to fetch wait protection status:', err)
    }
  }

  const runWaitTimeProtection = async (department?: string) => {
    setAiLoading(true)
    try {
      const url = department 
        ? `${API_BASE}/ai/protect-wait-times/${department}`
        : `${API_BASE}/ai/protect-all`
      const res = await fetch(url, { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        const msg = department
          ? `${data.message}\nDoctors assigned: ${data.doctors_assigned || 0}`
          : `Checked ${data.departments_checked} departments\nProtected: ${data.departments_protected}\nDoctors assigned: ${data.total_doctors_assigned}`
        alert(`Wait Time Protection\n\n${msg}`)
        fetchData()
        fetchAiInsights()
      }
    } catch (err) {
      setError('Wait time protection failed')
    } finally {
      setAiLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'bg-green-100 text-green-800 border-green-300'
      case 'busy': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'overloaded': return 'bg-red-100 text-red-800 border-red-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getLoadBarColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-6">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600">Hospital Operations Control Center</p>
          </div>
          <button onClick={fetchData} className="btn-secondary">
            🔄 Refresh Data
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
            {error}
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">✕</button>
          </div>
        )}

        {/* Key Metrics */}
        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-primary-500">
              <p className="text-sm text-gray-600">Check-ins Today</p>
              <p className="text-2xl font-bold text-gray-900">{metrics.total_checkins_today}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
              <p className="text-sm text-gray-600">Patients Served</p>
              <p className="text-2xl font-bold text-green-600">{metrics.total_served_today}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
              <p className="text-sm text-gray-600">Avg Triage Score</p>
              <p className="text-2xl font-bold text-blue-600">{metrics.avg_triage_score}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
              <p className="text-sm text-gray-600">Teleconsult Redirects</p>
              <p className="text-2xl font-bold text-purple-600">{metrics.teleconsult_redirects}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
              <p className="text-sm text-gray-600">Emergency Overrides</p>
              <p className="text-2xl font-bold text-red-600">{metrics.emergency_overrides}</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow border-l-4 border-orange-500">
              <p className="text-sm text-gray-600">Peak Hour</p>
              <p className="text-lg font-bold text-orange-600">{metrics.peak_hour}</p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex space-x-8 overflow-x-auto">
            {[
              { id: 'overview', label: '📊 Overview', icon: '📊' },
              { id: 'doctors', label: '👨‍⚕️ Spare Doctors', icon: '👨‍⚕️' },
              { id: 'ai', label: '🤖 AI Allocation', icon: '🤖' },
              { id: 'logs', label: '📜 Activity Logs', icon: '📜' },
              { id: 'audit', label: '📋 Override Audit', icon: '📋' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => {
                  setActiveTab(tab.id as typeof activeTab)
                  if (tab.id === 'ai') fetchAiInsights()
                }}
                className={`py-4 px-1 border-b-2 font-medium text-sm transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Department Status */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">🏥 Department Load Status</h2>
              {departmentStatus.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p>No department data available. Seed demo data to see departments.</p>
                </div>
              ) : (
              <div className="space-y-4">
                {departmentStatus.map(dept => (
                  <div key={dept.department} className="border rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <div>
                        <h3 className="font-semibold capitalize">{dept.department}</h3>
                        <p className="text-sm text-gray-600">
                          {dept.current_queue}/{dept.capacity} patients • {dept.avg_wait_minutes}m avg wait
                        </p>
                        <p className="text-xs text-gray-500">
                          {dept.active_doctors} doctors active • {dept.spare_doctors_assigned} spare assigned
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(dept.crowd_level)}`}>
                        {dept.crowd_level.toUpperCase()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className={`h-3 rounded-full transition-all ${getLoadBarColor(dept.utilization_percent)}`}
                        style={{ width: `${Math.min(dept.utilization_percent, 100)}%` }}
                      />
                    </div>
                    <p className="text-right text-sm text-gray-600 mt-1">{dept.utilization_percent}% capacity</p>
                  </div>
                ))}
              </div>
              )}
            </div>

            {/* Load Balancing Suggestions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4">💡 Load Balancing Suggestions</h2>
              {loadSuggestions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <p className="text-4xl mb-2">✅</p>
                  <p>All departments are balanced. No actions needed.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {loadSuggestions.map((suggestion, i) => (
                    <div key={i} className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                      <p className="font-medium text-yellow-800">{suggestion.suggestion}</p>
                      <p className="text-sm text-yellow-600 mt-1">
                        {suggestion.from_department} → {suggestion.to_department}
                      </p>
                      <p className="text-xs text-gray-600 mt-1">{suggestion.reason}</p>
                    </div>
                  ))}
                </div>
              )}

              {/* Real-time Activity */}
              <div className="mt-6 pt-6 border-t">
                <h3 className="font-semibold mb-3">📈 System Health</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <p className="text-2xl">🟢</p>
                    <p className="text-sm font-medium text-green-800">Triage Engine</p>
                    <p className="text-xs text-green-600">Operational</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <p className="text-2xl">🟢</p>
                    <p className="text-sm font-medium text-green-800">Queue System</p>
                    <p className="text-xs text-green-600">Operational</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <p className="text-2xl">🟢</p>
                    <p className="text-sm font-medium text-green-800">Teleconsult</p>
                    <p className="text-xs text-green-600">Available</p>
                  </div>
                  <div className="bg-green-50 rounded-lg p-3 text-center">
                    <p className="text-2xl">🟢</p>
                    <p className="text-sm font-medium text-green-800">Doctor Pool</p>
                    <p className="text-xs text-green-600">{spareDoctors.filter(d => d.status === 'available').length} available</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'doctors' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold">👨‍⚕️ Spare Doctor Pool Management</h2>
              <p className="text-gray-600 text-sm">Cross-hospital doctors available for surge support</p>
              <div className="mt-2 flex gap-4 text-sm">
                <span className="text-green-600">● {spareDoctors.filter(d => d.status === 'available').length} Available</span>
                <span className="text-orange-600">● {spareDoctors.filter(d => d.status === 'assigned').length} Assigned</span>
              </div>
            </div>
            <div className="divide-y">
              {spareDoctors.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <p>No spare doctors in the pool</p>
                </div>
              ) : (
                spareDoctors.map(doctor => (
                  <div key={doctor.doctor_id} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full ${doctor.status === 'available' ? 'bg-green-500' : 'bg-orange-500'}`} />
                      <div>
                        <h3 className="font-semibold">{doctor.name}</h3>
                        <p className="text-sm text-gray-600">
                          {doctor.specialty} • {doctor.hospital_origin}
                        </p>
                        <p className="text-xs text-gray-500">
                          {doctor.supports_teleconsult && '📹 Teleconsult OK • '}
                          Slots: {doctor.available_slots}/{doctor.max_patients}
                        </p>
                        {doctor.assigned_department && (
                          <p className="text-sm text-primary-600">
                            Currently assigned to: <strong className="capitalize">{doctor.assigned_department}</strong>
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {doctor.status === 'available' ? (
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              assignDoctorToDepartment(doctor.doctor_id, e.target.value)
                            }
                          }}
                          disabled={actionLoading}
                          className="input text-sm"
                          defaultValue=""
                        >
                          <option value="" disabled>Assign to...</option>
                          <option value="general">General</option>
                          <option value="emergency">Emergency</option>
                          <option value="pediatrics">Pediatrics</option>
                          <option value="cardiology">Cardiology</option>
                          <option value="orthopedics">Orthopedics</option>
                          <option value="neurology">Neurology</option>
                        </select>
                      ) : (
                        <button
                          onClick={() => releaseDoctor(doctor.doctor_id)}
                          disabled={actionLoading}
                          className="btn-secondary text-sm"
                        >
                          Release
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'ai' && (
          <div className="space-y-6">
            {/* AI Control Panel */}
            <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg shadow p-6 text-white">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-bold mb-2">🤖 AI Doctor Allocation System</h2>
                  <p className="text-purple-100">
                    Intelligent spare doctor assignment using predictive analytics
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={fetchAiInsights}
                    disabled={aiLoading}
                    className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition-colors"
                  >
                    🔄 Refresh
                  </button>
                  <button
                    onClick={() => runWaitTimeProtection()}
                    disabled={aiLoading}
                    className="bg-green-400 text-green-900 hover:bg-green-300 px-4 py-2 rounded-lg font-semibold transition-colors"
                  >
                    🛡️ Protect All Wait Times
                  </button>
                  <button
                    onClick={runAiAutoAllocate}
                    disabled={aiLoading}
                    className="bg-white text-purple-600 hover:bg-purple-50 px-4 py-2 rounded-lg font-semibold transition-colors"
                  >
                    {aiLoading ? '⏳ Running...' : '▶️ Run AI Auto-Allocate'}
                  </button>
                </div>
              </div>
              
              {aiInsights && (
                <div className="grid grid-cols-3 gap-4 mt-6">
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-purple-200 text-sm">Available Spare Doctors</p>
                    <p className="text-3xl font-bold">{aiInsights.spare_pool_summary?.available || 0}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-purple-200 text-sm">Currently Assigned</p>
                    <p className="text-3xl font-bold">{aiInsights.spare_pool_summary?.assigned || 0}</p>
                  </div>
                  <div className="bg-white/10 rounded-lg p-4">
                    <p className="text-purple-200 text-sm">Departments Need Attention</p>
                    <p className="text-3xl font-bold">{aiInsights.high_priority_departments?.length || 0}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Wait Time Protection Info Box */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-6">
              <div className="flex items-start gap-4">
                <div className="text-4xl">🛡️</div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-800">Wait Time Protection System</h3>
                  <p className="text-green-700 mt-1">
                    When critical patients arrive, spare doctors are <strong>automatically assigned</strong> to ensure 
                    existing patients' wait times don't increase. The 10th patient in queue will still be seen at their 
                    original expected time - spare doctors handle the critical surge.
                  </p>
                  <div className="flex gap-4 mt-4">
                    <div className="bg-white rounded-lg px-4 py-2 shadow-sm">
                      <p className="text-xs text-gray-500">Formula</p>
                      <p className="font-mono text-sm text-green-800">Extra Doctors = Critical Patients ÷ Current Doctors</p>
                    </div>
                    <div className="bg-white rounded-lg px-4 py-2 shadow-sm">
                      <p className="text-xs text-gray-500">Trigger</p>
                      <p className="text-sm text-green-800">Auto-activates on CRITICAL/HIGH patient check-in</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Department AI Analysis */}
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h3 className="text-lg font-semibold">📊 Department AI Analysis</h3>
                <p className="text-gray-600 text-sm">Real-time AI scoring and recommendations per department</p>
              </div>
              <div className="divide-y">
                {aiInsights?.department_analysis?.map((dept: any) => (
                  <div key={dept.department} className="p-4 flex items-center justify-between hover:bg-gray-50">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <h4 className="font-semibold capitalize">{dept.department}</h4>
                        {dept.needs_attention && (
                          <span className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded-full">
                            ⚠️ Needs Attention
                          </span>
                        )}
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          dept.trend === 'increasing' ? 'bg-red-100 text-red-700' :
                          dept.trend === 'decreasing' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {dept.trend === 'increasing' ? '📈' : dept.trend === 'decreasing' ? '📉' : '➡️'} {dept.trend}
                        </span>
                      </div>
                      <div className="grid grid-cols-5 gap-4 mt-2 text-sm">
                        <div>
                          <span className="text-gray-500">Queue:</span>
                          <span className="ml-1 font-medium">{dept.queue_size}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Utilization:</span>
                          <span className={`ml-1 font-medium ${dept.utilization >= 80 ? 'text-red-600' : dept.utilization >= 60 ? 'text-yellow-600' : 'text-green-600'}`}>
                            {dept.utilization?.toFixed(0)}%
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Critical:</span>
                          <span className={`ml-1 font-medium ${dept.critical_patients > 0 ? 'text-red-600' : ''}`}>
                            {dept.critical_patients}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Predicted (30min):</span>
                          <span className="ml-1 font-medium">{dept.predicted_30min}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Spare Drs:</span>
                          <span className="ml-1 font-medium">{dept.spare_doctors}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-xs text-gray-500">AI Score</p>
                        <div className={`text-2xl font-bold ${
                          dept.ai_score >= 0.7 ? 'text-red-600' :
                          dept.ai_score >= 0.5 ? 'text-yellow-600' :
                          'text-green-600'
                        }`}>
                          {(dept.ai_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <button
                          onClick={() => runAiForDepartment(dept.department)}
                          disabled={aiLoading}
                          className="btn-primary text-sm"
                        >
                          🤖 AI Assign
                        </button>
                        {dept.critical_patients > 0 && (
                          <button
                            onClick={() => runWaitTimeProtection(dept.department)}
                            disabled={aiLoading}
                            className="bg-green-500 hover:bg-green-600 text-white text-sm px-3 py-1.5 rounded-lg"
                          >
                            🛡️ Protect Wait
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                )) || (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-4xl mb-2">🔄</p>
                    <p>Loading AI analysis...</p>
                  </div>
                )}
              </div>
            </div>

            {/* Recent AI Decisions */}
            {aiInsights?.recent_ai_decisions?.length > 0 && (
              <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b">
                  <h3 className="text-lg font-semibold">🕐 Recent AI Decisions</h3>
                </div>
                <div className="divide-y">
                  {aiInsights.recent_ai_decisions.map((decision: any, i: number) => (
                    <div key={i} className="p-4 flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        decision.action === 'assign' ? 'bg-green-100 text-green-600' :
                        decision.action === 'release' ? 'bg-blue-100 text-blue-600' :
                        'bg-gray-100 text-gray-600'
                      }`}>
                        {decision.action === 'assign' ? '➕' : decision.action === 'release' ? '➖' : '⏸️'}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium capitalize">{decision.action} - {decision.department}</p>
                        <p className="text-sm text-gray-600">{decision.reason}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold">{(decision.confidence * 100).toFixed(0)}%</p>
                        <p className="text-xs text-gray-500">confidence</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Model Config */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-semibold text-gray-700 mb-2">⚙️ AI Model Configuration</h4>
              <div className="flex flex-wrap gap-4 text-sm">
                {aiInsights?.model_config?.weights && Object.entries(aiInsights.model_config.weights).map(([key, value]: [string, any]) => (
                  <div key={key} className="bg-white px-3 py-1 rounded shadow-sm">
                    <span className="text-gray-500 capitalize">{key.replace('_', ' ')}:</span>
                    <span className="ml-1 font-medium">{(value * 100).toFixed(0)}%</span>
                  </div>
                ))}
                <div className="bg-white px-3 py-1 rounded shadow-sm">
                  <span className="text-gray-500">Assign Threshold:</span>
                  <span className="ml-1 font-medium">{((aiInsights?.model_config?.assign_threshold || 0.65) * 100).toFixed(0)}%</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Activity Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-6">
            {/* Activity Stats */}
            {activityStats && (
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
                  <p className="text-sm text-gray-600">Total Check-ins</p>
                  <p className="text-2xl font-bold text-blue-600">{activityStats.total_checkins}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
                  <p className="text-sm text-gray-600">Doctor Assignments</p>
                  <p className="text-2xl font-bold text-green-600">{activityStats.total_doctor_assignments}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                  <p className="text-sm text-gray-600">AI Decisions</p>
                  <p className="text-2xl font-bold text-purple-600">{activityStats.total_ai_decisions}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
                  <p className="text-sm text-gray-600">Critical Patients</p>
                  <p className="text-2xl font-bold text-red-600">{activityStats.checkin_severity?.critical || 0}</p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
                  <p className="text-sm text-gray-600">Total Events</p>
                  <p className="text-2xl font-bold text-yellow-600">{activityStats.total_logs}</p>
                </div>
              </div>
            )}

            {/* Filter Buttons */}
            <div className="bg-white rounded-lg shadow p-4">
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'all', label: '📋 All', color: 'gray' },
                  { id: 'patient_checkin', label: '🏥 Check-ins', color: 'blue' },
                  { id: 'doctor_assigned', label: '👨‍⚕️ Doctor Assigned', color: 'green' },
                  { id: 'doctor_released', label: '🔓 Doctor Released', color: 'orange' },
                  { id: 'ai_allocation', label: '🤖 AI Decisions', color: 'purple' },
                  { id: 'emergency_override', label: '🚨 Overrides', color: 'red' }
                ].map(filter => (
                  <button
                    key={filter.id}
                    onClick={() => setLogFilter(filter.id)}
                    className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                      logFilter === filter.id
                        ? `bg-${filter.color}-500 text-white`
                        : `bg-${filter.color}-100 text-${filter.color}-700 hover:bg-${filter.color}-200`
                    }`}
                    style={{
                      backgroundColor: logFilter === filter.id 
                        ? (filter.color === 'gray' ? '#6b7280' : filter.color === 'blue' ? '#3b82f6' : filter.color === 'green' ? '#22c55e' : filter.color === 'orange' ? '#f97316' : filter.color === 'purple' ? '#a855f7' : '#ef4444')
                        : undefined,
                      color: logFilter === filter.id ? 'white' : undefined
                    }}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Activity Log Table */}
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold">📜 Activity Log</h2>
                <p className="text-gray-600 text-sm">Real-time log of all system activities with severity scores (1-10 scale)</p>
              </div>
              <div className="overflow-x-auto max-h-[600px] overflow-y-auto">
                {activityLogs.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-4xl mb-2">📭</p>
                    <p>No activity logged yet. Check in a patient to see logs.</p>
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Time</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Title</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Severity</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {activityLogs
                        .filter(log => logFilter === 'all' || log.activity_type === logFilter)
                        .map((log, i) => (
                        <tr key={log.log_id || i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm whitespace-nowrap">
                            {new Date(log.timestamp).toLocaleTimeString()}
                            <br />
                            <span className="text-xs text-gray-400">
                              {new Date(log.timestamp).toLocaleDateString()}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${
                              log.activity_type === 'patient_checkin' ? 'bg-blue-100 text-blue-800' :
                              log.activity_type === 'doctor_assigned' ? 'bg-green-100 text-green-800' :
                              log.activity_type === 'doctor_released' ? 'bg-orange-100 text-orange-800' :
                              log.activity_type === 'ai_allocation' ? 'bg-purple-100 text-purple-800' :
                              log.activity_type === 'emergency_override' ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              {log.activity_type === 'patient_checkin' ? '🏥 Check-in' :
                               log.activity_type === 'doctor_assigned' ? '👨‍⚕️ Assigned' :
                               log.activity_type === 'doctor_released' ? '🔓 Released' :
                               log.activity_type === 'ai_allocation' ? '🤖 AI' :
                               log.activity_type === 'emergency_override' ? '🚨 Override' :
                               log.activity_type.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <p className="font-medium">{log.title}</p>
                            <p className="text-xs text-gray-500">{log.description}</p>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {log.severity_score !== null ? (
                              <div className="flex items-center gap-2">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm ${
                                  log.severity_score >= 9 ? 'bg-red-600' :
                                  log.severity_score >= 7 ? 'bg-orange-500' :
                                  log.severity_score >= 5 ? 'bg-yellow-500' :
                                  log.severity_score >= 3 ? 'bg-blue-500' :
                                  'bg-green-500'
                                }`}>
                                  {log.severity_score}
                                </div>
                                <span className={`text-xs font-medium ${
                                  log.severity_label === 'CRITICAL' ? 'text-red-600' :
                                  log.severity_label === 'HIGH' ? 'text-orange-600' :
                                  log.severity_label === 'MODERATE' ? 'text-yellow-600' :
                                  log.severity_label === 'LOW' ? 'text-blue-600' :
                                  'text-green-600'
                                }`}>
                                  {log.severity_label}
                                </span>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {log.department ? (
                              <span className="capitalize">{log.department}</span>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-sm">
                            <span className={`text-xs px-2 py-1 rounded ${
                              log.actor === 'ai_system' ? 'bg-purple-100 text-purple-700' :
                              log.actor === 'admin' ? 'bg-blue-100 text-blue-700' :
                              log.actor === 'patient_self' ? 'bg-green-100 text-green-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {log.actor === 'ai_system' ? '🤖 AI System' :
                               log.actor === 'admin' ? '👤 Admin' :
                               log.actor === 'patient_self' ? '🧑 Patient' :
                               log.actor}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-sm">
                            {log.details && (
                              <details className="cursor-pointer">
                                <summary className="text-blue-600 hover:underline">View</summary>
                                <pre className="mt-2 p-2 bg-gray-100 rounded text-xs overflow-auto max-w-xs">
                                  {JSON.stringify(log.details, null, 2)}
                                </pre>
                              </details>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'audit' && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-xl font-semibold">📋 Emergency Override Audit Log</h2>
              <p className="text-gray-600 text-sm">Complete audit trail of all priority overrides</p>
            </div>
            <div className="overflow-x-auto">
              {overrideLogs.length === 0 ? (
                <div className="p-8 text-center text-gray-500">
                  <p className="text-4xl mb-2">📝</p>
                  <p>No override events logged yet</p>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Change</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Authorized By</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {overrideLogs.map((log, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-sm">
                          {new Date(log.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">
                          {log.patient_name || log.entry_id}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className="text-gray-500">{log.old_severity}</span>
                          <span className="mx-2">→</span>
                          <span className="font-semibold text-red-600">{log.new_severity}</span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                          {log.reason}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          {log.authorized_by}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
