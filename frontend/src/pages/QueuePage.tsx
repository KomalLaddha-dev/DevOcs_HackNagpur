import { useState, useEffect } from 'react'
import { Clock, Users, RefreshCw } from 'lucide-react'

interface QueueEntry {
  position: number
  tokenNumber: string
  triageScore: number
  status: string
  estimatedWait: number
}

export default function QueuePage() {
  const [queue, setQueue] = useState<QueueEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [searchToken, setSearchToken] = useState('')

  useEffect(() => {
    // Mock queue data
    const mockQueue: QueueEntry[] = [
      { position: 1, tokenNumber: 'SC202601310001', triageScore: 5, status: 'In Consultation', estimatedWait: 0 },
      { position: 2, tokenNumber: 'SC202601310015', triageScore: 4, status: 'Called', estimatedWait: 5 },
      { position: 3, tokenNumber: 'SC202601310023', triageScore: 4, status: 'Waiting', estimatedWait: 15 },
      { position: 4, tokenNumber: 'SC202601310042', triageScore: 3, status: 'Waiting', estimatedWait: 30 },
      { position: 5, tokenNumber: 'SC202601310056', triageScore: 3, status: 'Waiting', estimatedWait: 45 },
      { position: 6, tokenNumber: 'SC202601310067', triageScore: 2, status: 'Waiting', estimatedWait: 60 },
      { position: 7, tokenNumber: 'SC202601310078', triageScore: 2, status: 'Waiting', estimatedWait: 75 },
    ]
    
    setTimeout(() => {
      setQueue(mockQueue)
      setIsLoading(false)
    }, 1000)
  }, [])

  const getSeverityBadge = (score: number) => {
    const styles = {
      5: 'bg-red-100 text-red-800 border-red-300',
      4: 'bg-orange-100 text-orange-800 border-orange-300',
      3: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      2: 'bg-green-100 text-green-800 border-green-300',
      1: 'bg-blue-100 text-blue-800 border-blue-300',
    }
    const labels = { 5: 'Critical', 4: 'Urgent', 3: 'Moderate', 2: 'Low', 1: 'Minimal' }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${styles[score as keyof typeof styles]}`}>
        {labels[score as keyof typeof labels]}
      </span>
    )
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      'In Consultation': 'bg-purple-100 text-purple-800',
      'Called': 'bg-green-100 text-green-800',
      'Waiting': 'bg-gray-100 text-gray-800',
    }
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status]}`}>
        {status}
      </span>
    )
  }

  const filteredQueue = searchToken 
    ? queue.filter(q => q.tokenNumber.includes(searchToken.toUpperCase()))
    : queue

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Queue Status</h1>
          <p className="text-gray-600">Real-time patient queue updates</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="card text-center">
            <Users className="h-8 w-8 text-healthcare-blue mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">{queue.length}</p>
            <p className="text-sm text-gray-600">In Queue</p>
          </div>
          <div className="card text-center">
            <Clock className="h-8 w-8 text-healthcare-green mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">~12 min</p>
            <p className="text-sm text-gray-600">Avg Wait Time</p>
          </div>
          <div className="card text-center">
            <RefreshCw className="h-8 w-8 text-healthcare-accent mx-auto mb-2" />
            <p className="text-2xl font-bold text-gray-900">4</p>
            <p className="text-sm text-gray-600">Doctors Available</p>
          </div>
        </div>

        {/* Search */}
        <div className="card mb-6">
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder="Search by token number (e.g., SC202601310042)"
              value={searchToken}
              onChange={(e) => setSearchToken(e.target.value)}
              className="input-field flex-1"
            />
            <button className="btn-primary">Search</button>
          </div>
        </div>

        {/* Queue List */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Current Queue</h2>
          
          {isLoading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 text-gray-400 animate-spin mx-auto mb-2" />
              <p className="text-gray-500">Loading queue...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">#</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Token</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Severity</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Est. Wait</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQueue.map((entry) => (
                    <tr 
                      key={entry.tokenNumber} 
                      className={`border-b border-gray-100 hover:bg-gray-50 
                        ${entry.tokenNumber === 'SC202601310042' ? 'bg-blue-50' : ''}`}
                    >
                      <td className="py-4 px-4">
                        <span className="font-semibold text-gray-900">{entry.position}</span>
                      </td>
                      <td className="py-4 px-4">
                        <span className="font-mono text-sm">{entry.tokenNumber}</span>
                      </td>
                      <td className="py-4 px-4">
                        {getSeverityBadge(entry.triageScore)}
                      </td>
                      <td className="py-4 px-4">
                        {getStatusBadge(entry.status)}
                      </td>
                      <td className="py-4 px-4 text-gray-600">
                        {entry.estimatedWait === 0 ? 'Now' : `~${entry.estimatedWait} min`}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <p className="text-center text-sm text-gray-500 mt-4">
          Queue updates automatically every 30 seconds
        </p>
      </div>
    </div>
  )
}
