import { createSlice, PayloadAction } from '@reduxjs/toolkit'

interface QueueEntry {
  id: number
  patientId: number
  tokenNumber: string
  triageScore: number
  priorityScore: number
  status: string
  position: number
  estimatedWait: number
}

interface QueueState {
  entries: QueueEntry[]
  userEntry: QueueEntry | null
  isLoading: boolean
  lastUpdated: string | null
}

const initialState: QueueState = {
  entries: [],
  userEntry: null,
  isLoading: false,
  lastUpdated: null,
}

const queueSlice = createSlice({
  name: 'queue',
  initialState,
  reducers: {
    setQueue: (state, action: PayloadAction<QueueEntry[]>) => {
      state.entries = action.payload
      state.lastUpdated = new Date().toISOString()
    },
    setUserEntry: (state, action: PayloadAction<QueueEntry | null>) => {
      state.userEntry = action.payload
    },
    updateEntry: (state, action: PayloadAction<QueueEntry>) => {
      const index = state.entries.findIndex(e => e.id === action.payload.id)
      if (index !== -1) {
        state.entries[index] = action.payload
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const { setQueue, setUserEntry, updateEntry, setLoading } = queueSlice.actions
export default queueSlice.reducer
