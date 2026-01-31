import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { 
  User, 
  FileText, 
  AlertCircle,
  CheckCircle,
  ArrowRight,
  Loader2
} from 'lucide-react'

interface CheckInFormData {
  fullName: string
  phone: string
  dateOfBirth: string
  symptoms: string[]
  description: string
  duration: string
  selfSeverity: number
}

const COMMON_SYMPTOMS = [
  'Fever', 'Headache', 'Cough', 'Sore Throat', 'Body Pain',
  'Nausea', 'Fatigue', 'Chest Pain', 'Difficulty Breathing',
  'Abdominal Pain', 'Dizziness', 'Rash'
]

export default function CheckInPage() {
  const [step, setStep] = useState(1)
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [triageResult, setTriageResult] = useState<any>(null)

  const { register, handleSubmit, formState: { errors } } = useForm<CheckInFormData>()

  const toggleSymptom = (symptom: string) => {
    setSelectedSymptoms(prev => 
      prev.includes(symptom) 
        ? prev.filter(s => s !== symptom)
        : [...prev, symptom]
    )
  }

  const onSubmit = async (data: CheckInFormData) => {
    setIsSubmitting(true)
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // Mock triage result
    setTriageResult({
      tokenNumber: 'SC202601310042',
      triageScore: selectedSymptoms.includes('Chest Pain') ? 5 : 3,
      severityLevel: selectedSymptoms.includes('Chest Pain') ? 'Critical' : 'Moderate',
      estimatedWait: selectedSymptoms.includes('Chest Pain') ? 0 : 45,
      queuePosition: selectedSymptoms.includes('Chest Pain') ? 1 : 12,
      recommendation: selectedSymptoms.includes('Chest Pain') 
        ? 'Proceed to Emergency Room immediately'
        : 'Please wait in the standard queue. You will be called shortly.'
    })
    
    setIsSubmitting(false)
    setStep(3)
  }

  const getSeverityColor = (score: number) => {
    if (score >= 5) return 'text-red-600 bg-red-100'
    if (score >= 4) return 'text-orange-600 bg-orange-100'
    if (score >= 3) return 'text-yellow-600 bg-yellow-100'
    return 'text-green-600 bg-green-100'
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
                            ? 'bg-healthcare-blue text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                      >
                        {symptom}
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
                    {...register('selfSeverity')}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>1 - Mild</span>
                    <span>5 - Moderate</span>
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
                    disabled={isSubmitting}
                    className="flex-1 btn-primary flex items-center justify-center"
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
              <div className={`w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4 ${getSeverityColor(triageResult.triageScore)}`}>
                <span className="text-3xl font-bold">{triageResult.triageScore}</span>
              </div>
              
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Check-In Complete!</h2>
              
              <div className="bg-gray-50 rounded-lg p-4 mb-6">
                <p className="text-sm text-gray-600">Your Token Number</p>
                <p className="text-3xl font-bold text-healthcare-blue">{triageResult.tokenNumber}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Severity Level</p>
                  <p className="text-lg font-semibold">{triageResult.severityLevel}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="text-sm text-gray-600">Queue Position</p>
                  <p className="text-lg font-semibold">#{triageResult.queuePosition}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4 col-span-2">
                  <p className="text-sm text-gray-600">Estimated Wait Time</p>
                  <p className="text-lg font-semibold">
                    {triageResult.estimatedWait === 0 ? 'Immediate' : `~${triageResult.estimatedWait} minutes`}
                  </p>
                </div>
              </div>

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
