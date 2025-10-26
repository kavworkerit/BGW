import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Switch,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Input,
  Form,
  Alert,
  Badge,
  List,
  Tag,
  TimePicker,
  Select,
  message
} from 'antd'
import {
  BellOutlined,
  SendOutlined,
  SettingOutlined,
  MobileOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import dayjs from 'dayjs'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

interface NotificationSettings {
  webpush: {
    enabled: boolean
    vapidPublicKey: string
    vapidPrivateKey: string
    vapidEmail: string
  }
  telegram: {
    enabled: boolean
    botToken: string
    chatId: string
  }
  global: {
    quietHours: {
      enabled: boolean
      start: string
      end: string
    }
    maxNotifications: number
    cooldownMinutes: number
  }
}

interface NotificationHistory {
  id: string
  channel: 'webpush' | 'telegram'
  title: string
  message: string
  status: 'sent' | 'failed' | 'pending'
  timestamp: string
  rule?: string
}

const Notifications: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [settings, setSettings] = useState<NotificationSettings | null>(null)
  const [history, setHistory] = useState<NotificationHistory[]>([])
  const [subscribeLoading, setSubscribeLoading] = useState(false)
  const [isSubscribed, setIsSubscribed] = useState(false)

  // Моковые данные для демонстрации
  const mockSettings: NotificationSettings = {
    webpush: {
      enabled: true,
      vapidPublicKey: 'BMxFTcQkq3fE8vYJ0V6j7n8p5q2r4w1s6a9z8x3c7v2b1n6m5k4j3h2g1f9d8s7',
      vapidPrivateKey: 'your-private-key',
      vapidEmail: 'admin@example.com'
    },
    telegram: {
      enabled: false,
      botToken: '',
      chatId: ''
    },
    global: {
      quietHours: {
        enabled: true,
        start: '22:00',
        end: '08:00'
      },
      maxNotifications: 50,
      cooldownMinutes: 15
    }
  }

  const mockHistory: NotificationHistory[] = [
    {
      id: '1',
      channel: 'webpush',
      title: 'Громкое дело - Скидка 25%',
      message: 'В магазине Hobby Games скидка 25% на игру Громкое дело. Новая цена: 2175₽',
      status: 'sent',
      timestamp: '2024-01-20T14:30:00Z',
      rule: 'Скидки > 20%'
    },
    {
      id: '2',
      channel: 'telegram',
      title: 'Dune: Imperium - Релиз',
      message: 'Игра Dune: Imperium поступила в продажу в магазине Лавка Игр',
      status: 'sent',
      timestamp: '2024-01-20T12:15:00Z',
      rule: 'Релизы отслеживаемых игр'
    },
    {
      id: '3',
      channel: 'webpush',
      title: 'Монополия - Предзаказ',
      message: 'Открыт предзаказ на новое издание Монополии',
      status: 'failed',
      timestamp: '2024-01-20T10:45:00Z',
      rule: 'Предзаказы'
    },
    {
      id: '4',
      channel: 'webpush',
      title: 'Эволюция - Снижение цены',
      message: 'Цена на игру Эволюция снижена на 15% в магазине Nastol.io',
      status: 'pending',
      timestamp: '2024-01-20T09:20:00Z',
      rule: 'Снижение цен > 10%'
    }
  ]

  useEffect(() => {
    loadSettings()
    loadHistory()
    checkWebPushSubscription()
  }, [])

  const loadSettings = async () => {
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch('/api/settings/notifications')
      // const data = await response.json()

      // Используем моковые данные
      setSettings(mockSettings)
      form.setFieldsValue(mockSettings)
    } catch (error) {
      message.error('Ошибка загрузки настроек')
    }
  }

  const loadHistory = async () => {
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch('/api/notifications/history')
      // const data = await response.json()

      // Используем моковые данные
      setHistory(mockHistory)
    } catch (error) {
      message.error('Ошибка загрузки истории уведомлений')
    }
  }

  const checkWebPushSubscription = async () => {
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()
      setIsSubscribed(!!subscription)
    } catch (error) {
      console.log('Web Push не поддерживается или не настроен')
    }
  }

  const handleSaveSettings = async (values: NotificationSettings) => {
    setLoading(true)
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch('/api/settings/notifications', {
      //   method: 'PUT',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(values)
      // })

      // if (response.ok) {
        setSettings(values)
        message.success('Настройки сохранены')
      // } else {
      //   message.error('Ошибка сохранения настроек')
      // }
    } catch (error) {
      message.error('Ошибка сохранения настроек')
    } finally {
      setLoading(false)
    }
  }

  const handleTestWebPush = async () => {
    setTestLoading(true)
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch('/api/notifications/test/webpush', {
      //   method: 'POST'
      // })

      // if (response.ok) {
        message.success('Тестовое уведомление отправлено')
      // } else {
      //   message.error('Ошибка отправки тестового уведомления')
      // }
    } catch (error) {
      message.error('Ошибка отправки тестового уведомления')
    } finally {
      setTestLoading(false)
    }
  }

  const handleTestTelegram = async () => {
    setTestLoading(true)
    try {
      // В реальном приложении здесь будет API запрос
      // const response = await fetch('/api/notifications/test/telegram', {
      //   method: 'POST'
      // })

      // if (response.ok) {
        message.success('Тестовое сообщение в Telegram отправлено')
      // } else {
      //   message.error('Ошибка отправки тестового сообщения')
      // }
    } catch (error) {
      message.error('Ошибка отправки тестового сообщения')
    } finally {
      setTestLoading(false)
    }
  }

  const handleSubscribeWebPush = async () => {
    setSubscribeLoading(true)
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: settings?.webpush.vapidPublicKey
      })

      // В реальном приложении здесь будет API запрос для сохранения подписки
      // await fetch('/api/webpush/subscribe', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(subscription)
      // })

      setIsSubscribed(true)
      message.success('Подписка на Web Push уведомления оформлена')
    } catch (error) {
      message.error('Ошибка оформления подписки на Web Push')
    } finally {
      setSubscribeLoading(false)
    }
  }

  const handleUnsubscribeWebPush = async () => {
    try {
      const registration = await navigator.serviceWorker.ready
      const subscription = await registration.pushManager.getSubscription()

      if (subscription) {
        await subscription.unsubscribe()

        // В реальном приложении здесь будет API запрос для удаления подписки
        // await fetch('/api/webpush/unsubscribe', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({ endpoint: subscription.endpoint })
        // })

        setIsSubscribed(false)
        message.success('Подписка на Web Push уведомления отменена')
      }
    } catch (error) {
      message.error('Ошибка отмены подписки на Web Push')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'sent': return 'success'
      case 'failed': return 'error'
      case 'pending': return 'warning'
      default: return 'default'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'sent': return 'Отправлено'
      case 'failed': return 'Ошибка'
      case 'pending': return 'В очереди'
      default: return 'Неизвестно'
    }
  }

  return (
    <div>
      <Title level={2}>Уведомления</Title>

      <Row gutter={24}>
        <Col span={16}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSaveSettings}
            initialValues={settings}
          >
            {/* Web Push настройки */}
            <Card
              title={
                <Space>
                  <MobileOutlined />
                  Web Push уведомления
                </Space>
              }
              extra={
                <Space>
                  <Badge status={isSubscribed ? 'success' : 'default'} text={isSubscribed ? 'Подписан' : 'Не подписан'} />
                  <Button
                    type={isSubscribed ? 'default' : 'primary'}
                    size="small"
                    onClick={isSubscribed ? handleUnsubscribeWebPush : handleSubscribeWebPush}
                    loading={subscribeLoading}
                  >
                    {isSubscribed ? 'Отписаться' : 'Подписаться'}
                  </Button>
                </Space>
              }
            >
              <Form.Item
                name={['webpush', 'enabled']}
                label="Включить Web Push уведомления"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Alert
                message="Web Push уведомления"
                description="Для получения Web Push уведомлений необходимо подписаться в браузере. Убедитесь, что у вас разрешены уведомления для этого сайта."
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                name={['webpush', 'vapidEmail']}
                label="Email для VAPID ключей"
                rules={[{ type: 'email', message: 'Введите корректный email' }]}
              >
                <Input placeholder="admin@example.com" />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<CheckCircleOutlined />}
                >
                  Сохранить настройки
                </Button>
                <Button
                  onClick={handleTestWebPush}
                  loading={testLoading}
                  icon={<SendOutlined />}
                >
                  Тестовое уведомление
                </Button>
              </Space>
            </Card>

            {/* Telegram настройки */}
            <Card
              title={
                <Space>
                  <MessageOutlined />
                  Telegram уведомления
                </Space>
              }
              style={{ marginTop: 24 }}
            >
              <Form.Item
                name={['telegram', 'enabled']}
                label="Включить Telegram уведомления"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name={['telegram', 'botToken']}
                label="Bot Token"
                rules={[
                  { required: true, message: 'Введите Bot Token' },
                  { len: 46, message: 'Bot Token должен содержать 46 символов' }
                ]}
              >
                <Input.Password placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz" />
              </Form.Item>

              <Form.Item
                name={['telegram', 'chatId']}
                label="Chat ID"
                rules={[{ required: true, message: 'Введите Chat ID' }]}
              >
                <Input placeholder="@your_channel или 123456789" />
              </Form.Item>

              <Paragraph type="secondary" style={{ fontSize: '12px' }}>
                Для получения Chat ID можно отправить сообщение боту @userinfobot или @RawDataBot
              </Paragraph>

              <Space>
                <Button
                  type="primary"
                  htmlType="submit"
                  loading={loading}
                  icon={<CheckCircleOutlined />}
                >
                  Сохранить настройки
                </Button>
                <Button
                  onClick={handleTestTelegram}
                  loading={testLoading}
                  icon={<SendOutlined />}
                >
                  Тестовое сообщение
                </Button>
              </Space>
            </Card>

            {/* Глобальные настройки */}
            <Card
              title={
                <Space>
                  <SettingOutlined />
                  Глобальные настройки
                </Space>
              }
              style={{ marginTop: 24 }}
            >
              <Form.Item
                name={['global', 'quietHours', 'enabled']}
                label="Тихие часы"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name={['global', 'quietHours', 'start']}
                    label="Начало тихих часов"
                  >
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      placeholder="22:00"
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name={['global', 'quietHours', 'end']}
                    label="Конец тихих часов"
                  >
                    <TimePicker
                      format="HH:mm"
                      style={{ width: '100%' }}
                      placeholder="08:00"
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item
                name={['global', 'maxNotifications']}
                label="Максимум уведомлений в день"
              >
                <Input type="number" placeholder="50" />
              </Form.Item>

              <Form.Item
                name={['global', 'cooldownMinutes']}
                label="Период охлаждения (минуты)"
              >
                <Input type="number" placeholder="15" />
              </Form.Item>

              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<CheckCircleOutlined />}
              >
                Сохранить настройки
              </Button>
            </Card>
          </Form>
        </Col>

        <Col span={8}>
          <Card title="История уведомлений" size="small">
            <List
              dataSource={history.slice(0, 10)}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      item.channel === 'webpush' ? (
                        <MobileOutlined style={{ color: '#1890ff' }} />
                      ) : (
                        <MessageOutlined style={{ color: '#0088cc' }} />
                      )
                    }
                    title={
                      <Space>
                        <Text strong>{item.title}</Text>
                        <Tag color={getStatusColor(item.status)}>
                          {getStatusText(item.status)}
                        </Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <div style={{ fontSize: '12px', marginBottom: 4 }}>
                          {item.message}
                        </div>
                        <div style={{ fontSize: '11px', color: '#999' }}>
                          {dayjs(item.timestamp).format('DD.MM.YYYY HH:mm')}
                          {item.rule && ` • ${item.rule}`}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>

          <Card title="Статистика" size="small" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Отправлено сегодня:</Text>
                <Text strong>12</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Ошибок сегодня:</Text>
                <Text strong style={{ color: '#f5222d' }}>2</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>В очереди:</Text>
                <Text strong style={{ color: '#faad14' }}>3</Text>
              </div>
              <Divider />
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Web Push подписчики:</Text>
                <Text strong>1</Text>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <Text>Telegram чаты:</Text>
                <Text strong>0</Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Notifications