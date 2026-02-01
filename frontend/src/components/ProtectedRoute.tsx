import { Navigate, useLocation } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { RootState } from '../store'

interface ProtectedRouteProps {
  children: React.ReactNode
  allowedRoles?: string[]
  requireAuth?: boolean
}

export default function ProtectedRoute({ 
  children, 
  allowedRoles = [], 
  requireAuth = true 
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useSelector((state: RootState) => state.auth)
  const location = useLocation()

  // Check if authentication is required
  if (requireAuth && !isAuthenticated) {
    // Redirect to login with return path
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // Check if user has required role (if roles are specified)
  if (allowedRoles.length > 0 && user) {
    if (!allowedRoles.includes(user.role)) {
      // User doesn't have the required role - redirect to home or unauthorized page
      return <Navigate to="/" replace />
    }
  }

  return <>{children}</>
}
