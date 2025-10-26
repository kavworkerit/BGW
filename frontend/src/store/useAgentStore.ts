import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { Agent } from '../services/agentService'

interface AgentState {
  agents: Agent[]
  currentAgent: Agent | null
  agentTypes: Array<{ type: string; name: string; description: string }>
  loading: boolean
  error: string | null
  runningTasks: Map<string, { status: string; startTime: Date }>
  logs: Array<{ timestamp: string; message: string; level: 'info' | 'error' | 'warning' }>
}

interface AgentActions {
  // Actions
  fetchAgents: (params?: { enabled_only?: boolean; agent_type?: string }) => Promise<void>
  fetchAgent: (id: string) => Promise<void>
  createAgent: (agent: Partial<Agent>) => Promise<Agent>
  updateAgent: (id: string, agent: Partial<Agent>) => Promise<Agent>
  deleteAgent: (id: string) => Promise<void>
  runAgent: (id: string) => Promise<void>
  importAgent: (file: File) => Promise<Agent>
  exportAgent: (id: string) => Promise<Blob>
  getAgentStats: (id: string, days?: number) => Promise<any>
  getAgentLogs: (id: string, limit?: number) => Promise<any[]>
  fetchAgentTypes: () => Promise<void>

  // Setters
  setAgents: (agents: Agent[]) => void
  setCurrentAgent: (agent: Agent | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setAgentTypes: (types: AgentState['agentTypes']) => void
  addTask: (agentId: string, task: { status: string; startTime: Date }) => void
  updateTask: (agentId: string, status: string) => void
  removeTask: (agentId: string) => void
  addLog: (message: string, level?: 'info' | 'error' | 'warning') => void
  clearLogs: () => void
}

export const useAgentStore = create<AgentState & AgentActions>()(
  devtools(
    (set, get) => ({
      // Initial state
      agents: [],
      currentAgent: null,
      agentTypes: [],
      loading: false,
      error: null,
      runningTasks: new Map(),
      logs: [],

      // Setters
      setAgents: (agents) => set({ agents }),
      setCurrentAgent: (agent) => set({ currentAgent: agent }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setAgentTypes: (types) => set({ agentTypes: types }),
      addTask: (agentId, task) => set((state) => {
        const newTasks = new Map(state.runningTasks)
        newTasks.set(agentId, task)
        return { runningTasks: newTasks }
      }),
      updateTask: (agentId, status) => set((state) => {
        const newTasks = new Map(state.runningTasks)
        if (newTasks.has(agentId)) {
          newTasks.set(agentId, { ...newTasks.get(agentId)!, status })
        }
        return { runningTasks: newTasks }
      }),
      removeTask: (agentId) => set((state) => {
        const newTasks = new Map(state.runningTasks)
        newTasks.delete(agentId)
        return { runningTasks: newTasks }
      }),
      addLog: (message, level = 'info') => set((state) => ({
        logs: [
          ...state.logs,
          {
            timestamp: new Date().toISOString(),
            message,
            level
          }
        ].slice(-1000) // Keep last 1000 logs
      })),
      clearLogs: () => set({ logs: [] }),

      // Actions
      fetchAgents: async (params = {}) => {
        set({ loading: true, error: null })

        try {
          const queryParams = new URLSearchParams()
          if (params.enabled_only) queryParams.append('enabled_only', 'true')
          if (params.agent_type) queryParams.append('agent_type', params.agent_type)

          const response = await fetch(`/api/agents?${queryParams}`)
          if (!response.ok) throw new Error('Failed to fetch agents')

          const agents = await response.json()
          set({ agents, loading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch agents',
            loading: false
          })
        }
      },

      fetchAgent: async (id) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch(`/api/agents/${id}`)
          if (!response.ok) throw new Error('Failed to fetch agent')

          const agent = await response.json()
          set({ currentAgent: agent, loading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch agent',
            loading: false
          })
        }
      },

      createAgent: async (agentData) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch('/api/agents', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(agentData)
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to create agent')
          }

          const agent = await response.json()
          set((state) => ({
            agents: [...state.agents, agent],
            loading: false
          }))

          get().addLog(`Agent created: ${agent.name}`, 'info')
          return agent
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create agent',
            loading: false
          })
          get().addLog(`Failed to create agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      updateAgent: async (id, agentData) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch(`/api/agents/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(agentData)
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to update agent')
          }

          const agent = await response.json()
          set((state) => ({
            agents: state.agents.map(a => a.id === id ? agent : a),
            currentAgent: state.currentAgent?.id === id ? agent : state.currentAgent,
            loading: false
          }))

          get().addLog(`Agent updated: ${agent.name}`, 'info')
          return agent
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update agent',
            loading: false
          })
          get().addLog(`Failed to update agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      deleteAgent: async (id) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch(`/api/agents/${id}`, {
            method: 'DELETE'
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to delete agent')
          }

          set((state) => ({
            agents: state.agents.filter(a => a.id !== id),
            currentAgent: state.currentAgent?.id === id ? null : state.currentAgent,
            loading: false
          }))

          get().addLog(`Agent deleted: ${id}`, 'info')
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete agent',
            loading: false
          })
          get().addLog(`Failed to delete agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      runAgent: async (id) => {
        try {
          get().addTask(id, { status: 'starting', startTime: new Date() })

          const response = await fetch(`/api/agents/${id}/run`, {
            method: 'POST'
          })

          if (!response.ok) {
            throw new Error('Failed to run agent')
          }

          const result = await response.json()
          get().updateTask(id, 'running')
          get().addLog(`Agent started: ${id} (Task: ${result.task_id})`, 'info')

          // Start polling for task status
          const pollInterval = setInterval(async () => {
            try {
              const statusResponse = await fetch(`/api/tasks/${result.task_id}`)
              if (statusResponse.ok) {
                const status = await statusResponse.json()
                if (status.state === 'SUCCESS' || status.state === 'FAILURE') {
                  clearInterval(pollInterval)
                  get().updateTask(id, status.state === 'SUCCESS' ? 'completed' : 'failed')
                  get().addLog(`Agent ${id} ${status.state === 'SUCCESS' ? 'completed' : 'failed'}`,
                               status.state === 'SUCCESS' ? 'info' : 'error')
                  get().removeTask(id)
                }
              }
            } catch (error) {
              console.error('Error polling task status:', error)
            }
          }, 5000)

          return result
        } catch (error) {
          get().updateTask(id, 'failed')
          get().addLog(`Failed to run agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      importAgent: async (file) => {
        set({ loading: true, error: null })

        try {
          const formData = new FormData()
          formData.append('file', file)

          const response = await fetch('/api/agents/import', {
            method: 'POST',
            body: formData
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to import agent')
          }

          const agent = await response.json()
          set((state) => ({
            agents: [...state.agents, agent],
            loading: false
          }))

          get().addLog(`Agent imported: ${agent.name}`, 'info')
          return agent
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to import agent',
            loading: false
          })
          get().addLog(`Failed to import agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      exportAgent: async (id) => {
        try {
          const response = await fetch(`/api/agents/${id}/export`)
          if (!response.ok) throw new Error('Failed to export agent')

          const blob = await response.blob()
          get().addLog(`Agent exported: ${id}`, 'info')
          return blob
        } catch (error) {
          get().addLog(`Failed to export agent: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error')
          throw error
        }
      },

      getAgentStats: async (id, days = 30) => {
        try {
          const response = await fetch(`/api/agents/${id}/stats?days=${days}`)
          if (!response.ok) throw new Error('Failed to fetch agent stats')

          return await response.json()
        } catch (error) {
          console.error('Error fetching agent stats:', error)
          return null
        }
      },

      getAgentLogs: async (id, limit = 100) => {
        try {
          const response = await fetch(`/api/agents/${id}/logs?limit=${limit}`)
          if (!response.ok) throw new Error('Failed to fetch agent logs')

          return await response.json()
        } catch (error) {
          console.error('Error fetching agent logs:', error)
          return []
        }
      },

      fetchAgentTypes: async () => {
        try {
          const response = await fetch('/api/agents/types')
          if (!response.ok) throw new Error('Failed to fetch agent types')

          const types = await response.json()
          set({ agentTypes: types })
        } catch (error) {
          console.error('Error fetching agent types:', error)
        }
      }
    }),
    {
      name: 'agent-store'
    }
  )
)