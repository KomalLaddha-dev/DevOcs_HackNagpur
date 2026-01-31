import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import queueReducer from './slices/queueSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    queue: queueReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
