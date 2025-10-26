import api from './api'

export interface Game {
  id: string
  title: string
  synonyms: string[]
  bgg_id?: string
  publisher?: string
  tags: string[]
  created_at: string
}

export interface GameCreate {
  title: string
  synonyms?: string[]
  bgg_id?: string
  publisher?: string
  tags?: string[]
}

export const gameService = {
  // Получить список игр
  async getGames(): Promise<Game[]> {
    const response = await api.get('/api/games')
    return response.data
  },

  // Получить игру по ID
  async getGame(id: string): Promise<Game> {
    const response = await api.get(`/api/games/${id}`)
    return response.data
  },

  // Создать игру
  async createGame(game: GameCreate): Promise<Game> {
    const response = await api.post('/api/games', game)
    return response.data
  },

  // Обновить игру
  async updateGame(id: string, game: Partial<GameCreate>): Promise<Game> {
    const response = await api.put(`/api/games/${id}`, game)
    return response.data
  },

  // Удалить игру
  async deleteGame(id: string): Promise<void> {
    await api.delete(`/api/games/${id}`)
  },

  // Поиск игр (для мэтчинга)
  async searchGames(query: string): Promise<Game[]> {
    const response = await api.get(`/api/games/search?q=${encodeURIComponent(query)}`)
    return response.data
  }
}