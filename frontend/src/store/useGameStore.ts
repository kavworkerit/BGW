import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import { Game } from '../services/gameService'

interface GameState {
  games: Game[]
  currentGame: Game | null
  loading: boolean
  error: string | null
  filters: {
    search: string
    publisher: string
    minPlayers: number | null
    maxPlayers: number | null
    minPlaytime: number | null
    maxPlaytime: number | null
    tags: string
    language: string
  }
  pagination: {
    skip: number
    limit: number
    total: number
  }
}

interface GameActions {
  // Actions
  fetchGames: (params?: Partial<GameState['filters'] & { skip?: number; limit?: number }>) => Promise<void>
  fetchGame: (id: string) => Promise<void>
  createGame: (game: Partial<Game>) => Promise<void>
  updateGame: (id: string, game: Partial<Game>) => Promise<void>
  deleteGame: (id: string) => Promise<void>
  searchGames: (query: string) => Promise<void>

  // Setters
  setGames: (games: Game[]) => void
  setCurrentGame: (game: Game | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setFilters: (filters: Partial<GameState['filters']>) => void
  setPagination: (pagination: Partial<GameState['pagination']>) => void
  resetFilters: () => void

  // Additional actions
  matchGame: (title: string, threshold?: number) => Promise<Game[]>
  getGamePriceHistory: (id: string, storeId?: string, days?: number) => Promise<any[]>
  getGameEvents: (id: string, filters?: any) => Promise<any[]>

  // Statistics
  getStats: () => Promise<any>

  // Price history with extended filters
  fetchPriceHistory: (params: any) => Promise<any[]>
  exportPriceHistory: (params: any) => Promise<void>
}

const initialFilters: GameState['filters'] = {
  search: '',
  publisher: '',
  minPlayers: null,
  maxPlayers: null,
  minPlaytime: null,
  maxPlaytime: null,
  tags: '',
  language: ''
}

const initialPagination: GameState['pagination'] = {
  skip: 0,
  limit: 100,
  total: 0
}

export const useGameStore = create<GameState & GameActions>()(
  devtools(
    (set, get) => ({
      // Initial state
      games: [],
      currentGame: null,
      loading: false,
      error: null,
      filters: initialFilters,
      pagination: initialPagination,

      // Setters
      setGames: (games) => set({ games }),
      setCurrentGame: (game) => set({ currentGame: game }),
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      setFilters: (filters) => set((state) => ({ filters: { ...state.filters, ...filters } })),
      setPagination: (pagination) => set((state) => ({ pagination: { ...state.pagination, ...pagination } })),
      resetFilters: () => set({ filters: initialFilters, pagination: { ...initialPagination, skip: 0 } }),

      // Actions
      fetchGames: async (params = {}) => {
        set({ loading: true, error: null })

        try {
          const { fetchGames } = await import('../services/gameService')
          const { filters, pagination } = get()

          const requestParams = {
            skip: pagination.skip,
            limit: pagination.limit,
            ...filters,
            ...params
          }

          const games = await fetchGames(requestParams)

          set({
            games: params.skip === 0 ? games : [...get().games, ...games],
            loading: false
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch games',
            loading: false
          })
        }
      },

      fetchGame: async (id) => {
        set({ loading: true, error: null })

        try {
          const { getGame } = await import('../services/gameService')
          const game = await getGame(id)

          set({
            currentGame: game,
            loading: false
          })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to fetch game',
            loading: false
          })
        }
      },

      createGame: async (gameData) => {
        set({ loading: true, error: null })

        try {
          const { createGame } = await import('../services/gameService')
          const game = await createGame(gameData as any)

          set((state) => ({
            games: [game, ...state.games],
            loading: false
          }))

          return game
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to create game',
            loading: false
          })
          throw error
        }
      },

      updateGame: async (id, gameData) => {
        set({ loading: true, error: null })

        try {
          const { updateGame } = await import('../services/gameService')
          const game = await updateGame(id, gameData)

          set((state) => ({
            games: state.games.map(g => g.id === id ? game : g),
            currentGame: state.currentGame?.id === id ? game : state.currentGame,
            loading: false
          }))

          return game
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to update game',
            loading: false
          })
          throw error
        }
      },

      deleteGame: async (id) => {
        set({ loading: true, error: null })

        try {
          const { deleteGame } = await import('../services/gameService')
          await deleteGame(id)

          set((state) => ({
            games: state.games.filter(g => g.id !== id),
            currentGame: state.currentGame?.id === id ? null : state.currentGame,
            loading: false
          }))
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to delete game',
            loading: false
          })
          throw error
        }
      },

      searchGames: async (query) => {
        set({ loading: true, error: null })

        try {
          const { getGame } = await import('../services/gameService')
          // Используем endpoint поиска или фильтрации
          await get().fetchGames({ search: query })
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Failed to search games',
            loading: false
          })
        }
      },

      matchGame: async (title, threshold = 0.75) => {
        try {
          const response = await fetch(`/api/games/match?title=${encodeURIComponent(title)}&threshold=${threshold}`)
          if (!response.ok) throw new Error('Failed to match game')

          return await response.json()
        } catch (error) {
          console.error('Error matching game:', error)
          return []
        }
      },

      getGamePriceHistory: async (id, storeId, days = 30) => {
        try {
          const params = new URLSearchParams({ days: days.toString() })
          if (storeId) params.append('store_id', storeId)

          const response = await fetch(`/api/games/${id}/price-history?${params}`)
          if (!response.ok) throw new Error('Failed to fetch price history')

          return await response.json()
        } catch (error) {
          console.error('Error fetching price history:', error)
          return []
        }
      },

      getGameEvents: async (id, filters = {}) => {
        try {
          const params = new URLSearchParams()
          Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
              params.append(key, value.toString())
            }
          })

          const response = await fetch(`/api/games/${id}/events?${params}`)
          if (!response.ok) throw new Error('Failed to fetch game events')

          return await response.json()
        } catch (error) {
          console.error('Error fetching game events:', error)
          return []
        }
      },

      getStats: async () => {
        try {
          const response = await fetch('/api/games/stats')
          if (!response.ok) throw new Error('Failed to fetch stats')

          return await response.json()
        } catch (error) {
          console.error('Error fetching stats:', error)
          return null
        }
      },

      fetchPriceHistory: async (params) => {
        try {
          const queryString = new URLSearchParams()
          Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
              if (Array.isArray(value)) {
                value.forEach(v => queryString.append(key, v.toString()))
              } else {
                queryString.append(key, value.toString())
              }
            }
          })

          const response = await fetch(`/api/prices?${queryString}`)
          if (!response.ok) throw new Error('Failed to fetch price history')

          return await response.json()
        } catch (error) {
          console.error('Error fetching price history:', error)
          throw error
        }
      },

      exportPriceHistory: async (params) => {
        try {
          const queryString = new URLSearchParams()
          Object.entries(params).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
              if (Array.isArray(value)) {
                value.forEach(v => queryString.append(key, v.toString()))
              } else {
                queryString.append(key, value.toString())
              }
            }
          })

          const response = await fetch(`/api/prices/export?${queryString}`)
          if (!response.ok) throw new Error('Failed to export price history')

          // Create blob and download
          const blob = await response.blob()
          const url = window.URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `price-history-${params.game_id}-${new Date().toISOString().split('T')[0]}.csv`
          document.body.appendChild(a)
          a.click()
          window.URL.revokeObjectURL(url)
          document.body.removeChild(a)
        } catch (error) {
          console.error('Error exporting price history:', error)
          throw error
        }
      }
    }),
    {
      name: 'game-store'
    }
  )
)