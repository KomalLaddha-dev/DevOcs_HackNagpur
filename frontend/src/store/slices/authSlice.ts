import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface User {
  id: number
  email: string
  full_name: string
  role: string
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

// Check localStorage for existing token on app load
const token = localStorage.getItem('token')
const userStr = localStorage.getItem('user')
const user = userStr ? JSON.parse(userStr) : null

const initialState: AuthState = {
  user: user,
  token: token,
  isAuthenticated: !!token,
  isLoading: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<{ user: User; token: string }>) => {
      state.user = action.payload.user
      state.token = action.payload.token
      state.isAuthenticated = true
      // Persist to localStorage
      localStorage.setItem('token', action.payload.token)
      localStorage.setItem('user', JSON.stringify(action.payload.user))
    },
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      // Clear localStorage
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const { setCredentials, logout, setLoading } = authSlice.actions
export default authSlice.reducer
