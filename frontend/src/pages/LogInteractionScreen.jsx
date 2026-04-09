import { useState, useEffect, useRef } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  fetchHCPs, fetchInteractions, createInteraction,
  updateInteraction, sendAgentMessage, addUserMessage, clearChat
} from '../store'

const INTERACTION_TYPES = ['Meeting', 'Call', 'Email', 'Conference', 'Other']
const SENTIMENTS = ['Positive', 'Neutral', 'Negative']

const emptyForm = {
  hcp_id: '',
  interaction_type: 'Meeting',
  date: new Date().toISOString().split('T')[0],
  time: new Date().toTimeString().slice(0, 5),
  attendees: '',
  topics_discussed: '',
  materials_shared: '',
  samples_distributed: '',
  sentiment: 'Neutral',
  outcomes: '',
  follow_up_actions: '',
}

export default function LogInteractionScreen() {
  const dispatch = useDispatch()
  const { list: hcps } = useSelector(s => s.hcps)
  const { list: interactions, lastSaved } = useSelector(s => s.interactions)
  const { chatHistory, loading: agentLoading, lastToolsUsed } = useSelector(s => s.agent)

  const [view, setView] = useState('form') // 'form' | 'chat'
  const [form, setForm] = useState(emptyForm)
  const [editId, setEditId] = useState(null)
  const [chatInput, setChatInput] = useState('')
  const [successMsg, setSuccessMsg] = useState('')
  const [hcpSearch, setHcpSearch] = useState('')
  const chatEndRef = useRef(null)

  useEffect(() => { dispatch(fetchHCPs()) }, [dispatch])
  useEffect(() => { dispatch(fetchInteractions()) }, [dispatch])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatHistory])

  useEffect(() => {
    if (lastSaved) {
      setSuccessMsg(`Interaction saved successfully (ID: ${lastSaved.id})`)
      setTimeout(() => setSuccessMsg(''), 4000)
      setForm(emptyForm)
      setEditId(null)
    }
  }, [lastSaved])

  const handleFormChange = (e) => {
    setForm(f => ({ ...f, [e.target.name]: e.target.value }))
  }

  const handleFormSubmit = (e) => {
    e.preventDefault()
    if (!form.hcp_id) return alert('Please select an HCP')
    if (editId) {
      dispatch(updateInteraction({ id: editId, data: form }))
    } else {
      dispatch(createInteraction({ ...form, hcp_id: parseInt(form.hcp_id) }))
    }
  }

  const handleEditClick = (interaction) => {
    setView('form')
    setEditId(interaction.id)
    setForm({
      hcp_id: interaction.hcp_id,
      interaction_type: interaction.interaction_type || 'Meeting',
      date: interaction.date || '',
      time: interaction.time || '',
      attendees: interaction.attendees || '',
      topics_discussed: interaction.topics_discussed || '',
      materials_shared: interaction.materials_shared || '',
      samples_distributed: interaction.samples_distributed || '',
      sentiment: interaction.sentiment || 'Neutral',
      outcomes: interaction.outcomes || '',
      follow_up_actions: interaction.follow_up_actions || '',
    })
    window.scrollTo(0, 0)
  }

  const handleCancelEdit = () => {
    setEditId(null)
    setForm(emptyForm)
  }

  const handleChatSend = () => {
    if (!chatInput.trim()) return
    dispatch(addUserMessage(chatInput))
    dispatch(sendAgentMessage(chatInput))
    setChatInput('')
  }

  const filteredHcps = hcps.filter(h =>
    h.name.toLowerCase().includes(hcpSearch.toLowerCase()) ||
    (h.speciality || '').toLowerCase().includes(hcpSearch.toLowerCase())
  )

  const sentimentColor = (s) => s === 'Positive' ? '#22c55e' : s === 'Negative' ? '#ef4444' : '#f59e0b'

  return (
    <div style={{ fontFamily: "'Inter', sans-serif", minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      {/* Header */}
      <div style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '0 32px' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 60 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <span style={{ color: '#fff', fontSize: 16 }}>⚕</span>
            </div>
            <span style={{ fontWeight: 600, fontSize: 18, color: '#1e293b' }}>HCP CRM</span>
            <span style={{ color: '#94a3b8', fontSize: 14, marginLeft: 8 }}>Log Interaction</span>
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            {['form', 'chat'].map(v => (
              <button key={v} onClick={() => setView(v)} style={{
                padding: '6px 18px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 14, fontFamily: 'Inter',
                background: view === v ? '#6366f1' : '#f1f5f9',
                color: view === v ? '#fff' : '#64748b',
                fontWeight: view === v ? 600 : 400,
                transition: 'all 0.15s'
              }}>
                {v === 'form' ? '📋 Form' : '🤖 AI Chat'}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 32px', display: 'grid', gridTemplateColumns: view === 'form' ? '1fr 340px' : '1fr 340px', gap: 24 }}>

        {/* LEFT: Form or Chat */}
        <div>
          {successMsg && (
            <div style={{ background: '#dcfce7', border: '1px solid #86efac', color: '#166534', padding: '10px 16px', borderRadius: 8, marginBottom: 16, fontSize: 14 }}>
              ✓ {successMsg}
            </div>
          )}

          {/* ── FORM VIEW ── */}
          {view === 'form' && (
            <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>
                  {editId ? `✏️ Edit Interaction #${editId}` : 'Log HCP Interaction'}
                </h2>
                {editId && (
                  <button onClick={handleCancelEdit} style={{ background: '#f1f5f9', border: 'none', borderRadius: 6, padding: '6px 14px', cursor: 'pointer', fontSize: 13, color: '#64748b' }}>
                    Cancel Edit
                  </button>
                )}
              </div>

              <form onSubmit={handleFormSubmit}>
                {/* Row 1: HCP + Type */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label style={labelStyle}>HCP Name *</label>
                    <input
                      type="text"
                      placeholder="Search HCP..."
                      value={hcpSearch}
                      onChange={e => setHcpSearch(e.target.value)}
                      style={{ ...inputStyle, marginBottom: 4 }}
                    />
                    <select name="hcp_id" value={form.hcp_id} onChange={handleFormChange} required style={inputStyle}>
                      <option value="">-- Select HCP --</option>
                      {filteredHcps.map(h => (
                        <option key={h.id} value={h.id}>{h.name} — {h.speciality}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label style={labelStyle}>Interaction Type</label>
                    <select name="interaction_type" value={form.interaction_type} onChange={handleFormChange} style={inputStyle}>
                      {INTERACTION_TYPES.map(t => <option key={t}>{t}</option>)}
                    </select>
                  </div>
                </div>

                {/* Row 2: Date + Time */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label style={labelStyle}>Date</label>
                    <input type="date" name="date" value={form.date} onChange={handleFormChange} style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Time</label>
                    <input type="time" name="time" value={form.time} onChange={handleFormChange} style={inputStyle} />
                  </div>
                </div>

                {/* Attendees */}
                <div style={{ marginBottom: 16 }}>
                  <label style={labelStyle}>Attendees</label>
                  <input type="text" name="attendees" value={form.attendees} onChange={handleFormChange} placeholder="Enter names or search..." style={inputStyle} />
                </div>

                {/* Topics */}
                <div style={{ marginBottom: 16 }}>
                  <label style={labelStyle}>Topics Discussed *</label>
                  <textarea name="topics_discussed" value={form.topics_discussed} onChange={handleFormChange} placeholder="Key discussion points..." rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
                </div>

                {/* Materials + Samples */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label style={labelStyle}>Materials Shared</label>
                    <input type="text" name="materials_shared" value={form.materials_shared} onChange={handleFormChange} placeholder="Brochure, study, etc." style={inputStyle} />
                  </div>
                  <div>
                    <label style={labelStyle}>Samples Distributed</label>
                    <input type="text" name="samples_distributed" value={form.samples_distributed} onChange={handleFormChange} placeholder="Product samples..." style={inputStyle} />
                  </div>
                </div>

                {/* Sentiment */}
                <div style={{ marginBottom: 16 }}>
                  <label style={labelStyle}>HCP Sentiment</label>
                  <div style={{ display: 'flex', gap: 12 }}>
                    {SENTIMENTS.map(s => (
                      <label key={s} style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 14 }}>
                        <input type="radio" name="sentiment" value={s} checked={form.sentiment === s} onChange={handleFormChange} />
                        <span style={{ color: sentimentColor(s), fontWeight: 500 }}>{s}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Outcomes */}
                <div style={{ marginBottom: 16 }}>
                  <label style={labelStyle}>Outcomes</label>
                  <textarea name="outcomes" value={form.outcomes} onChange={handleFormChange} placeholder="Key outcomes or agreements..." rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
                </div>

                {/* Follow-up */}
                <div style={{ marginBottom: 20 }}>
                  <label style={labelStyle}>Follow-up Actions</label>
                  <textarea name="follow_up_actions" value={form.follow_up_actions} onChange={handleFormChange} placeholder="Next steps or tasks..." rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
                </div>

                <button type="submit" style={{
                  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 8,
                  padding: '10px 28px', fontSize: 15, fontWeight: 600, cursor: 'pointer',
                  fontFamily: 'Inter', width: '100%', transition: 'background 0.15s'
                }}>
                  {editId ? '💾 Save Changes' : '📝 Log Interaction'}
                </button>
              </form>
            </div>
          )}

          {/* ── CHAT VIEW ── */}
          {view === 'chat' && (
            <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column', height: 580 }}>
              <div style={{ padding: '16px 20px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 10 }}>
                <div style={{ width: 32, height: 32, borderRadius: '50%', background: '#ede9fe', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 16 }}>🤖</div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>AI Assistant</div>
                  <div style={{ fontSize: 12, color: '#94a3b8' }}>Powered by LangGraph + Groq gemma2-9b-it</div>
                </div>
                {lastToolsUsed.length > 0 && (
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 4 }}>
                    {lastToolsUsed.map(t => (
                      <span key={t} style={{ background: '#ede9fe', color: '#6366f1', borderRadius: 4, padding: '2px 8px', fontSize: 11, fontWeight: 500 }}>{t}</span>
                    ))}
                  </div>
                )}
              </div>

              {/* Chat messages */}
              <div style={{ flex: 1, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {chatHistory.length === 0 && (
                  <div style={{ color: '#94a3b8', fontSize: 13, textAlign: 'center', marginTop: 40 }}>
                    <div style={{ fontSize: 32, marginBottom: 12 }}>💬</div>
                    <div>Try: <em>"Met Dr. Anjali today, she was positive about OncoBoost, shared brochure"</em></div>
                    <div style={{ marginTop: 8 }}>Or: <em>"Search for Dr. Ravi Kumar's profile"</em></div>
                    <div style={{ marginTop: 8 }}>Or: <em>"Suggest follow-up for HCP 1"</em></div>
                  </div>
                )}
                {chatHistory.map((msg, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      maxWidth: '80%', padding: '10px 14px', borderRadius: msg.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
                      background: msg.role === 'user' ? '#6366f1' : '#f8fafc',
                      color: msg.role === 'user' ? '#fff' : '#1e293b',
                      border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0',
                      fontSize: 14, lineHeight: 1.5, whiteSpace: 'pre-wrap'
                    }}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {agentLoading && (
                  <div style={{ display: 'flex', gap: 6, padding: '10px 14px', background: '#f8fafc', borderRadius: 12, width: 'fit-content', border: '1px solid #e2e8f0' }}>
                    {[0, 1, 2].map(i => (
                      <div key={i} style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366f1', animation: `bounce 1s ${i * 0.2}s infinite` }} />
                    ))}
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat input */}
              <div style={{ padding: 12, borderTop: '1px solid #e2e8f0', display: 'flex', gap: 8 }}>
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && handleChatSend()}
                  placeholder='Describe the interaction or ask the AI...'
                  style={{ ...inputStyle, flex: 1, marginBottom: 0 }}
                  disabled={agentLoading}
                />
                <button onClick={handleChatSend} disabled={agentLoading || !chatInput.trim()} style={{
                  background: '#6366f1', color: '#fff', border: 'none', borderRadius: 8,
                  padding: '0 18px', cursor: 'pointer', fontSize: 18, opacity: agentLoading || !chatInput.trim() ? 0.5 : 1
                }}>↑</button>
              </div>
            </div>
          )}
        </div>

        {/* RIGHT: Recent Interactions */}
        <div>
          <div style={{ background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: 20 }}>
            <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 600 }}>Recent Interactions</h3>
            {interactions.length === 0 ? (
              <p style={{ color: '#94a3b8', fontSize: 13 }}>No interactions logged yet.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {interactions.slice(0, 8).map(i => (
                  <div key={i.id} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '10px 12px', fontSize: 13 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: '#1e293b' }}>{i.hcp?.name || `HCP #${i.hcp_id}`}</span>
                      <span style={{ color: sentimentColor(i.sentiment), fontSize: 11, fontWeight: 500, background: '#f8fafc', padding: '2px 6px', borderRadius: 4 }}>
                        {i.sentiment}
                      </span>
                    </div>
                    <div style={{ color: '#64748b', marginBottom: 6 }}>{i.interaction_type} · {i.date}</div>
                    {i.topics_discussed && (
                      <div style={{ color: '#475569', fontSize: 12, lineHeight: 1.4 }}>
                        {i.topics_discussed.slice(0, 80)}{i.topics_discussed.length > 80 ? '…' : ''}
                      </div>
                    )}
                    <button onClick={() => handleEditClick(i)} style={{
                      marginTop: 8, background: 'none', border: '1px solid #e2e8f0', borderRadius: 4,
                      padding: '3px 10px', fontSize: 11, cursor: 'pointer', color: '#6366f1', fontFamily: 'Inter'
                    }}>
                      Edit
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
        @keyframes bounce { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
        input:focus, select:focus, textarea:focus { outline: 2px solid #6366f1; outline-offset: 0; }
        button:hover { opacity: 0.9; }
      `}</style>
    </div>
  )
}

const labelStyle = { display: 'block', fontSize: 13, fontWeight: 500, color: '#374151', marginBottom: 6 }
const inputStyle = {
  width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 8,
  fontSize: 14, fontFamily: 'Inter', color: '#1e293b', background: '#fff',
  boxSizing: 'border-box', marginBottom: 0
}
