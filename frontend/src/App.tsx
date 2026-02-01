import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/HomePage'
import CheckInPage from './pages/CheckInPage'
import QueuePage from './pages/QueuePage'
import DoctorDashboard from './pages/DoctorDashboard'
import AdminDashboard from './pages/AdminDashboard'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        {/* Check-in requires authentication (any role can check-in) */}
        <Route 
          path="checkin" 
          element={
            <ProtectedRoute requireAuth={true}>
              <CheckInPage />
            </ProtectedRoute>
          } 
        />
        {/* Queue status is public */}
        <Route path="queue" element={<QueuePage />} />
        {/* Doctor dashboard - only doctors can access */}
        <Route 
          path="doctor" 
          element={
            <ProtectedRoute allowedRoles={['doctor', 'admin']}>
              <DoctorDashboard />
            </ProtectedRoute>
          } 
        />
        {/* Admin dashboard - only admins can access */}
        <Route 
          path="admin" 
          element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } 
        />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App
