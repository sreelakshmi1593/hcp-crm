import { configureStore, createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import axios from 'axios'

const API = '/api'

// ── Async Thunks ──────────────────────────────────────────────

export const fetchHCPs = createAsyncThunk('hcps/fetchAll', async (search = '') => {
  const res = await axios.get(`${API}/hcps${search ? `?search=${search}` : ''}`)
  return res.data
})

export const fetchInteractions = createAsyncThunk('interactions/fetchAll', async (hcpId) => {
  const url = hcpId ? `${API}/interactions?hcp_id=${hcpId}` : `${API}/interactions`
  const res = await axios.get(url)
  return res.data
})

export const createInteraction = createAsyncThunk('interactions/create', async (data) => {
  const res = await axios.post(`${API}/interactions`, data)
  return res.data
})

export const updateInteraction = createAsyncThunk('interactions/update', async ({ id, data }) => {
  const res = await axios.put(`${API}/interactions/${id}`, data)
  return res.data
})

export const deleteInteraction = createAsyncThunk('interactions/delete', async (id) => {
  await axios.delete(`${API}/interactions/${id}`)
  return id
})

export const sendAgentMessage = createAsyncThunk('agent/send', async (message) => {
  const res = await axios.post(`${API}/agent/chat`, { message })
  return res.data
})

// ── HCP Slice ─────────────────────────────────────────────────

const hcpSlice = createSlice({
  name: 'hcps',
  initialState: { list: [], loading: false, error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (s) => { s.loading = true; s.error = null })
      .addCase(fetchHCPs.fulfilled, (s, a) => { s.loading = false; s.list = a.payload })
      .addCase(fetchHCPs.rejected, (s, a) => { s.loading = false; s.error = a.error.message })
  }
})

// ── Interactions Slice ────────────────────────────────────────

const interactionsSlice = createSlice({
  name: 'interactions',
  initialState: { list: [], loading: false, error: null, lastSaved: null },
  reducers: {
    clearLastSaved(s) { s.lastSaved = null }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchInteractions.pending, (s) => { s.loading = true })
      .addCase(fetchInteractions.fulfilled, (s, a) => { s.loading = false; s.list = a.payload })
      .addCase(createInteraction.fulfilled, (s, a) => {
        s.list.unshift(a.payload)
        s.lastSaved = a.payload
      })
      .addCase(updateInteraction.fulfilled, (s, a) => {
        const idx = s.list.findIndex(i => i.id === a.payload.id)
        if (idx !== -1) s.list[idx] = a.payload
        s.lastSaved = a.payload
      })
      .addCase(deleteInteraction.fulfilled, (s, a) => {
        s.list = s.list.filter(i => i.id !== a.payload)
      })
  }
})

// ── Agent Slice ────────────────────────────────────────────────

const agentSlice = createSlice({
  name: 'agent',
  initialState: {
    chatHistory: [],
    loading: false,
    error: null,
    lastToolsUsed: []
  },
  reducers: {
    addUserMessage(s, a) {
      s.chatHistory.push({ role: 'user', content: a.payload, ts: Date.now() })
    },
    clearChat(s) {
      s.chatHistory = []
      s.lastToolsUsed = []
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendAgentMessage.pending, (s) => { s.loading = true; s.error = null })
      .addCase(sendAgentMessage.fulfilled, (s, a) => {
        s.loading = false
        s.chatHistory.push({ role: 'assistant', content: a.payload.message, ts: Date.now() })
        s.lastToolsUsed = a.payload.result?.tools_used || []
      })
      .addCase(sendAgentMessage.rejected, (s, a) => {
        s.loading = false
        s.error = a.error.message
        s.chatHistory.push({ role: 'assistant', content: 'Sorry, I encountered an error. Please try again.', ts: Date.now() })
      })
  }
})

export const { clearLastSaved } = interactionsSlice.actions
export const { addUserMessage, clearChat } = agentSlice.actions

export const store = configureStore({
  reducer: {
    hcps: hcpSlice.reducer,
    interactions: interactionsSlice.reducer,
    agent: agentSlice.reducer,
  }
})
