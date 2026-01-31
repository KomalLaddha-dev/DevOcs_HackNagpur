import { Link, useNavigate } from 'react-router-dom'
import { Activity, Menu, X, User, LogOut } from 'lucide-react'
import { useState } from 'react'
import { useSelector, useDispatch } from 'react-redux'
import { RootState } from '../../store'
import { logout } from '../../store/slices/authSlice'

export default function Navbar() {
  const [isOpen, setIsOpen] = useState(false)
  const navigate = useNavigate()
  const dispatch = useDispatch()
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)

  const handleLogout = () => {
    dispatch(logout())
    navigate('/login')
  }

  return (
    <nav className="bg-white shadow-sm border-b border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <Activity className="h-8 w-8 text-healthcare-blue" />
              <span className="text-xl font-bold text-gray-900">SmartCare</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link to="/" className="text-gray-600 hover:text-healthcare-blue transition-colors">
              Home
            </Link>
            <Link to="/checkin" className="text-gray-600 hover:text-healthcare-blue transition-colors">
              Check-In
            </Link>
            <Link to="/queue" className="text-gray-600 hover:text-healthcare-blue transition-colors">
              Queue Status
            </Link>
            {isAuthenticated ? (
              <div className="flex items-center space-x-4">
                {user?.role === 'doctor' && (
                  <Link to="/doctor" className="text-gray-600 hover:text-healthcare-blue transition-colors">
                    Dashboard
                  </Link>
                )}
                {user?.role === 'admin' && (
                  <Link to="/admin" className="text-gray-600 hover:text-healthcare-blue transition-colors">
                    Admin
                  </Link>
                )}
                <div className="flex items-center space-x-2 text-gray-600">
                  <User className="h-4 w-4" />
                  <span className="text-sm">{user?.email}</span>
                </div>
                <button 
                  onClick={handleLogout}
                  className="btn-secondary flex items-center space-x-2"
                >
                  <LogOut className="h-4 w-4" />
                  <span>Logout</span>
                </button>
              </div>
            ) : (
              <Link to="/login" className="btn-primary flex items-center space-x-2">
                <User className="h-4 w-4" />
                <span>Login</span>
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="text-gray-600 hover:text-gray-900"
            >
              {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <div className="md:hidden pb-4">
            <div className="flex flex-col space-y-4">
              <Link to="/" className="text-gray-600 hover:text-healthcare-blue">Home</Link>
              <Link to="/checkin" className="text-gray-600 hover:text-healthcare-blue">Check-In</Link>
              <Link to="/queue" className="text-gray-600 hover:text-healthcare-blue">Queue Status</Link>
              {isAuthenticated ? (
                <>
                  {user?.role === 'doctor' && (
                    <Link to="/doctor" className="text-gray-600 hover:text-healthcare-blue">Dashboard</Link>
                  )}
                  {user?.role === 'admin' && (
                    <Link to="/admin" className="text-gray-600 hover:text-healthcare-blue">Admin</Link>
                  )}
                  <div className="text-gray-600 text-sm">{user?.email}</div>
                  <button onClick={handleLogout} className="btn-secondary text-center">Logout</button>
                </>
              ) : (
                <Link to="/login" className="btn-primary text-center">Login</Link>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
