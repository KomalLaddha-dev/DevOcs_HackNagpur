import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import api from '../services/api'
import { setCredentials } from '../store/slices/authSlice'

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const dispatch = useDispatch()
  const [formData, setFormData] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const successMessage = location.state?.message

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Login endpoint expects form data (x-www-form-urlencoded)
      const params = new URLSearchParams()
      params.append('username', formData.email)
      params.append('password', formData.password)

      const response = await api.post('/auth/login', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })

      // Decode JWT to get user info (payload is in second part)
      const tokenParts = response.data.access_token.split('.')
      const payload = JSON.parse(atob(tokenParts[1]))
      
      const user = {
        id: parseInt(payload.sub),
        email: formData.email,
        full_name: formData.email.split('@')[0], // Will be updated from API
        role: payload.role
      }

      // Update Redux store (this also saves to localStorage)
      dispatch(setCredentials({ 
        user, 
        token: response.data.access_token 
      }))
      localStorage.setItem('refresh_token', response.data.refresh_token)
      
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="card max-w-md w-full mx-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-6 text-center">Login to SmartCare</h1>
        
        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-4">
            {successMessage}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input 
              type="email" 
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input-field" 
              placeholder="your@email.com"
              required 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input 
              type="password" 
              name="password"
              value={formData.password}
              onChange={handleChange}
              className="input-field" 
              placeholder="••••••••"
              required 
            />
          </div>
          <button 
            type="submit" 
            className="btn-primary w-full disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600 mt-4">
          Don't have an account? <a href="/register" className="text-healthcare-blue hover:underline">Register</a>
        </p>
      </div>
    </div>
  )
}
