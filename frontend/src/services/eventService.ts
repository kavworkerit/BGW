import api from './api'

export interface ListingEvent {
  id: string
  game_id?: string
  store_id?: string
  kind?: 'announce' | 'preorder' | 'release' | 'discount' | 'price'
  title?: string
  edition?: string
  price?: number
  currency: string
  discount_pct?: number
  in_stock?: boolean
  start_at?: string
  end_at?: string
  url?: string
  source_id?: string
  signature_hash: string
  created_at: string
  game_title?: string
  store_name?: string
  processed: boolean
}

export interface EventFilters {
  game_id?: string
  store_id?: string
  kind?: string
  min_discount?: number
  max_price?: number
  from_date?: string
  to_date?: string
  limit?: number
  offset?: number
}

export const eventService = {
  // Получить события с фильтрацией
  async getEvents(filters: EventFilters = {}): Promise<ListingEvent[]> {
    const params = new URLSearchParams()
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })

    const response = await api.get(`/api/events?${params}`)
    return response.data
  },

  // Получить событие по ID
  async getEvent(id: string): Promise<ListingEvent> {
    const response = await api.get(`/api/events/${id}`)
    return response.data
  },

  // Получить историю цен для игры
  async getPriceHistory(gameId: string, storeId?: string): Promise<any[]> {
    const params = new URLSearchParams()
    if (storeId) params.append('store_id', storeId)

    const response = await api.get(`/api/prices?game_id=${gameId}&${params}`)
    return response.data
  },

  // Получить статистику событий
  async getEventStats(): Promise<any> {
    const response = await api.get('/api/events/stats')
    return response.data
  }
}