import React, { useEffect, useState } from 'react'
import {
  Row,
  Col,
  Card,
  Statistic,
  List,
  Tag,
  Typography,
  Space,
  Spin,
  message,
  Button,
  Tooltip,
  Progress,
  Alert
} from 'antd'
import {
  DatabaseOutlined,
  RobotOutlined,
  BellOutlined,
  CalendarOutlined,
  TrendingUpOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import { useGameStore } from '../store/useGameStore'
import { useAgentStore } from '../store/useAgentStore'
import { useNotificationStore } from '../store/useNotificationStore'

const { Title, Text } = Typography
const { Space } = Space

interface DashboardStats {
  totalGames: number
  activeAgents: number
  todayEvents: number
  activeRules: number
  todayPages: number
  successRate: number
}

interface DashboardEvent {
  id: string
  title: string
  store_name?: string
  price?: number
  discount_pct?: number
  kind: string
  created_at: string
  url?: string
}

interface AgentStatus {
  id: string
  name: string
  enabled: boolean
  last_run?: string
  status: 'idle' | 'running' | 'error' | 'success'
  daily_pages?: number
  success_rate?: number
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<DashboardStats>({
    totalGames: 0,
    activeAgents: 0,
    todayEvents: 0,
    activeRules: 0,
    todayPages: 0,
    successRate: 0
  })

  const [recentEvents, setRecentEvents] = useState<DashboardEvent[]>([])
  const [agentStatuses, setAgentStatuses] = useState<AgentStatus[]>([])
  const [refreshing, setRefreshing] = useState(false)

  // Store hooks
  const { games, fetchGames } = useGameStore()
  const { agents, fetchAgents, runAgent, addLog, runningTasks } = useAgentStore()
  const { rules, fetchRules, notifications } = useNotificationStore()

  // Load dashboard data
  const loadDashboardData = async () => {
    setLoading(true)
    try {
      await Promise.all([
        fetchGames(),
        fetchAgents(),
        fetchRules()
      ])

      // Fetch recent events
      const eventsResponse = await fetch('/api/events?limit=10')
      if (eventsResponse.ok) {
        const events = await eventsResponse.json()
        setRecentEvents(events)
      }

      // Fetch dashboard stats
      const statsResponse = await fetch('/api/dashboard/stats')
      if (statsResponse.ok) {
        const dashboardStats = await statsResponse.json()
        setStats(dashboardStats)
      }

      // Fetch agent statuses
      if (agents.length > 0) {
        const agentStatuses = await Promise.all(
          agents.slice(0, 5).map(async (agent) => {
            try {
              const statsResponse = await fetch(`/api/agents/${agent.id}/stats?days=1`)
              if (statsResponse.ok) {
                const agentStats = await statsResponse.json()
                return {
                  id: agent.id,
                  name: agent.name,
                  enabled: agent.enabled,
                  last_run: agentStats.last_run,
                  status: agent.enabled ? 'idle' : 'disabled',
                  daily_pages: agentStats.pages_fetched,
                  success_rate: agentStats.success_rate
                }
              }
              return {
                id: agent.id,
                name: agent.name,
                enabled: agent.enabled,
                status: 'error'
              }
            } catch (error) {
              return {
                id: agent.id,
                name: agent.name,
                enabled: agent.enabled,
                status: 'error'
              }
            }
          })
        )
        setAgentStatuses(agentStatuses)
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error)
      message.error('Не удалось загрузить данные дашборда')
    } finally {
      setLoading(false)
    }
  }

  const refreshDashboard = async () => {
    setRefreshing(true)
    addLog('Refreshing dashboard data...', 'info')
    await loadDashboardData()
    setRefreshing(false)
  }

  const handleRunAgent = async (agentId: string) => {
    try {
      await runAgent(agentId)
      message.success('Агент запущен')
      addLog(`Agent ${agentId} started`, 'info')
      // Refresh after a short delay
      setTimeout(() => {
        loadDashboardData()
      }, 2000)
    } catch (error) {
      message.error('Не удалось запустить агента')
      addLog(`Failed to run agent ${agentId}`, 'error')
    }
  }

  const getAgentIcon = (status: string, running: boolean) => {
    if (running) {
      return <PlayCircleOutlined style={{ color: '#52c41a' }} />
    }

    switch (status) {
      case 'idle':
        return <PauseCircleOutlined style={{ color: '#1890ff' }} />
      case 'running':
        return <PlayCircleOutlined style={{ color: '#52c41a' }} />
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'disabled':
        return <PauseCircleOutlined style={{ color: '#d9d9d9' }} />
      default:
        return <PauseCircleOutlined />
    }
  }

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffDays > 0) return `${diffDays} дн. назад`
    if (diffHours > 0) return `${diffHours} ч. назад`
    if (diffMins > 0) return `${diffMins} мин. назад`
    return 'Только что'
  }

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'preorder': 'blue',
      'discount': 'red',
      'release': 'green',
      'announce': 'orange',
      'price': 'default'
    }
    return colors[type] || 'default'
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'preorder': 'Предзаказ',
      'discount': 'Скидка',
      'release': 'Релиз',
      'announce': 'Анонс',
      'price': 'Цена'
    }
    return labels[type] || type
  }

  useEffect(() => {
    loadDashboardData()

    // Set up periodic refresh
    const interval = setInterval(() => {
      loadDashboardData()
    }, 30000) // Refresh every 30 seconds

    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <Title level={4} style={{ marginTop: 16 }}>Загрузка дашборда...</Title>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Дашборд</Title>
        <Space>
          <Tooltip title="Обновить данные">
            <Button
              icon={<ReloadOutlined />}
              onClick={refreshDashboard}
              loading={refreshing}
            >
              Обновить
            </Button>
          </Tooltip>
        </Space>
      </div>

      {/* System Status Alert */}
      {stats.successRate < 80 && (
        <Alert
          message="Низкий уровень успешности"
          description={`Успешность выполнения агентов: ${stats.successRate}%. Рекомендуется проверить настройки агентов.`}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Stats Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card">
            <Statistic
              title="Игр в отслеживании"
              value={games.length}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card">
            <Statistic
              title="Активных агентов"
              value={agents.filter(a => a.enabled).length}
              prefix={<RobotOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card">
            <Statistic
              title="Событий сегодня"
              value={stats.todayEvents}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stats-card">
            <Statistic
              title="Активных правил"
              value={rules.filter(r => r.enabled).length}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Additional Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Производительность системы">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text>Успешность агентов</Text>
                <Progress
                  percent={stats.successRate}
                  status={stats.successRate >= 80 ? 'success' : stats.successRate >= 50 ? 'normal' : 'exception'}
                  format={percent => `${percent}%`}
                />
              </div>
              <div>
                <Text>Страниц сегодня</Text>
                <Text strong style={{ float: 'right' }}>{stats.todayPages} / 1000</Text>
              </div>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Сводка">
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Всего агентов"
                  value={agents.length}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Всего правил"
                  value={rules.length}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Уведомлений"
                  value={notifications.length}
                  valueStyle={{ fontSize: '16px' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Последние события" extra={<TrendingUpOutlined />}>
            <List
              itemLayout="horizontal"
              dataSource={recentEvents}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={
                      <Space>
                        <Text strong>{item.title}</Text>
                        <Tag color={getTypeColor(item.kind)}>
                          {getTypeLabel(item.kind)}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space split={<span>•</span>}>
                        <Text>{item.store_name || 'Неизвестный магазин'}</Text>
                        {item.price && (
                          <Text className="event-price">
                            {item.price} ₽
                          </Text>
                        )}
                        {item.discount_pct && (
                          <Text className="event-discount" style={{ color: '#ff4d4f' }}>
                            -{item.discount_pct}%
                          </Text>
                        )}
                        <Text type="secondary">{formatTimeAgo(item.created_at)}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Статус агентов">
            <List
              itemLayout="horizontal"
              dataSource={agentStatuses}
              renderItem={(item) => {
                const isRunning = runningTasks.has(item.id)
                return (
                  <List.Item
                    actions={
                      item.enabled && !isRunning ? [
                        <Tooltip title="Запустить агента">
                          <Button
                            size="small"
                            icon={<PlayCircleOutlined />}
                            onClick={() => handleRunAgent(item.id)}
                          />
                        </Tooltip>
                      ] : undefined
                    }
                  >
                    <List.Item.Meta
                      avatar={getAgentIcon(item.status, isRunning)}
                      title={
                        <Space>
                          <Text>{item.name}</Text>
                          {isRunning && (
                            <Tag color="processing">Запущен</Tag>
                          )}
                        </Space>
                      }
                      description={
                        <Space split={<span>•</span>} size="small">
                          <Text
                            type={
                              item.status === 'error' ? 'danger' :
                              item.status === 'disabled' ? 'secondary' :
                              'success'
                            }
                          >
                            {item.status === 'idle' ? 'Готов' :
                             item.status === 'running' ? 'Работает' :
                             item.status === 'error' ? 'Ошибка' :
                             item.status === 'success' ? 'Завершен' :
                             item.status === 'disabled' ? 'Отключен' :
                             item.status}
                          </Text>
                          {item.last_run && (
                            <Text type="secondary">{formatTimeAgo(item.last_run)}</Text>
                          )}
                          {item.daily_pages && (
                            <Text type="secondary">{item.daily_pages} стр.</Text>
                          )}
                        </Space>
                      }
                    />
                  </List.Item>
                )
              }}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard