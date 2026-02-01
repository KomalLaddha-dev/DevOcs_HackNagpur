import { useState, useEffect, useCallback } from 'react'
import { useSelector } from 'react-redux'
import type { RootState } from '../store'
import api from '../services/api'

interface QueueEntry {
  entry_id: number
  patient_id: number
  patient_name: string
  age: number
  symptoms: string[]
  chronic_conditions: string[]
  severity: string
  severity_description: string
  triage_score: number
  priority_score: number
  triage_explanation: string[]
  department: string
  check_in_time: string
  expected_wait_minutes: {
    estimated_minutes: number
    range_min: number
    range_max: number
  } | number
  position: number
  teleconsult_eligible: boolean
}

interface QueueStats {
  total_patients: number
  avg_wait_minutes: number
  critical_count: number
  urgent_count: number
  moderate_count: number
  low_count: number
  minimal_count?: number
  emergency_count: number
}

interface DepartmentStatus {
  department: string
  current_patients: number
  capacity: number
  load_percentage: number
  status: 'normal' | 'busy' | 'overloaded'
  avg_wait_minutes: number
}

interface CurrentPatient {
  entry_id: string
  patient_name: string
  symptoms: string[]
  chronic_conditions: string[]
  severity: string
  triage_explanation: string[]
  check_in_time: string
}

export default function DoctorDashboard() {
  const { user } = useSelector((state: RootState) => state.auth)
  const [queue, setQueue] = useState<QueueEntry[]>([])
  const [stats, setStats] = useState<QueueStats | null>(null)
  const [departmentStatus, setDepartmentStatus] = useState<DepartmentStatus[]>([])
  const [currentPatient, setCurrentPatient] = useState<CurrentPatient | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [selectedDepartment, setSelectedDepartment] = useState<string>('general')
  const [overrideReason, setOverrideReason] = useState('')
  const [showOverrideModal, setShowOverrideModal] = useState(false)
  const [selectedPatientForOverride, setSelectedPatientForOverride] = useState<number | null>(null)

  const fetchCurrentPatient = useCallback(async () => {
    try {
      const res = await api.get(`/smartqueue/current?department=${selectedDepartment}`)
      if (res.data.has_patient && res.data.patient) {
        setCurrentPatient(res.data.patient)
      }
    } catch (err) {
      console.error('Failed to fetch current patient:', err)
    }
  }, [selectedDepartment])

  const fetchQueueData = useCallback(async () => {
    try {
      const [queueRes, deptRes] = await Promise.all([
        api.get(`/smartqueue/list?department=${selectedDepartment}&limit=20`),
        api.get('/smartqueue/crowd/status')
      ])

      setQueue(queueRes.data.queue || [])
      setStats(queueRes.data.stats || null)
      setDepartmentStatus(deptRes.data.departments || [])

      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
    } finally {
      setLoading(false)
    }
  }, [selectedDepartment])

  useEffect(() => {
    fetchCurrentPatient()
    fetchQueueData()
    const interval = setInterval(fetchQueueData, 10000) // Refresh every 10 seconds
    return () => clearInterval(interval)
  }, [fetchQueueData, fetchCurrentPatient])

  const callNextPatient = async () => {
    setActionLoading(true)
    try {
      const res = await api.post(`/smartqueue/next?department=${selectedDepartment}`)
      if (res.data.success) {
        setCurrentPatient(res.data.patient)
        fetchQueueData()
      } else {
        if (res.data.current_patient) {
          setCurrentPatient(res.data.current_patient)
        }
        setError(res.data.message || 'Failed to call patient')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to call patient')
    } finally {
      setActionLoading(false)
    }
  }

  const completeCurrentPatient = async () => {
    setActionLoading(true)
    try {
      await api.post(`/smartqueue/complete?department=${selectedDepartment}`)
      setCurrentPatient(null)
      fetchQueueData()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to complete')
    } finally {
      setActionLoading(false)
    }
  }

  const handleEmergencyOverride = async () => {
    if (!selectedPatientForOverride || !overrideReason.trim()) return

    setActionLoading(true)
    try {
      await api.post('/smartqueue/emergency/escalate', {
        entry_id: selectedPatientForOverride,
        new_severity: 'CRITICAL',
        reason: overrideReason,
        authorized_by: user?.email || 'doctor'
      })
      setShowOverrideModal(false)
      setOverrideReason('')
      setSelectedPatientForOverride(null)
      await fetchQueueData()
    } catch (err: any) {
      console.error('Emergency override error:', err)
      setError(err.response?.data?.detail || err.message || 'Override failed')
    } finally {
      setActionLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL': return 'bg-red-100 text-red-800 border-red-300'
      case 'HIGH': return 'bg-orange-100 text-orange-800 border-orange-300'
      case 'MEDIUM': return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      case 'LOW': return 'bg-green-100 text-green-800 border-green-300'
      default: return 'bg-gray-100 text-gray-800 border-gray-300'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'text-green-600'
      case 'busy': return 'text-yellow-600'
      case 'overloaded': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const departments = ['general', 'emergency', 'pediatrics', 'cardiology', 'orthopedics', 'neurology']

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
            <h1 className="text-3xl font-bold text-gray-900">Doctor Dashboard</h1>
            <p className="text-gray-600">Welcome, Dr. {user?.email?.split('@')[0] || 'Doctor'}</p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="input"
            >
              {departments.map(dept => (
                <option key={dept} value={dept}>
                  {dept.charAt(0).toUpperCase() + dept.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={fetchQueueData}
              className="btn-secondary"
            >
              🔄 Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg mb-6">
            {error}
            <button onClick={() => setError(null)} className="ml-4 text-red-500 hover:text-red-700">✕</button>
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-primary-500">
            <p className="text-sm text-gray-600">In Queue</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.total_patients || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
            <p className="text-sm text-gray-600">Avg Wait</p>
            <p className="text-2xl font-bold text-gray-900">{stats?.avg_wait_minutes?.toFixed(0) || 0}m</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
            <p className="text-sm text-gray-600">Critical</p>
            <p className="text-2xl font-bold text-red-600">{stats?.critical_count || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-orange-500">
            <p className="text-sm text-gray-600">Urgent</p>
            <p className="text-2xl font-bold text-orange-600">{stats?.urgent_count || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
            <p className="text-sm text-gray-600">Moderate</p>
            <p className="text-2xl font-bold text-yellow-600">{stats?.moderate_count || 0}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
            <p className="text-sm text-gray-600">Low</p>
            <p className="text-2xl font-bold text-green-600">{stats?.low_count || 0}</p>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Current Patient Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">👤</span> Current Patient
              </h2>
              
              {currentPatient ? (
                <div className="space-y-4">
                  <div className={`p-4 rounded-lg border-2 ${getSeverityColor(currentPatient.severity)}`}>
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-lg">{currentPatient.patient_name}</h3>
                      <span className="px-2 py-1 rounded text-xs font-semibold">
                        {currentPatient.severity}
                      </span>
                    </div>
                    
                    <div className="space-y-2 text-sm">
                      <div>
                        <strong>Symptoms:</strong>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {currentPatient.symptoms.map((s, i) => (
                            <span key={i} className="bg-white/50 px-2 py-0.5 rounded text-xs">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      {currentPatient.chronic_conditions.length > 0 && (
                        <div>
                          <strong>Chronic Conditions:</strong>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {currentPatient.chronic_conditions.map((c, i) => (
                              <span key={i} className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-xs">
                                {c}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      <div>
                        <strong>Triage Analysis:</strong>
                        <ul className="mt-1 space-y-1">
                          {currentPatient.triage_explanation.map((exp, i) => (
                            <li key={i} className="text-xs bg-white/30 p-1 rounded">
                              📋 {exp}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={completeCurrentPatient}
                    className="w-full btn-primary bg-green-600 hover:bg-green-700"
                  >
                    ✓ Complete Consultation
                  </button>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 mb-4">No patient currently being seen</p>
                  <button
                    onClick={callNextPatient}
                    disabled={actionLoading || queue.length === 0}
                    className="btn-primary w-full disabled:opacity-50"
                  >
                    {actionLoading ? 'Calling...' : '📢 Call Next Patient'}
                  </button>
                </div>
              )}
            </div>

            {/* Department Status */}
            <div className="bg-white rounded-lg shadow p-6 mt-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <span className="text-2xl">🏥</span> Department Load
              </h2>
              <div className="space-y-3">
                {departmentStatus.map(dept => (
                  <div key={dept.department} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium capitalize">{dept.department}</p>
                      <p className="text-xs text-gray-500">
                        {dept.current_patients}/{dept.capacity} patients
                      </p>
                    </div>
                    <div className="text-right">
                      <span className={`font-semibold ${getStatusColor(dept.status)}`}>
                        {dept.load_percentage}%
                      </span>
                      <p className="text-xs text-gray-500">{dept.avg_wait_minutes}m wait</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Patient Queue */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <span className="text-2xl">📋</span> Patient Queue
                  <span className="text-sm font-normal text-gray-500">
                    (Sorted by Priority)
                  </span>
                </h2>
              </div>
              
              <div className="divide-y max-h-[600px] overflow-y-auto">
                {queue.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <p className="text-4xl mb-2">🎉</p>
                    <p>No patients waiting in queue</p>
                  </div>
                ) : (
                  queue.map((patient, index) => (
                    <div
                      key={patient.entry_id}
                      className={`p-4 hover:bg-gray-50 ${index === 0 ? 'bg-primary-50' : ''}`}
                    >
                      <div className="flex justify-between items-start">
                        <div className="flex gap-4">
                          <div className="text-center">
                            <span className="text-2xl font-bold text-gray-400">#{patient.position}</span>
                          </div>
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold">{patient.patient_name}</h3>
                              <span className={`px-2 py-0.5 rounded text-xs font-semibold border ${getSeverityColor(patient.severity)}`}>
                                {patient.triage_score || 5}/10 • {patient.severity}
                              </span>
                              {patient.teleconsult_eligible && (
                                <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                                  📹 Teleconsult OK
                                </span>
                              )}
                            </div>
                            <p className="text-sm text-gray-600">
                              Age: {patient.age} • Priority Score: <strong>{patient.priority_score.toFixed(1)}</strong>
                            </p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {patient.symptoms.slice(0, 3).map((s, i) => (
                                <span key={i} className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs">
                                  {s}
                                </span>
                              ))}
                              {patient.symptoms.length > 3 && (
                                <span className="text-xs text-gray-500">+{patient.symptoms.length - 3} more</span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">
                            Wait: <strong>{typeof patient.expected_wait_minutes === 'object' ? patient.expected_wait_minutes.estimated_minutes : patient.expected_wait_minutes}m</strong>
                          </p>
                          <p className="text-xs text-gray-500">
                            {new Date(patient.check_in_time).toLocaleTimeString()}
                          </p>
                          <button
                            onClick={() => {
                              setSelectedPatientForOverride(patient.entry_id)
                              setShowOverrideModal(true)
                            }}
                            className="text-xs text-red-600 hover:text-red-800 mt-2"
                          >
                            ⚡ Emergency Override
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Override Modal */}
        {showOverrideModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
              <h3 className="text-xl font-bold mb-4 text-red-600">⚠️ Emergency Override</h3>
              <p className="text-gray-600 mb-4">
                This will escalate the patient to CRITICAL priority and move them to the front of the queue.
                This action will be logged for audit purposes.
              </p>
              <textarea
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Enter medical justification for override..."
                className="input w-full h-24 mb-4"
                required
              />
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowOverrideModal(false)
                    setOverrideReason('')
                    setSelectedPatientForOverride(null)
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  onClick={handleEmergencyOverride}
                  disabled={!overrideReason.trim() || actionLoading}
                  className="btn-primary bg-red-600 hover:bg-red-700 flex-1 disabled:opacity-50"
                >
                  {actionLoading ? 'Processing...' : 'Confirm Override'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
