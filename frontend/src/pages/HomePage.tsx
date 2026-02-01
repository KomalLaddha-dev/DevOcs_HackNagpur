import { Link } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { RootState } from '../store'
import { 
  Activity, 
  Clock, 
  Users, 
  Brain, 
  Video, 
  BarChart3,
  ArrowRight,
  LogIn
} from 'lucide-react'

export default function HomePage() {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth)
  const features = [
    {
      icon: Brain,
      title: 'AI-Powered Triage',
      description: 'Intelligent symptom analysis for accurate severity assessment',
    },
    {
      icon: Clock,
      title: 'Reduced Wait Times',
      description: 'Priority-based queuing reduces average wait by 40%',
    },
    {
      icon: Users,
      title: 'Smart Scheduling',
      description: 'Optimal doctor-patient matching for efficient care',
    },
    {
      icon: Video,
      title: 'Tele-consultation',
      description: 'Low-risk cases redirected to virtual consultations',
    },
    {
      icon: Activity,
      title: 'Real-time Updates',
      description: 'Live queue status and wait time estimates',
    },
    {
      icon: BarChart3,
      title: 'Analytics Dashboard',
      description: 'Comprehensive insights for healthcare administrators',
    },
  ]

  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-healthcare-blue to-healthcare-green text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-4xl md:text-5xl font-bold mb-6">
                Smart Healthcare Queue Management
              </h1>
              <p className="text-xl text-blue-100 mb-8">
                Revolutionize patient care with AI-powered triage and intelligent scheduling. 
                Reduce wait times, improve outcomes, and enhance the healthcare experience.
              </p>
              <div className="flex flex-col sm:flex-row gap-4">
                {isAuthenticated ? (
                  <Link to="/checkin" className="bg-white text-healthcare-blue px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition-colors inline-flex items-center justify-center">
                    Start Check-In
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                ) : (
                  <Link to="/login" className="bg-white text-healthcare-blue px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition-colors inline-flex items-center justify-center">
                    Login to Check-In
                    <LogIn className="ml-2 h-5 w-5" />
                  </Link>
                )}
                <Link to="/queue" className="border-2 border-white text-white px-8 py-4 rounded-lg font-semibold hover:bg-white/10 transition-colors inline-flex items-center justify-center">
                  View Queue Status
                </Link>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8">
                <div className="space-y-4">
                  <div className="flex items-center space-x-4 bg-white/10 rounded-lg p-4">
                    <div className="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center">
                      <span className="font-bold">5</span>
                    </div>
                    <div>
                      <p className="font-semibold">Critical Patient</p>
                      <p className="text-sm text-blue-100">Immediate attention</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 bg-white/10 rounded-lg p-4">
                    <div className="w-12 h-12 bg-orange-500 rounded-full flex items-center justify-center">
                      <span className="font-bold">4</span>
                    </div>
                    <div>
                      <p className="font-semibold">Urgent Care</p>
                      <p className="text-sm text-blue-100">~15 min wait</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4 bg-white/10 rounded-lg p-4">
                    <div className="w-12 h-12 bg-yellow-500 rounded-full flex items-center justify-center">
                      <span className="font-bold">3</span>
                    </div>
                    <div>
                      <p className="font-semibold">Standard Queue</p>
                      <p className="text-sm text-blue-100">~45 min wait</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Transforming Healthcare Delivery
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Our AI-powered system optimizes every step of the patient journey
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="card hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-healthcare-light rounded-lg flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-healthcare-blue" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How SmartCare Works
            </h2>
          </div>

          <div className="grid md:grid-cols-4 gap-8">
            {[
              { step: 1, title: 'Check In', desc: 'Register your symptoms digitally' },
              { step: 2, title: 'AI Triage', desc: 'Get instant severity assessment' },
              { step: 3, title: 'Smart Queue', desc: 'Priority-based positioning' },
              { step: 4, title: 'See Doctor', desc: 'Optimal doctor assignment' },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-16 h-16 bg-healthcare-blue text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-healthcare-blue py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Experience Smarter Healthcare?
          </h2>
          <p className="text-blue-100 mb-8">
            Join thousands of patients who enjoy reduced wait times and better care.
          </p>
          {isAuthenticated ? (
            <Link to="/checkin" className="bg-white text-healthcare-blue px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition-colors inline-flex items-center">
              Start Your Check-In Now
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          ) : (
            <Link to="/login" className="bg-white text-healthcare-blue px-8 py-4 rounded-lg font-semibold hover:bg-blue-50 transition-colors inline-flex items-center">
              Login to Get Started
              <LogIn className="ml-2 h-5 w-5" />
            </Link>
          )}
        </div>
      </section>
    </div>
  )
}
