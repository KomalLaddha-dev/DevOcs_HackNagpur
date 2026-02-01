import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { 
  User, 
  FileText, 
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Loader2,
  Video,
  Clock
} from 'lucide-react'
import api from '../services/api'

interface CheckInFormData {
  fullName: string
  phone: string
  dateOfBirth: string
  symptoms: string[]
  description: string
  duration: string
  selfSeverity: number
  chronicConditions: string[]
  department: string
}

const COMMON_SYMPTOMS = [
  'Fever', 'Headache', 'Cough', 'Sore Throat', 'Body Pain',
  'Nausea', 'Fatigue', 'Chest Pain', 'Difficulty Breathing',
  'Abdominal Pain', 'Dizziness', 'Rash', 'High Fever', 'Vomiting'
]

const CHRONIC_CONDITIONS = [
  'Diabetes', 'Hypertension', 'Heart Disease', 'Asthma', 
  'COPD', 'Kidney Disease', 'Cancer', 'None'
]

const DEPARTMENTS = [
  { value: 'general', label: '🏥 General Medicine' },
  { value: 'emergency', label: '🚑 Emergency' },
  { value: 'pediatrics', label: '👶 Pediatrics' },
  { value: 'cardiology', label: '❤️ Cardiology' },
  { value: 'neurology', label: '🧠 Neurology' },
  { value: 'orthopedics', label: '🦴 Orthopedics' },
]

const DURATION_MAP: Record<string, number> = {
  'just_now': 0,
  'hours': 2,
  'today': 12,
  'days': 48,
  'week': 168,
  'longer': 200
}

export default function CheckInPage() {
  const [step, setStep] = useState(1)
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])
  const [selectedDepartment, setSelectedDepartment] = useState('general')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [triageResult, setTriageResult] = useState<any>(null)
  const [error, setError] = useState('')

  const { register, handleSubmit, watch, formState: { errors } } = useForm<CheckInFormData>()

  const toggleSymptom = (symptom: string) => {
    setSelectedSymptoms(prev => 
      prev.includes(symptom) 
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    )
  }

  const toggleCondition = (condition: string) => {
    if (condition === 'None') {
      setSelectedConditions([])
    } else {
      setSelectedConditions(prev => 
        prev.includes(condition) 
          ? prev.filter(c => c !== condition)
          : [...prev.filter(c => c !== 'None'), condition]
      )
    }
  }

  const calculateAge = (dob: string): number => {
    const today = new Date()
    const birth = new Date(dob)
    let age = today.getFullYear() - birth.getFullYear()
    const m = today.getMonth() - birth.getMonth()
    if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--
    return age
  }

  const onSubmit = async (data: CheckInFormData) => {
    setIsSubmitting(true)
    setError('')
    
    try {
      const age = calculateAge(data.dateOfBirth)
      const durationHours = DURATION_MAP[data.duration] || 0
      
      // Call the SmartQueue API
      const response = await api.post('/smartqueue/checkin', {
        patient_id: Date.now(), // Generate unique ID for demo
        patient_name: data.fullName,
        symptoms: selectedSymptoms.map(s => s.toLowerCase().replace(/ /g, '_')),
        description: data.description,
        age: age,
        chronic_conditions: selectedConditions.filter(c => c !== 'None').map(c => c.toLowerCase().replace(/ /g, '_')),
        duration_hours: durationHours,
        self_severity: parseInt(String(data.selfSeverity)) || 5,
        department: selectedDepartment
      })

      if (response.data.success) {
        setTriageResult({
          tokenNumber: response.data.token,
          entryId: response.data.entry_id,
          triageScore: response.data.triage.triage_score,
          triageScore10: response.data.triage_score_10 || response.data.triage.triage_score,  // Already 1-10 scale
          severityLevel: response.data.triage.severity_level,
          severityColor: response.data.triage.severity_color,
          estimatedWait: response.data.wait_estimate.estimated_minutes,
          waitRange: `${response.data.wait_estimate.range_min}-${response.data.wait_estimate.range_max}`,
          queuePosition: response.data.position,
          priorityScore: response.data.priority_score,
          recommendation: response.data.triage.recommended_action,
          explanation: response.data.triage.explanation,
          teleconsultEligible: response.data.teleconsult.eligible,
          teleconsultRecommended: response.data.teleconsult.recommended,
          teleconsultReason: response.data.teleconsult.reason,
          teleconsultBenefits: response.data.teleconsult.benefits || [],
          department: response.data.department,
          waitTimeProtection: response.data.wait_time_protection,
          aiActionsCount: response.data.ai_actions_taken || 0
        })
        setStep(3)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Check-in failed. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSeverityColor = (score: number) => {
    // Now handles 1-10 scale
    if (score >= 9) return 'text-red-600 bg-red-100 border-red-300'
    if (score >= 7) return 'text-orange-600 bg-orange-100 border-orange-300'
    if (score >= 5) return 'text-yellow-600 bg-yellow-100 border-yellow-300'
    if (score >= 3) return 'text-blue-600 bg-blue-100 border-blue-300'
    return 'text-green-600 bg-green-100 border-green-300'
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center space-x-4">
            {[1, 2, 3].map((s) => (
              <div key={s} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold
                  ${step >= s ? 'bg-healthcare-blue text-white' : 'bg-gray-200 text-gray-500'}`}>
                  {step > s ? <CheckCircle className="h-5 w-5" /> : s}
                </div>
                {s < 3 && (
                  <div className={`w-20 h-1 mx-2 ${step > s ? 'bg-healthcare-blue' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>
          <div className="flex justify-center space-x-12 mt-2 text-sm text-gray-600">
            <span>Personal Info</span>
            <span>Symptoms</span>
            <span>Result</span>
          </div>
        </div>

        <div className="card">
          {step === 1 && (
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <User className="h-6 w-6 text-healthcare-blue" />
                <h2 className="text-2xl font-bold text-gray-900">Personal Information</h2>
              </div>
              
              <form onSubmit={(e) => { e.preventDefault(); setStep(2); }} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                  <input
                    {...register('fullName', { required: true })}
                    className="input-field"
                    placeholder="Enter your full name"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                  <input
                    {...register('phone', { required: true })}
                    className="input-field"
                    placeholder="+91 XXXXX XXXXX"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Date of Birth</label>
                  <input
                    type="date"
                    {...register('dateOfBirth', { required: true })}
                    className="input-field"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Select Department</label>
                  <div className="grid grid-cols-2 gap-2">
                    {DEPARTMENTS.map((dept) => (
                      <button
                        key={dept.value}
                        type="button"
                        onClick={() => setSelectedDepartment(dept.value)}
                        className={`p-3 rounded-lg text-left font-medium transition-all border-2
                          ${selectedDepartment === dept.value
                            ? 'bg-healthcare-blue text-white border-healthcare-blue'
                            : 'bg-gray-50 text-gray-700 border-gray-200 hover:border-healthcare-blue hover:bg-blue-50'
                          }`}
                      >
                        {dept.label}
                      </button>
                    ))}
                  </div>
                </div>

                <button type="submit" className="btn-primary w-full flex items-center justify-center">
                  Continue
                  <ArrowRight className="ml-2 h-5 w-5" />
                </button>
              </form>
            </div>
          )}

          {step === 2 && (
            <div>
              <div className="flex items-center space-x-3 mb-6">
                <FileText className="h-6 w-6 text-healthcare-blue" />
                <h2 className="text-2xl font-bold text-gray-900">Describe Your Symptoms</h2>
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Select your symptoms (click all that apply)
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {COMMON_SYMPTOMS.map((symptom) => (
                      <button
                        key={symptom}
                        type="button"
                        onClick={() => toggleSymptom(symptom)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                          ${selectedSymptoms.includes(symptom)
                            ? symptom.includes('Chest') || symptom.includes('Breathing') 
                              ? 'bg-red-600 text-white'
                              : 'bg-healthcare-blue text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                      >
                        {symptom}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Do you have any chronic conditions?
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {CHRONIC_CONDITIONS.map((condition) => (
                      <button
                        key={condition}
                        type="button"
                        onClick={() => toggleCondition(condition)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-colors
                          ${selectedConditions.includes(condition) || (condition === 'None' && selectedConditions.length === 0)
                            ? 'bg-purple-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                      >
                        {condition}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Describe your symptoms in detail
                  </label>
                  <textarea
                    {...register('description', { required: true })}
                    className="input-field h-32"
                    placeholder="Please describe how you're feeling, when symptoms started, etc."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    How long have you had these symptoms?
                  </label>
                  <select {...register('duration')} className="input-field">
                    <option value="">Select duration</option>
                    <option value="just_now">Just now / Few minutes</option>
                    <option value="hours">Few hours</option>
                    <option value="today">Since today</option>
                    <option value="days">Few days</option>
                    <option value="week">About a week</option>
                    <option value="longer">More than a week</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    How severe do you feel your condition is? (1-10)
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="10"
                    defaultValue="5"
                    {...register('selfSeverity')}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>1 - Mild</span>
                    <span>2</span>
                    <span>3</span>
                    <span>4</span>
                    <span>5 - Moderate</span>
                    <span>6</span>
                    <span>7</span>
                    <span>8</span>
                    <span>9</span>
                    <span>10 - Severe</span>
                  </div>
                </div>

                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => setStep(1)}
                    className="flex-1 px-6 py-3 border border-gray-300 rounded-lg font-semibold text-gray-700 hover:bg-gray-50"
                  >
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting || selectedSymptoms.length === 0}
                    className="flex-1 btn-primary flex items-center justify-center disabled:opacity-50"
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="animate-spin mr-2 h-5 w-5" />
                        Analyzing...
                      </>
                    ) : (
                      <>
                        Submit for Triage
                        <ArrowRight className="ml-2 h-5 w-5" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {step === 3 && triageResult && (
            <div className="text-center">
              <div className={`w-24 h-24 rounded-full flex items-center justify-center mx-auto mb-4 border-4 ${getSeverityColor(triageResult.triageScore10 || triageResult.triageScore * 2)}`}>
                <div>
                  <span className="text-3xl font-bold">{triageResult.triageScore10 || triageResult.triageScore * 2}</span>
                  <span className="text-sm">/10</span>
                </div>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Check-In Complete!</h2>
              <p className="text-gray-600 mb-2">{triageResult.severityLevel} Priority</p>
              <p className="text-sm text-healthcare-blue font-medium mb-4 capitalize">
                📍 Department: {triageResult.department}
              </p>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-600">Your Token Number</p>
                <p className="text-3xl font-bold text-healthcare-blue">{triageResult.tokenNumber}</p>
              </div>

              {/* AI Actions Notice */}
              {triageResult.aiActionsCount > 0 && (
                <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-4 text-left">
                  <div className="flex items-center mb-2">
                    <span className="text-xl mr-2">🤖</span>
                    <h3 className="font-semibold text-purple-900">AI Auto-Allocated {triageResult.aiActionsCount} Doctor(s)</h3>
                  </div>
                  <p className="text-sm text-purple-700">
                    Our AI system automatically assigned spare doctors to manage the queue efficiently.
                  </p>
                </div>
              )}

              {/* Wait Time Protection Notice */}
              {triageResult.waitTimeProtection && triageResult.waitTimeProtection.doctors_assigned > 0 && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 text-left">
                  <div className="flex items-center mb-2">
                    <span className="text-xl mr-2">🛡️</span>
                    <h3 className="font-semibold text-green-900">Wait Time Protection Active!</h3>
                  </div>
                  <p className="text-sm text-green-700 mb-2">
                    Because you're a high-priority patient, we've assigned {triageResult.waitTimeProtection.doctors_assigned} additional doctor(s) 
                    to ensure other patients' wait times aren't affected.
                  </p>
                  <p className="text-xs text-green-600">
                    This helps maintain fair wait times for everyone.
                  </p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Queue Position</p>
                  <p className="text-2xl font-semibold text-healthcare-blue">#{triageResult.queuePosition}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Severity Score</p>
                  <p className="text-2xl font-semibold">{triageResult.triageScore10 || triageResult.triageScore * 2}/10</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 col-span-2">
                  <Clock className="h-5 w-5 text-gray-400 mx-auto mb-1" />
                  <p className="text-sm text-gray-600">Estimated Wait Time</p>
                  <p className="text-xl font-semibold">
                    {triageResult.estimatedWait === 0 ? 'Immediate' : `${triageResult.waitRange} minutes`}
                  </p>
                </div>
              </div>

              {/* Triage Explanation */}
              {triageResult.explanation && triageResult.explanation.length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4 mb-6 text-left">
                  <h3 className="font-semibold text-blue-900 mb-2">How your priority was calculated:</h3>
                  <ul className="text-sm text-blue-800 space-y-1">
                    {triageResult.explanation.map((exp: string, i: number) => (
                      <li key={i} className="flex items-start">
                        <CheckCircle className="h-4 w-4 mr-2 mt-0.5 flex-shrink-0" />
                        {exp}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Teleconsult Option */}
              {triageResult.teleconsultEligible && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 text-left">
                  <div className="flex items-center mb-2">
                    <Video className="h-5 w-5 text-green-600 mr-2" />
                    <h3 className="font-semibold text-green-900">Teleconsultation Available!</h3>
                  </div>
                  <p className="text-sm text-green-700 mb-3">{triageResult.teleconsultReason}</p>
                  {triageResult.teleconsultBenefits.length > 0 && (
                    <ul className="text-sm text-green-600 space-y-1 mb-3">
                      {triageResult.teleconsultBenefits.map((b: string, i: number) => (
                        <li key={i}>✓ {b}</li>
                      ))}
                    </ul>
                  )}
                  <button className="w-full bg-green-600 text-white py-2 rounded-lg font-semibold hover:bg-green-700 transition-colors">
                    Switch to Teleconsultation
                  </button>
                </div>
              )}

              <div className={`p-4 rounded-lg mb-6 ${triageResult.triageScore >= 4 ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
                <div className="flex items-start space-x-2">
                  <AlertCircle className={`h-5 w-5 mt-0.5 ${triageResult.triageScore >= 4 ? 'text-red-500' : 'text-blue-500'}`} />
                  <p className={`text-sm ${triageResult.triageScore >= 4 ? 'text-red-700' : 'text-blue-700'}`}>
                    {triageResult.recommendation}
                  </p>
                </div>
              </div>

              <a href="/queue" className="btn-primary inline-flex items-center">
                Track Your Queue Status
                <ArrowRight className="ml-2 h-5 w-5" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
