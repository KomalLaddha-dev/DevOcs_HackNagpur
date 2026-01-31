import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
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
        <Route path="checkin" element={<CheckInPage />} />
        <Route path="queue" element={<QueuePage />} />
        <Route path="doctor" element={<DoctorDashboard />} />
        <Route path="admin" element={<AdminDashboard />} />
      </Route>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
    </Routes>
  )
}

export default App
