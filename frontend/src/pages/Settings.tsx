import React, { useState } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Switch,
  Typography,
  Tabs,
  Space,
  message,
  Divider
} from 'antd'
import {
  SaveOutlined,
  BellOutlined,
  KeyOutlined,
  DatabaseOutlined,
  RobotOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography
const { TabPane } = Tabs

const Settings: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [form] = Form.useForm()

  const handleSave = async (section: string) => {
    setLoading(true)
    try {
      // Здесь будет сохранение настроек
      await new Promise(resolve => setTimeout(resolve, 1000))
      message.success(`Настройки ${section} сохранены`)
    } catch (error) {
      message.error('Ошибка сохранения настроек')
    } finally {
      setLoading(false)
    }
  }

  const testNotification = (type: string) => {
    message.info(`Отправка тестового уведомления через ${type}`)
    // Здесь будет отправка тестового уведомления
  }

  return (
    <div>
      <Title level={2}>Настройки</Title>

      <Tabs defaultActiveKey="notifications">
        <TabPane tab={<span><BellOutlined />Уведомления</span>} key="notifications">
          <Card title="Настройки уведомлений">
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                webpush_enabled: true,
                telegram_enabled: false,
                quiet_hours_enabled: true,
                quiet_hours_start: '22:00',
                quiet_hours_end: '09:00'
              }}
            >
              <Form.Item
                name="webpush_enabled"
                label="Web Push уведомления"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="telegram_enabled"
                label="Telegram уведомления"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Divider />

              <Title level={5}>Тихие часы</Title>
              <Form.Item
                name="quiet_hours_enabled"
                label="Включить тихие часы"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="quiet_hours_start"
                label="Начало тихих часов"
              >
                <Input placeholder="22:00" />
              </Form.Item>

              <Form.Item
                name="quiet_hours_end"
                label="Конец тихих часов"
              >
                <Input placeholder="09:00" />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={loading}
                  onClick={() => handleSave('уведомлений')}
                >
                  Сохранить
                </Button>
                <Button
                  onClick={() => testNotification('webpush')}
                >
                  Тест Web Push
                </Button>
                <Button
                  onClick={() => testNotification('telegram')}
                >
                  Тест Telegram
                </Button>
              </Space>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab={<span><KeyOutlined />Telegram</span>} key="telegram">
          <Card title="Настройки Telegram бота">
            <Form
              layout="vertical"
              initialValues={{
                telegram_bot_token: '',
                telegram_chat_id: ''
              }}
            >
              <Form.Item
                name="telegram_bot_token"
                label="Токен бота"
                rules={[{ required: true, message: 'Введите токен бота' }]}
              >
                <Input.Password placeholder="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11" />
              </Form.Item>

              <Form.Item
                name="telegram_chat_id"
                label="Chat ID"
                rules={[{ required: true, message: 'Введите Chat ID' }]}
              >
                <Input placeholder="123456789" />
              </Form.Item>

              <Space>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  loading={loading}
                  onClick={() => handleSave('telegram')}
                >
                  Сохранить
                </Button>
                <Button
                  onClick={() => testNotification('telegram')}
                >
                  Тестовое уведомление
                </Button>
              </Space>

              <Divider />

              <Title level={5}>Инструкция по настройке</Title>
              <ol>
                <li>Создайте бота через @BotFather в Telegram</li>
                <li>Получите токен бота и вставьте в поле выше</li>
                <li>Найдите свой Chat ID: отправьте сообщение @userinfobot</li>
                <li>Вставьте Chat ID в соответствующее поле</li>
                <li>Нажмите "Тестовое уведомление" для проверки</li>
              </ol>
            </Form>
          </Card>
        </TabPane>

        <TabPane tab={<span><DatabaseOutlined />База данных</span>} key="database">
          <Card title="Управление базой данных">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Title level={5}>Резервное копирование</Title>
                <Text>Последний бэкап: 20.01.2024 10:30</Text>
                <div style={{ marginTop: '8px' }}>
                  <Button>Создать бэкап</Button>
                  <Button style={{ marginLeft: '8px' }}>Скачать бэкап</Button>
                </div>
              </div>

              <Divider />

              <div>
                <Title level={5}>Импорт/Экспорт</Title>
                <Space>
                  <Button>Экспорт всех данных</Button>
                  <Button>Импорт из бэкапа</Button>
                </Space>
              </div>

              <Divider />

              <div>
                <Title level={5}>Очистка данных</Title>
                <Text type="secondary">
                  Автоматическая очистка данных старше 2 лет включена
                </Text>
                <div style={{ marginTop: '8px' }}>
                  <Button danger>Очистить старые данные</Button>
                </div>
              </div>
            </Space>
          </Card>
        </TabPane>

        <TabPane tab={<span><RobotOutlined />Агенты</span>} key="agents">
          <Card title="Настройки агентов">
            <Form
              layout="vertical"
              initialValues={{
                max_daily_pages: 1000,
                default_rps: 0.3,
                default_burst: 1,
                ollama_url: 'http://localhost:11434'
              }}
            >
              <Title level={5}>Общие ограничения</Title>

              <Form.Item
                name="max_daily_pages"
                label="Максимальное количество страниц в день"
              >
                <Input type="number" />
              </Form.Item>

              <Form.Item
                name="default_rps"
                label="Запросов в секунду по умолчанию"
              >
                <Input type="number" step="0.1" />
              </Form.Item>

              <Form.Item
                name="default_burst"
                label="Всплеск запросов по умолчанию"
              >
                <Input type="number" />
              </Form.Item>

              <Divider />

              <Title level={5}>Ollama (LLM)</Title>

              <Form.Item
                name="ollama_enabled"
                label="Использовать Ollama для обработки"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>

              <Form.Item
                name="ollama_url"
                label="URL Ollama сервера"
              >
                <Input placeholder="http://localhost:11434" />
              </Form.Item>

              <Form.Item
                name="ollama_model"
                label="Модель"
              >
                <Input placeholder="llama2" />
              </Form.Item>

              <Button
                type="primary"
                icon={<SaveOutlined />}
                loading={loading}
                onClick={() => handleSave('агентов')}
              >
                Сохранить
              </Button>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default Settings