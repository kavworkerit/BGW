import api from './api'

export interface Agent {
  id: string
  name: string
  type: 'api' | 'html' | 'headless' | 'telegram_public'
  schedule: any
  rate_limit: any
  config: any
  enabled: boolean
  created_at: string
  last_run?: string
  status?: 'idle' | 'running' | 'error'
}

export interface AgentCreate {
  id: string
  name: string
  type: 'api' | 'html' | 'headless' | 'telegram_public'
  schedule: any
  rate_limit: any
  config: any
  enabled?: boolean
}

export const agentService = {
  // Получить список агентов
  async getAgents(): Promise<Agent[]> {
    const response = await api.get('/api/agents')
    return response.data
  },

  // Получить агента по ID
  async getAgent(id: string): Promise<Agent> {
    const response = await api.get(`/api/agents/${id}`)
    return response.data
  },

  // Создать агента
  async createAgent(agent: AgentCreate): Promise<Agent> {
    const response = await api.post('/api/agents', agent)
    return response.data
  },

  // Обновить агента
  async updateAgent(id: string, agent: Partial<AgentCreate>): Promise<Agent> {
    const response = await api.put(`/api/agents/${id}`, agent)
    return response.data
  },

  // Удалить агента
  async deleteAgent(id: string): Promise<void> {
    await api.delete(`/api/agents/${id}`)
  },

  // Запустить агента вручную
  async runAgent(id: string): Promise<void> {
    await api.post(`/api/agents/${id}/run`)
  },

  // Импортировать агента из ZIP
  async importAgent(file: File): Promise<Agent> {
    const formData = new FormData()
    formData.append('file', file)
    const response = await api.post('/api/agents/import', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },

  // Экспортировать агента в ZIP
  async exportAgent(id: string): Promise<Blob> {
    const response = await api.get(`/api/agents/${id}/export`, {
      responseType: 'blob',
    })
    return response.data
  },

  // Получить логи агента
  async getAgentLogs(id: string): Promise<any[]> {
    const response = await api.get(`/api/agents/${id}/logs`)
    return response.data
  }
}