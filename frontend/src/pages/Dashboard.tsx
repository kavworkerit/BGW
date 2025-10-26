import React from 'react'
import { Row, Col, Card, Statistic, List, Tag, Typography } from 'antd'
import {
  DatabaseOutlined,
  RobotOutlined,
  BellOutlined,
  CalendarOutlined,
  TrendingUpOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography

const Dashboard: React.FC = () => {
  // Mock данные - в реальном приложении здесь будут запросы к API
  const stats = [
    {
      title: 'Игр в отслеживании',
      value: 42,
      icon: <DatabaseOutlined />,
      color: '#1890ff'
    },
    {
      title: 'Активных агентов',
      value: 8,
      icon: <RobotOutlined />,
      color: '#52c41a'
    },
    {
      title: 'Событий сегодня',
      value: 15,
      icon: <CalendarOutlined />,
      color: '#fa8c16'
    },
    {
      title: 'Активных правил',
      value: 6,
      icon: <BellOutlined />,
      color: '#eb2f96'
    }
  ]

  const recentEvents = [
    {
      title: 'Громкое дело - предзаказ',
      store: 'Hobby Games',
      price: '2 990 ₽',
      discount: null,
      time: '2 часа назад',
      type: 'preorder'
    },
    {
      title: 'Dune: Imperium - скидка 20%',
      store: 'Лавка Игр',
      price: '3 590 ₽',
      discount: '20%',
      time: '3 часа назад',
      type: 'discount'
    },
    {
      title: 'Root: Маршал',
      store: 'Nastol.io',
      price: '1 890 ₽',
      discount: null,
      time: '5 часов назад',
      type: 'release'
    }
  ]

  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      'preorder': 'blue',
      'discount': 'red',
      'release': 'green',
      'announce': 'orange'
    }
    return colors[type] || 'default'
  }

  const getTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      'preorder': 'Предзаказ',
      'discount': 'Скидка',
      'release': 'Релиз',
      'announce': 'Анонс'
    }
    return labels[type] || type
  }

  return (
    <div>
      <Title level={2}>Дашборд</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card className="stats-card">
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
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
                        {item.title}
                        <Tag color={getTypeColor(item.type)}>
                          {getTypeLabel(item.type)}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space split={<span>•</span>}>
                        <Text>{item.store}</Text>
                        <Text className="event-price">{item.price}</Text>
                        {item.discount && (
                          <Text className="event-discount">
                            -{item.discount}
                          </Text>
                        )}
                        <Text type="secondary">{item.time}</Text>
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
              dataSource={[
                { name: 'Hobby Games', status: 'Активен', lastRun: '10 мин назад' },
                { name: 'Лавка Игр', status: 'Активен', lastRun: '25 мин назад' },
                { name: 'Nastol.io', status: 'Ошибка', lastRun: '2 часа назад' },
                { name: 'CrowdGames', status: 'Активен', lastRun: '1 час назад' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={item.name}
                    description={
                      <Space split={<span>•</span>}>
                        <Text type={item.status === 'Активен' ? 'success' : 'danger'}>
                          {item.status}
                        </Text>
                        <Text type="secondary">{item.lastRun}</Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard