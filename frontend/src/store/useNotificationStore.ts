import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

interface Notification {
  id: string
  rule_id: string
  event_id: string
  status: 'pending' | 'sent' | 'error' | 'deferred'
  sent_at?: string
  meta: Record<string, any>
  created_at: string
}

interface AlertRule {
  id: string
  name: string
  logic: 'AND' | 'OR'
  conditions: any[]
  channels: string[]
  cooldown_hours: number
  enabled: boolean
  created_at: string
}

interface NotificationState {
  notifications: Notification[]
  rules: AlertRule[]
  loading: boolean
  error: string | null
  stats: {
    total: number
    sent: number
    errors: number
    pending: number
  }
}

interface NotificationActions {
  // Actions
  fetchNotifications: (params?: { limit?: number; status?: string }) => Promise<void>
  fetchRules: () => Promise<void>
  createRule: (rule: Partial<AlertRule>) => Promise<AlertRule>
  updateRule: (id: string, rule: Partial<AlertRule>) => Promise<AlertRule>
  deleteRule: (id: string) => Promise<void>
  testRule: (id: string) => Promise<any>
  testWebpush: () => Promise<boolean>
  testTelegram: () => Promise<boolean>

  // Setters
  setNotifications: (notifications: Notification[]) => void
  setRules: (rules: AlertRule[]) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setStats: (stats: NotificationState['stats']) => void
}

export const useNotificationStore = create<NotificationState & NotificationActions>()(
  devtools(
    (set, get) => ({
      // Initial state
      notifications: [],
      rules: [],
      loading: false,
      error: null,
      stats: {
        total: 0,
        sent: 0,
        errors: 0,
        pending: 0
      },

      // Setters
      setNotifications: (notifications) => set({ notifications }),
      setRules: (rules) => set({ rules }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setStats: (stats) => set({ stats }),

      // Actions
      fetchNotifications: async (params = {}) => {
        set({ loading: true, error: null })

        try {
          const queryParams = new URLSearchParams()
          if (params.limit) queryParams.append('limit', params.limit.toString())
          if (params.status) queryParams.append('status', params.status)

          const response = await fetch(`/api/notifications?${queryParams}`)
          if (!response.ok) throw new Error('Failed to fetch notifications')

          const notifications = await response.json()
          set({ notifications, loading: false })

          // Calculate stats
          const stats = notifications.reduce((acc, notif) => {
            acc.total += 1
            if (notif.status === 'sent') acc.sent += 1
            else if (notif.status === 'error') acc.errors += 1
            else if (notif.status === 'pending') acc.pending += 1
            return acc
          }, { total: 0, sent: 0, errors: 0, pending: 0 })

          set({ stats })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch notifications',
            loading: false
          })
        }
      },

      fetchRules: async () => {
        set({ loading: true, error: null })

        try {
          const response = await fetch('/api/rules')
          if (!response.ok) throw new Error('Failed to fetch rules')

          const rules = await response.json()
          set({ rules, loading: false })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch rules',
            loading: false
          })
        }
      },

      createRule: async (ruleData) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ruleData)
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to create rule')
          }

          const rule = await response.json()
          set((state) => ({
            rules: [...state.rules, rule],
            loading: false
          }))

          return rule
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create rule',
            loading: false
          })
          throw error
        }
      },

      updateRule: async (id, ruleData) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch(`/api/rules/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(ruleData)
          })

          if (!response.ok) {
            const errorData = await response.json()
            throw new Error(errorData.detail || 'Failed to update rule')
          }

          const rule = await response.json()
          set((state) => ({
            rules: state.rules.map(r => r.id === id ? rule : r),
            loading: false
          }))

          return rule
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update rule',
            loading: false
          })
          throw error
        }
      },

      deleteRule: async (id) => {
        set({ loading: true, error: null })

        try {
          const response = await fetch(`/api/rules/${id}`, {
            method: 'DELETE'
          })

          if (!response.ok) {
            throw new Error('Failed to delete rule')
          }

          set((state) => ({
            rules: state.rules.filter(r => r.id !== id),
            loading: false
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete rule',
            loading: false
          })
          throw error
        }
      },

      testRule: async (id) => {
        try {
          const response = await fetch(`/api/rules/${id}/test`, {
            method: 'POST'
          })

          if (!response.ok) throw new Error('Failed to test rule')

          return await response.json()
        } catch (error) {
          console.error('Error testing rule:', error)
          return null
        }
      },

      testWebpush: async () => {
        try {
          const response = await fetch('/api/notifications/test/webpush', {
            method: 'POST'
          })

          if (!response.ok) throw new Error('Failed to test WebPush')

          const result = await response.json()
          return result.success || false
        } catch (error) {
          console.error('Error testing WebPush:', error)
          return false
        }
      },

      testTelegram: async () => {
        try {
          const response = await fetch('/api/notifications/test/telegram', {
            method: 'POST'
          })

          if (!response.ok) throw new Error('Failed to test Telegram')

          const result = await response.json()
          return result.success || false
        } catch (error) {
          console.error('Error testing Telegram:', error)
          return false
        }
      }
    }),
    {
      name: 'notification-store'
    }
  )
)