import React, { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Card, Select, DatePicker, Button, Space, Spin, message } from 'antd'
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons'
import { useGameStore } from '../store/useGameStore'
import dayjs from 'dayjs'

const { Option } = Select
const { RangePicker } = DatePicker

interface PriceData {
  observed_at: string
  price: number
  store_name: string
  currency: string
}

interface PriceChartProps {
  gameId: string
  gameTitle: string
}

const PriceChart: React.FC<PriceChartProps> = ({ gameId, gameTitle }) => {
  const [priceData, setPriceData] = useState<PriceData[]>([])
  const [selectedStores, setSelectedStores] = useState<string[]>([])
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null)
  const [loading, setLoading] = useState(false)
  const [stores, setStores] = useState<string[]>([])

  const { fetchPriceHistory, exportPriceHistory } = useGameStore()

  useEffect(() => {
    loadPriceHistory()
  }, [gameId, selectedStores, dateRange])

  const loadPriceHistory = async () => {
    if (!gameId) return

    setLoading(true)
    try {
      const params: any = {
        game_id: gameId,
      }

      if (selectedStores.length > 0) {
        params.store_ids = selectedStores
      }

      if (dateRange) {
        params.from = dateRange[0].format('YYYY-MM-DD')
        params.to = dateRange[1].format('YYYY-MM-DD')
      }

      const data = await fetchPriceHistory(params)
      setPriceData(data)

      // Извлекаем уникальные магазины
      const uniqueStores = [...new Set(data.map((item: PriceData) => item.store_name))]
      setStores(uniqueStores)

      // Если еще не выбраны магазины, выбираем все
      if (selectedStores.length === 0 && uniqueStores.length > 0) {
        setSelectedStores(uniqueStores)
      }
    } catch (error) {
      message.error('Не удалось загрузить историю цен')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    if (!gameId) return

    try {
      const params: any = {
        game_id: gameId,
        format: 'csv'
      }

      if (selectedStores.length > 0) {
        params.store_ids = selectedStores
      }

      if (dateRange) {
        params.from = dateRange[0].format('YYYY-MM-DD')
        params.to = dateRange[1].format('YYYY-MM-DD')
      }

      await exportPriceHistory(params)
      message.success('CSV файл успешно загружен')
    } catch (error) {
      message.error('Не удалось экспортировать данные')
    }
  }

  // Подготовка данных для графика
  const chartData = prepareChartData()

  function prepareChartData() {
    const groupedData: { [key: string]: any } = {}

    priceData.forEach(item => {
      const date = dayjs(item.observed_at).format('YYYY-MM-DD')
      if (!groupedData[date]) {
        groupedData[date] = { date }
      }
      groupedData[date][item.store_name] = item.price
    })

    return Object.values(groupedData).sort((a, b) =>
      dayjs(a.date).valueOf() - dayjs(b.date).valueOf()
    )
  }

  // Генерация цветов для линий
  const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#eb2f96', '#fa541c']

  return (
    <Card
      title={`История цен: ${gameTitle}`}
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadPriceHistory}
            loading={loading}
          >
            Обновить
          </Button>
          <Button
            icon={<DownloadOutlined />}
            onClick={handleExport}
            disabled={priceData.length === 0}
          >
            Экспорт CSV
          </Button>
        </Space>
      }
    >
      {/* Фильтры */}
      <Space style={{ marginBottom: 16 }} wrap>
        <div>
          <label style={{ marginRight: 8 }}>Магазины:</label>
          <Select
            mode="multiple"
            placeholder="Выберите магазины"
            style={{ minWidth: 200 }}
            value={selectedStores}
            onChange={setSelectedStores}
          >
            {stores.map(store => (
              <Option key={store} value={store}>{store}</Option>
            ))}
          </Select>
        </div>

        <div>
          <label style={{ marginRight: 8 }}>Период:</label>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            format="DD.MM.YYYY"
          />
        </div>
      </Space>

      {/* График */}
      <Spin spinning={loading}>
        {priceData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart
              data={chartData}
              margin={{
                top: 5,
                right: 30,
                left: 20,
                bottom: 5,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) => dayjs(value).format('DD.MM.YY')}
              />
              <YAxis
                tickFormatter={(value) => `${value} ₽`}
              />
              <Tooltip
                labelFormatter={(value) => dayjs(value).format('DD.MM.YYYY')}
                formatter={(value: any, name: any) => [`${value} ₽`, name]}
              />
              <Legend />
              {selectedStores.map((store, index) => (
                <Line
                  key={store}
                  type="monotone"
                  dataKey={store}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls={true}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
            {loading ? 'Загрузка...' : 'Нет данных о ценах за выбранный период'}
          </div>
        )}
      </Spin>
    </Card>
  )
}

export default PriceChart