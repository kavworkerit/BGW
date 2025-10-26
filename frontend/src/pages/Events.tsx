import React, { useState } from 'react'
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
  Col
} from 'antd'
import {
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  EyeOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker
const { Search } = Input

interface Event {
  id: string
  title: string
  game_name?: string
  store_name: string
  kind: 'announce' | 'preorder' | 'release' | 'discount' | 'price'
  price?: number
  currency?: string
  discount_pct?: number
  in_stock?: boolean
  url?: string
  created_at: string
}

const Events: React.FC = () => {
  const [events] = useState<Event[]>([
    {
      id: '1',
      title: 'Громкое дело - предзаказ открыт',
      game_name: 'Громкое дело',
      store_name: 'Hobby Games',
      kind: 'preorder',
      price: 2990,
      currency: 'RUB',
      in_stock: true,
      url: 'https://hobbygames.ru/gromkoe-delo',
      created_at: '2024-01-20T10:30:00Z'
    },
    {
      id: '2',
      title: 'Dune: Imperium - скидка 20%',
      game_name: 'Dune: Imperium',
      store_name: 'Лавка Игр',
      kind: 'discount',
      price: 3590,
      currency: 'RUB',
      discount_pct: 20,
      in_stock: true,
      url: 'https://lavkaigr.ru/dune-imperium',
      created_at: '2024-01-20T09:15:00Z'
    },
    {
      id: '3',
      title: 'Root: Маршал теперь в наличии',
      game_name: 'Root: Маршал',
      store_name: 'Nastol.io',
      kind: 'release',
      price: 1890,
      currency: 'RUB',
      in_stock: true,
      url: 'https://nastol.io/root-marshals',
      created_at: '2024-01-20T08:45:00Z'
    }
  ])

  const columns = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Event) => (
        <div>
          <strong>{title}</strong>
          {record.game_name && (
            <div>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Игра: {record.game_name}
              </Text>
            </div>
          )}
        </div>
      )
    },
    {
      title: 'Тип',
      dataIndex: 'kind',
      key: 'kind',
      render: (kind: string) => {
        const typeConfig: Record<string, { label: string; color: string }> = {
          'announce': { label: 'Анонс', color: 'blue' },
          'preorder': { label: 'Предзаказ', color: 'purple' },
          'release': { label: 'Релиз', color: 'green' },
          'discount': { label: 'Скидка', color: 'red' },
          'price': { label: 'Цена', color: 'orange' }
        }
        const config = typeConfig[kind] || { label: kind, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      }
    },
    {
      title: 'Магазин',
      dataIndex: 'store_name',
      key: 'store_name'
    },
    {
      title: 'Цена',
      key: 'price',
      render: (_, record: Event) => (
        <div>
          {record.price && (
            <div>
              <Text strong>
                {new Intl.NumberFormat('ru-RU', {
                  style: 'currency',
                  currency: record.currency || 'RUB',
                  minimumFractionDigits: 0
                }).format(record.price)}
              </Text>
              {record.discount_pct && (
                <Tag color="red" style={{ marginLeft: '8px' }}>
                  -{record.discount_pct}%
                </Tag>
              )}
            </div>
          )}
          {record.in_stock !== undefined && (
            <Tag color={record.in_stock ? 'success' : 'default'} style={{ marginTop: '4px' }}>
              {record.in_stock ? 'В наличии' : 'Нет в наличии'}
            </Tag>
          )}
        </div>
      )
    },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <div>
          <div>{dayjs(date).format('DD.MM.YYYY')}</div>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {dayjs(date).format('HH:mm')}
          </Text>
        </div>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record: Event) => (
        <Space>
          {record.url && (
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => window.open(record.url, '_blank')}
            />
          )}
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>События</Title>
        <Button icon={<ExportOutlined />}>
          Экспорт
        </Button>
      </div>

      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <Search
              placeholder="Поиск по названию"
              allowClear
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Тип события"
              style={{ width: '100%' }}
              allowClear
            >
              <Select.Option value="announce">Анонс</Select.Option>
              <Select.Option value="preorder">Предзаказ</Select.Option>
              <Select.Option value="release">Релиз</Select.Option>
              <Select.Option value="discount">Скидка</Select.Option>
              <Select.Option value="price">Цена</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Select
              placeholder="Магазин"
              style={{ width: '100%' }}
              allowClear
            >
              <Select.Option value="hobbygames">Hobby Games</Select.Option>
              <Select.Option value="lavkaigr">Лавка Игр</Select.Option>
              <Select.Option value="nastolio">Nastol.io</Select.Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <RangePicker
              style={{ width: '100%' }}
              placeholder={['Начальная дата', 'Конечная дата']}
              format="DD.MM.YYYY"
            />
          </Col>
          <Col xs={24} sm={12} md={4}>
            <Button icon={<FilterOutlined />}>
              Фильтры
            </Button>
          </Col>
        </Row>
      </Card>

      <Table
        columns={columns}
        dataSource={events}
        rowKey="id"
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} событий`,
          defaultPageSize: 20
        }}
      />
    </div>
  )
}

export default Events