import { useState, useEffect, useCallback } from 'react'
import { Clock, Users, RefreshCw, Search, Activity, UserCheck, AlertTriangle } from 'lucide-react'
import api from '../services/api'

interface QueueEntry {
  position: number
  entry_id: number
  patient_id: number
  patient_name: string
  triage_score: number
  severity: string
  department: string
  expected_wait_minutes: {
    estimated_minutes: number
    range_min: number
    range_max: number
  }
  check_in_time: string
  symptoms: string[]
}

interface QueueStats {
  total_in_queue: number
  avg_wait_minutes: number
  total_doctors: number
  spare_doctors_available: number
  critical_patients: number
  departments: {
    name: string
    queue_count: number
    crowd_level: string
    avg_wait: number
  }[]
}

const DEPARTMENTS = [
  { value: '', label: 'All Departments' },
  { value: 'general', label: '🏥 General' },
  { value: 'emergency', label: '🚑 Emergency' },
  { value: 'pediatrics', label: '👶 Pediatrics' },
  { value: 'cardiology', label: '❤️ Cardiology' },
  { value: 'neurology', label: '🧠 Neurology' },
  { value: 'orthopedics', label: '🦴 Orthopedics' },
]

export default function QueuePage() {
  const [queue, setQueue] = useState<QueueEntry[]>([])
  const [stats, setStats] = useState<QueueStats | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [searchToken, setSearchToken] = useState('')
  const [selectedDepartment, setSelectedDepartment] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
  const [error, setError] = useState('')

  const fetchQueueData = useCallback(async () => {
    try {
      setError('')
      
      // Fetch queue list and status in parallel
      const [listRes, statusRes] = await Promise.all([
        api.get(`/smartqueue/list?limit=100${selectedDepartment ? `&department=${selectedDepartment}` : ''}`),
        api.get('/smartqueue/status')
      ])
      
      if (listRes.data.success) {
        setQueue(listRes.data.queue || [])
      }
      
      if (statusRes.data.success) {
        setStats(statusRes.data)
      }
      
      setLastUpdated(new Date())
    } catch (err: any) {
      setError('Failed to load queue data. Please try again.')
      console.error('Queue fetch error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [selectedDepartment])

  useEffect(() => {
    fetchQueueData()
    
    // Auto-refresh every 15 seconds
    const interval = setInterval(fetchQueueData, 15000)
    return () => clearInterval(interval)
  }, [fetchQueueData])

  const getSeverityBadge = (score: number) => {
    // Score is already on 1-10 scale from backend
    const score10 = score
    
    // Color based on 1-10 scale
    let colorClass = 'bg-blue-100 text-blue-800 border-blue-300'
    let label = 'Minimal'
    
    if (score10 >= 9) {
      colorClass = 'bg-red-100 text-red-800 border-red-300'
      label = 'Critical'
    } else if (score10 >= 7) {
      colorClass = 'bg-orange-100 text-orange-800 border-orange-300'
      label = 'Urgent'
    } else if (score10 >= 5) {
      colorClass = 'bg-yellow-100 text-yellow-800 border-yellow-300'
      label = 'Moderate'
    } else if (score10 >= 3) {
      colorClass = 'bg-green-100 text-green-800 border-green-300'
      label = 'Low'
    }
    
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium border flex items-center gap-1 ${colorClass}`}>
        <span className="font-bold">{score10}/10</span>
        <span>•</span>
        <span>{label}</span>
      </span>
    )
  }

  const getDepartmentBadge = (dept: string) => {
    const colors: Record<string, string> = {
      general: 'bg-blue-100 text-blue-800',
      emergency: 'bg-red-100 text-red-800',
      pediatrics: 'bg-pink-100 text-pink-800',
      cardiology: 'bg-purple-100 text-purple-800',
      neurology: 'bg-indigo-100 text-indigo-800',
      orthopedics: 'bg-amber-100 text-amber-800',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${colors[dept.toLowerCase()] || 'bg-gray-100 text-gray-800'}`}>
        {dept}
      </span>
    )
  }

  const getCrowdLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100'
      case 'moderate': return 'text-yellow-600 bg-yellow-100'
      case 'high': return 'text-orange-600 bg-orange-100'
      case 'critical': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const filteredQueue = searchToken 
    ? queue.filter(q => 
        `TKN-${q.entry_id}`.toLowerCase().includes(searchToken.toLowerCase()) ||
        q.patient_name.toLowerCase().includes(searchToken.toLowerCase())
      )
    : queue

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">📋 Live Queue Status</h1>
          <p className="text-gray-600">Real-time patient queue updates</p>
          <p className="text-xs text-gray-400 mt-1">
            Last updated: {lastUpdated.toLocaleTimeString()}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          <div className="card text-center bg-white">
            <Users className="h-8 w-8 text-healthcare-blue mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{stats?.total_in_queue || 0}</p>
            <p className="text-sm text-gray-600">In Queue</p>
          </div>
          <div className="card text-center bg-white">
            <Clock className="h-8 w-8 text-healthcare-green mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">~{stats?.avg_wait_minutes || 0} min</p>
            <p className="text-sm text-gray-600">Avg Wait</p>
          </div>
          <div className="card text-center bg-white">
            <UserCheck className="h-8 w-8 text-purple-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{stats?.total_doctors || 0}</p>
            <p className="text-sm text-gray-600">Active Doctors</p>
          </div>
          <div className="card text-center bg-white">
            <Activity className="h-8 w-8 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{stats?.spare_doctors_available || 0}</p>
            <p className="text-sm text-gray-600">Spare Doctors</p>
          </div>
          <div className="card text-center bg-white">
            <AlertTriangle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{stats?.critical_patients || 0}</p>
            <p className="text-sm text-gray-600">Critical Cases</p>
          </div>
        </div>

        {/* Department Status */}
        {stats?.departments && stats.departments.length > 0 && (
          <div className="card mb-6 bg-white">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Department Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {stats.departments.map((dept) => (
                <div 
                  key={dept.name} 
                  className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md
                    ${selectedDepartment === dept.name ? 'border-healthcare-blue bg-blue-50' : 'border-gray-200'}`}
                  onClick={() => setSelectedDepartment(selectedDepartment === dept.name ? '' : dept.name)}
                >
                  <p className="font-medium text-gray-900 capitalize text-sm">{dept.name}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-lg font-bold">{dept.queue_count}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${getCrowdLevelColor(dept.crowd_level)}`}>
                      {dept.crowd_level}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">~{dept.avg_wait} min wait</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search & Filter */}
        <div className="card mb-6 bg-white">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search by token (TKN-XXXXX) or patient name..."
                value={searchToken}
                onChange={(e) => setSearchToken(e.target.value)}
                className="input-field pl-10 w-full"
              />
            </div>
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="input-field md:w-48"
            >
              {DEPARTMENTS.map((dept) => (
                <option key={dept.value} value={dept.value}>{dept.label}</option>
              ))}
            </select>
            <button 
              onClick={fetchQueueData}
              className="btn-primary flex items-center justify-center"
              disabled={isLoading}
            >
              <RefreshCw className={`h-5 w-5 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Queue List */}
        <div className="card bg-white">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">Current Queue</h2>
            <span className="text-sm text-gray-500">
              {filteredQueue.length} patient{filteredQueue.length !== 1 ? 's' : ''}
            </span>
          </div>
          
          {isLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-500">Loading queue...</p>
            </div>
          ) : filteredQueue.length === 0 ? (
            <div className="text-center py-12">
              <Users className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No patients in queue</p>
              <p className="text-sm text-gray-400">
                {selectedDepartment ? `for ${selectedDepartment} department` : ''}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 bg-gray-50">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">#</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Token</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Patient</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Department</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Priority</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Est. Wait</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQueue.map((entry) => (
                    <tr 
                      key={entry.entry_id} 
                      className={`border-b border-gray-100 hover:bg-gray-50 transition-colors
                        ${entry.triage_score >= 5 ? 'bg-red-50' : ''}
                        ${searchToken && `TKN-${entry.entry_id}`.toLowerCase().includes(searchToken.toLowerCase()) ? 'bg-blue-50' : ''}`}
                    >
                      <td className="py-4 px-4">
                        <span className={`font-semibold ${entry.position <= 3 ? 'text-healthcare-blue' : 'text-gray-900'}`}>
                          {entry.position}
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-mono text-sm font-medium">TKN-{entry.entry_id}</span>
                      </td>
                      <td className="py-4 px-4">
                        <div>
                          <p className="font-medium text-gray-900">{entry.patient_name}</p>
                          {entry.symptoms && entry.symptoms.length > 0 && (
                            <p className="text-xs text-gray-500 truncate max-w-[200px]">
                              {entry.symptoms.slice(0, 2).join(', ')}
                              {entry.symptoms.length > 2 && '...'}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        {getDepartmentBadge(entry.department)}
                      </td>
                      <td className="py-4 px-4">
                        {getSeverityBadge(entry.triage_score)}
                      </td>
                      <td className="py-4 px-4 text-gray-600">
                        {entry.expected_wait_minutes?.estimated_minutes === 0 
                          ? <span className="text-green-600 font-semibold">Now</span>
                          : `~${entry.expected_wait_minutes?.estimated_minutes || '?'} min`
                        }
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          🔄 Queue updates automatically every 15 seconds
        </p>
      </div>
    </div>
  )
}
