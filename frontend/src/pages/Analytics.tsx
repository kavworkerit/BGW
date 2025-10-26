import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Space,
  Typography,
  Statistic,
  Table,
  Tag,
  Progress
} from 'antd'
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  DollarOutlined,
  CalendarOutlined,
  BarChartOutlined,
  LineChartOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'
import 'dayjs/locale/ru'
import { PriceChart } from '../components/PriceChart'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Option } = Select

interface AnalyticsData {
  totalGames: number
  activeStores: number
  totalEvents: number
  avgPrice: number
  priceChange: number
  topGames: Array<{
    title: string
    events: number
    avgPrice: number
    minPrice: number
    maxPrice: number
  }>
  storeStats: Array<{
    id: string
    name: string
    events: number
    avgPrice: number
    priceChange: number
  }>
  eventsByKind: Array<{
    kind: string
    count: number
    percentage: number
  }>
}

const Analytics: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [selectedGame, setSelectedGame] = useState<string>('')
  const [selectedStores, setSelectedStores] = useState<string[]>([])
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs]>([
    dayjs().subtract(30, 'day'),
    dayjs()
  ])
  const [chartData, setChartData] = useState<any[]>([])

  // Заглушка данных для демонстрации
  const mockData: AnalyticsData = {
    totalGames: 156,
    activeStores: 9,
    totalEvents: 2847,
    avgPrice: 2450,
    priceChange: -5.2,
    topGames: [
      { title: 'Громкое дело', events: 23, avgPrice: 2890, minPrice: 2500, maxPrice: 3200 },
      { title: 'Dune: Imperium', events: 18, avgPrice: 4200, minPrice: 3800, maxPrice: 4500 },
      { title: 'Монополия', events: 15, avgPrice: 1890, minPrice: 1500, maxPrice: 2100 },
      { title: 'Эволюция. Новые миры', events: 12, avgPrice: 3200, minPrice: 2900, maxPrice: 3500 },
      { title: 'Колонизаторы', events: 10, avgPrice: 3690, minPrice: 3400, maxPrice: 3990 }
    ],
    storeStats: [
      { id: 'hobbygames', name: 'Hobby Games', events: 456, avgPrice: 2650, priceChange: -2.1 },
      { id: 'lavkaigr', name: 'Лавка Игр', events: 342, avgPrice: 2890, priceChange: -8.3 },
      { id: 'nastolio', name: 'Nastol.io', events: 298, avgPrice: 2340, priceChange: 3.2 },
      { id: 'evrikus', name: 'Evrikus', events: 234, avgPrice: 2150, priceChange: -1.5 },
      { id: 'crowdgames', name: 'Crowd Games', events: 187, avgPrice: 2780, priceChange: -6.7 }
    ],
    eventsByKind: [
      { kind: 'price', count: 1234, percentage: 43.3 },
      { kind: 'discount', count: 678, percentage: 23.8 },
      { kind: 'release', count: 456, percentage: 16.0 },
      { kind: 'preorder', count: 345, percentage: 12.1 },
      { kind: 'announce', count: 134, percentage: 4.7 }
    ]
  }

  useEffect(() => {
    loadAnalyticsData()
  }, [dateRange])

  const loadAnalyticsData = async () => {
    setLoading(true)
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch(`/api/analytics?from=${dateRange[0].toISOString()}&to=${dateRange[1].toISOString()}`)
      // const data = await response.json()

      // Используем моковые данные
      setTimeout(() => {
        setData(mockData)
        setLoading(false)
      }, 1000)
    } catch (error) {
      console.error('Error loading analytics data:', error)
      setLoading(false)
    }
  }

  const loadChartData = async () => {
    if (!selectedGame || selectedStores.length === 0) return

    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch(`/api/prices?game_id=${selectedGame}&stores=${selectedStores.join(',')}&from=${dateRange[0].toISOString()}&to=${dateRange[1].toISOString()}`)
      // const chartData = await response.json()

      // Моковые данные для графика
      const mockChartData = selectedStores.map(store => ({
        store: store,
        data: Array.from({ length: 30 }, (_, i) => ({
          date: dayjs().subtract(29 - i, 'day').format('YYYY-MM-DD'),
          price: Math.floor(Math.random() * 2000) + 2000 + (store === 'hobbygames' ? 500 : 0)
        }))
      }))

      setChartData(mockChartData)
    } catch (error) {
      console.error('Error loading chart data:', error)
    }
  }

  useEffect(() => {
    loadChartData()
  }, [selectedGame, selectedStores])

  const gameColumns = [
    {
      title: 'Игра',
      dataIndex: 'title',
      key: 'title',
      render: (title: string) => <Text strong>{title}</Text>
    },
    {
      title: 'Событий',
      dataIndex: 'events',
      key: 'events',
      sorter: (a: any, b: any) => a.events - b.events
    },
    {
      title: 'Средняя цена',
      dataIndex: 'avgPrice',
      key: 'avgPrice',
      render: (price: number) => `${price.toLocaleString()} ₽`,
      sorter: (a: any, b: any) => a.avgPrice - b.avgPrice
    },
    {
      title: 'Диапазон цен',
      key: 'priceRange',
      render: (_, record: any) => (
        <Text type="secondary">
          {record.minPrice.toLocaleString()} - {record.maxPrice.toLocaleString()} ₽
        </Text>
      )
    }
  ]

  const storeColumns = [
    {
      title: 'Магазин',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <Text strong>{name}</Text>
    },
    {
      title: 'Событий',
      dataIndex: 'events',
      key: 'events',
      sorter: (a: any, b: any) => a.events - b.events
    },
    {
      title: 'Средняя цена',
      dataIndex: 'avgPrice',
      key: 'avgPrice',
      render: (price: number) => `${price.toLocaleString()} ₽`,
      sorter: (a: any, b: any) => a.avgPrice - b.avgPrice
    },
    {
      title: 'Изменение цен',
      dataIndex: 'priceChange',
      key: 'priceChange',
      render: (change: number) => (
        <Space>
          {change >= 0 ? (
            <TrendingUpOutlined style={{ color: '#f5222d' }} />
          ) : (
            <TrendingDownOutlined style={{ color: '#52c41a' }} />
          )}
          <Text style={{ color: change >= 0 ? '#f5222d' : '#52c41a' }}>
            {Math.abs(change)}%
          </Text>
        </Space>
      ),
      sorter: (a: any, b: any) => a.priceChange - b.priceChange
    }
  ]

  const kindColors: Record<string, string> = {
    price: 'blue',
    discount: 'green',
    release: 'orange',
    preorder: 'purple',
    announce: 'cyan'
  }

  const kindLabels: Record<string, string> = {
    price: 'Цена',
    discount: 'Скидка',
    release: 'Релиз',
    preorder: 'Предзаказ',
    announce: 'Анонс'
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Аналитика</Title>
        <Space>
          <RangePicker
            value={dateRange}
            onChange={(dates) => dates && setDateRange(dates)}
            locale={dayjs.locale('ru')}
          />
        </Space>
      </div>

      {/* Основная статистика */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего игр"
              value={data?.totalGames}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Активных магазинов"
              value={data?.activeStores}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего событий"
              value={data?.totalEvents}
              prefix={<CalendarOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Средняя цена"
              value={data?.avgPrice}
              suffix="₽"
              prefix={
                data?.priceChange && data.priceChange >= 0 ? (
                  <TrendingUpOutlined style={{ color: '#f5222d' }} />
                ) : (
                  <TrendingDownOutlined style={{ color: '#52c41a' }} />
                )
              }
              valueStyle={{
                color: data?.priceChange && data.priceChange >= 0 ? '#f5222d' : '#52c41a'
              }}
            />
            <div style={{ fontSize: '12px', marginTop: 4 }}>
              {data?.priceChange && (
                <Text type={data.priceChange >= 0 ? 'danger' : 'success'}>
                  {data.priceChange >= 0 ? '+' : ''}{data.priceChange}% за период
                </Text>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Распределение по типам событий */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="Распределение событий по типам">
            <Space direction="vertical" style={{ width: '100%' }}>
              {data?.eventsByKind.map((item) => (
                <div key={item.kind}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <Tag color={kindColors[item.kind]}>{kindLabels[item.kind]}</Tag>
                    <Text strong>{item.count} ({item.percentage}%)</Text>
                  </div>
                  <Progress percent={item.percentage} showInfo={false} strokeColor={kindColors[item.kind]} />
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="График цен">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Выберите игру:</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="Выберите игру для анализа"
                  value={selectedGame}
                  onChange={setSelectedGame}
                >
                  {data?.topGames.map((game) => (
                    <Option key={game.title} value={game.title}>
                      {game.title}
                    </Option>
                  ))}
                </Select>
              </div>

              <div>
                <Text strong>Магазины:</Text>
                <Select
                  mode="multiple"
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="Выберите магазины для сравнения"
                  value={selectedStores}
                  onChange={setSelectedStores}
                >
                  {data?.storeStats.map((store) => (
                    <Option key={store.id} value={store.id}>
                      {store.name}
                    </Option>
                  ))}
                </Select>
              </div>

              {selectedGame && selectedStores.length > 0 && (
                <div style={{ marginTop: 16, height: 300 }}>
                  <PriceChart
                    data={chartData}
                    title={`История цен: ${selectedGame}`}
                  />
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      {/* Таблицы с детальной информацией */}
      <Row gutter={16}>
        <Col span={12}>
          <Card title="Популярные игры" size="small">
            <Table
              columns={gameColumns}
              dataSource={data?.topGames}
              pagination={{ pageSize: 5 }}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="Активность магазинов" size="small">
            <Table
              columns={storeColumns}
              dataSource={data?.storeStats}
              pagination={{ pageSize: 5 }}
              size="small"
              loading={loading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Analytics