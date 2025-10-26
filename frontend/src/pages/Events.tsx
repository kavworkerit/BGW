import React, { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Space,
  Tag,
  Typography,
  DatePicker,
  Select,
  Input,
  Card,
  Row,
  Col,
  Statistic,
  Tooltip,
  Modal,
  Descriptions,
  message,
  Drawer,
  Empty
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  EyeOutlined,
  ReloadOutlined,
  CalendarOutlined,
  ShopOutlined,
  TagOutlined,
  DollarOutlined
} from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Search } = Input
const { Option } = Select

interface Event {
  id: string
  title: string
  game_name?: string
  game_id?: string
  store_name?: string
  store_id?: string
  kind: 'preorder' | 'discount' | 'release' | 'announce' | 'price'
  price?: number
  discount_pct?: number
  url?: string
  in_stock?: boolean
  created_at: string
  meta?: Record<string, any>
}

interface EventFilters {
  search?: string
  game_id?: string
  store_id?: string
  kind?: string
  min_discount?: number
  max_price?: number
  date_range?: [Dayjs, Dayjs]
  in_stock?: boolean
}

const Events: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [isDrawerVisible, setIsDrawerVisible] = useState(false)
  const [stats, setStats] = useState({
    total: 0,
    today: 0,
    discounts: 0,
    preorders: 0
  })
  const [filters, setFilters] = useState<EventFilters>({})
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0
  })

  // Load events on component mount and filter changes
  useEffect(() => {
    loadEvents()
    loadStats()
  }, [filters, pagination.current, pagination.pageSize])

  const loadEvents = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()

      if (filters.search) params.append('search', filters.search)
      if (filters.game_id) params.append('game_id', filters.game_id)
      if (filters.store_id) params.append('store_id', filters.store_id)
      if (filters.kind) params.append('kind', filters.kind)
      if (filters.min_discount) params.append('min_discount', filters.min_discount.toString())
      if (filters.max_price) params.append('max_price', filters.max_price.toString())
      if (filters.in_stock !== undefined) params.append('in_stock', filters.in_stock.toString())
      if (filters.date_range) {
        params.append('from_date', filters.date_range[0].toISOString())
        params.append('to_date', filters.date_range[1].toISOString())
      }

      params.append('limit', pagination.pageSize.toString())
      params.append('offset', ((pagination.current - 1) * pagination.pageSize).toString())

      const response = await fetch(`/api/events?${params}`)
      if (!response.ok) throw new Error('Failed to fetch events')

      const eventsData = await response.json()
      setEvents(eventsData)

      // Get total count for pagination
      const countResponse = await fetch(`/api/events/count?${params}`)
      if (countResponse.ok) {
        const { total } = await countResponse.json()
        setPagination(prev => ({ ...prev, total }))
      }
    } catch (error) {
      message.error('Не удалось загрузить события')
      console.error('Error loading events:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      // Get today's start date
      const today = dayjs().startOf('day').toISOString()

      const [totalResponse, todayResponse] = await Promise.all([
        fetch('/api/events/count'),
        fetch(`/api/events/count?from_date=${today}`)
      ])

      if (totalResponse.ok && todayResponse.ok) {
        const total = await totalResponse.json()
        const todayStats = await todayResponse.json()

        // Count by kind
        const discountsResponse = await fetch('/api/events/count?kind=discount')
        const preordersResponse = await fetch('/api/events/count?kind=preorder')

        const discounts = discountsResponse.ok ? await discountsResponse.json() : { total: 0 }
        const preorders = preordersResponse.ok ? await preordersResponse.json() : { total: 0 }

        setStats({
          total: total.total || 0,
          today: todayStats.total || 0,
          discounts: discounts.total || 0,
          preorders: preorders.total || 0
        })
      }
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handleFilterChange = (key: keyof EventFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }))
    setPagination(prev => ({ ...prev, current: 1 }))
  }

  const handleTableChange = (pagination: any) => {
    setPagination(pagination)
  }

  const handleViewEvent = (event: Event) => {
    setSelectedEvent(event)
    setIsDrawerVisible(true)
  }

  const exportEvents = async () => {
    try {
      const params = new URLSearchParams()

      // Add current filters to export
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (key === 'date_range' && Array.isArray(value)) {
            params.append('from_date', value[0].toISOString())
            params.append('to_date', value[1].toISOString())
          } else if (typeof value !== 'object') {
            params.append(key, value.toString())
          }
        }
      })

      const response = await fetch(`/api/export/events?${params}`)
      if (!response.ok) throw new Error('Failed to export events')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `events_${dayjs().format('YYYY-MM-DD')}.csv`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      message.success('События экспортированы')
    } catch (error) {
      message.error('Не удалось экспортировать события')
      console.error('Error exporting events:', error)
    }
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

  const formatTimeAgo = (dateString: string) => {
    const date = dayjs(dateString)
    const now = dayjs()
    const diffMins = now.diff(date, 'minute')
    const diffHours = now.diff(date, 'hour')
    const diffDays = now.diff(date, 'day')

    if (diffDays > 0) return `${diffDays} дн. назад`
    if (diffHours > 0) return `${diffHours} ч. назад`
    if (diffMins > 0) return `${diffMins} мин. назад`
    return 'Только что'
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Event) => (
        <div>
          <Text strong>{title}</Text>
          {record.game_name && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Игра: {record.game_name}
              </Text>
            </div>
          )}
        </div>
      ),
      ellipsis: true
    },
    {
      title: 'Тип',
      dataIndex: 'kind',
      key: 'kind',
      width: 120,
      render: (kind: string) => (
        <Tag color={getTypeColor(kind)}>
          {getTypeLabel(kind)}
        </Tag>
      ),
      filters: [
        { text: 'Предзаказ', value: 'preorder' },
        { text: 'Скидка', value: 'discount' },
        { text: 'Релиз', value: 'release' },
        { text: 'Анонс', value: 'announce' },
        { text: 'Цена', value: 'price' }
      ],
      onFilter: (value: string, record: Event) => record.kind === value
    },
    {
      title: 'Магазин',
      dataIndex: 'store_name',
      key: 'store_name',
      width: 150,
      render: (storeName: string) => (
        <Text>{storeName || 'Неизвестно'}</Text>
      )
    },
    {
      title: 'Цена',
      key: 'price',
      width: 120,
      render: (record: Event) => (
        <div>
          {record.price && (
            <Text strong>{record.price} ₽</Text>
          )}
          {record.discount_pct && (
            <div>
              <Tag color="red" size="small">-{record.discount_pct}%</Tag>
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Наличие',
      dataIndex: 'in_stock',
      key: 'in_stock',
      width: 100,
      render: (in_stock?: boolean) => (
        <Tag color={in_stock ? 'green' : 'red'}>
          {in_stock ? 'В наличии' : 'Нет в наличии'}
        </Tag>
      ),
      filters: [
        { text: 'В наличии', value: true },
        { text: 'Нет в наличии', value: false }
      ],
      onFilter: (value: boolean, record: Event) => record.in_stock === value
    },
    {
      title: 'Время',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('DD.MM.YYYY HH:mm')}>
          <Text>{formatTimeAgo(date)}</Text>
        </Tooltip>
      ),
      sorter: (a: Event, b: Event) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: 'descend' as const
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 80,
      render: (record: Event) => (
        <Space>
          <Tooltip title="Подробнее">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleViewEvent(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>События</Title>
        <Space>
          <Button
            icon={<ExportOutlined />}
            onClick={exportEvents}
          >
            Экспорт
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadEvents}
            loading={loading}
          >
            Обновить
          </Button>
        </Space>
      </div>

      {/* Статистика */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Всего событий"
              value={stats.total}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Сегодня"
              value={stats.today}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Скидки"
              value={stats.discounts}
              prefix={<TagOutlined style={{ color: '#ff4d4f' }} />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Предзаказы"
              value={stats.preorders}
              prefix={<ShopOutlined style={{ color: '#1890ff' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* Фильтры */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Search
              placeholder="Поиск по названию..."
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && handleFilterChange('search', '')}
              style={{ width: '100%' }}
            />
          </Col>
          <Col>
            <RangePicker
              placeholder={['Дата начала', 'Дата окончания']}
              onChange={(dates) => handleFilterChange('date_range', dates)}
              style={{ width: 250 }}
            />
          </Col>
          <Col>
            <Select
              placeholder="Тип события"
              allowClear
              style={{ width: 150 }}
              onChange={(value) => handleFilterChange('kind', value)}
            >
              <Option value="preorder">Предзаказ</Option>
              <Option value="discount">Скидка</Option>
              <Option value="release">Релиз</Option>
              <Option value="announce">Анонс</Option>
              <Option value="price">Цена</Option>
            </Select>
          </Col>
          <Col>
            <Select
              placeholder="Наличие"
              allowClear
              style={{ width: 130 }}
              onChange={(value) => handleFilterChange('in_stock', value)}
            >
              <Option value={true}>В наличии</Option>
              <Option value={false}>Нет в наличии</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Таблица событий */}
      <Card>
        <Table
          columns={columns}
          dataSource={events}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} событий`,
            onChange: (page, pageSize) => {
              setPagination(prev => ({ ...prev, current: page, pageSize }))
            }
          }}
          onChange={handleTableChange}
          scroll={{ x: 1000 }}
          locale={{
            emptyText: <Empty description="События не найдены" />
          }}
        />
      </Card>

      {/* Drawer для просмотра деталей события */}
      <Drawer
        title="Детали события"
        placement="right"
        size="large"
        open={isDrawerVisible}
        onClose={() => setIsDrawerVisible(false)}
      >
        {selectedEvent && (
          <div>
            <Descriptions column={1} bordered>
              <Descriptions.Item label="Название">
                <Text strong>{selectedEvent.title}</Text>
              </Descriptions.Item>
              {selectedEvent.game_name && (
                <Descriptions.Item label="Игра">
                  {selectedEvent.game_name}
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Тип">
                <Tag color={getTypeColor(selectedEvent.kind)}>
                  {getTypeLabel(selectedEvent.kind)}
                </Tag>
              </Descriptions.Item>
              {selectedEvent.store_name && (
                <Descriptions.Item label="Магазин">
                  {selectedEvent.store_name}
                </Descriptions.Item>
              )}
              {selectedEvent.price && (
                <Descriptions.Item label="Цена">
                  <Text strong>{selectedEvent.price} ₽</Text>
                </Descriptions.Item>
              )}
              {selectedEvent.discount_pct && (
                <Descriptions.Item label="Скидка">
                  <Tag color="red">-{selectedEvent.discount_pct}%</Tag>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Наличие">
                <Tag color={selectedEvent.in_stock ? 'green' : 'red'}>
                  {selectedEvent.in_stock ? 'В наличии' : 'Нет в наличии'}
                </Tag>
              </Descriptions.Item>
              {selectedEvent.url && (
                <Descriptions.Item label="Ссылка">
                  <a href={selectedEvent.url} target="_blank" rel="noopener noreferrer">
                    Открыть страницу
                  </a>
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Дата создания">
                {dayjs(selectedEvent.created_at).format('DD.MM.YYYY HH:mm:ss')}
              </Descriptions.Item>
            </Descriptions>

            {selectedEvent.meta && Object.keys(selectedEvent.meta).length > 0 && (
              <div style={{ marginTop: 24 }}>
                <Title level={5}>Дополнительные данные</Title>
                <pre style={{
                  background: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(selectedEvent.meta, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </Drawer>
    </div>
  )
}

export default Events