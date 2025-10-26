import React, { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Tag,
  Typography,
  Progress,
  Upload,
  message
} from 'antd'
import {
  PlusOutlined,
  PlayCircleOutlined,
  UploadOutlined,
  DownloadOutlined,
  EditOutlined,
  DeleteOutlined,
  SettingOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography

interface Agent {
  id: string
  name: string
  type: 'api' | 'html' | 'headless' | 'telegram_public'
  schedule: string
  status: 'active' | 'inactive' | 'error'
  last_run: string
  daily_usage: number
  daily_limit: number
  success_rate: number
}

const Agents: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([
    {
      id: 'hobbygames_coming_soon',
      name: 'Hobby Games - Coming Soon',
      type: 'html',
      schedule: '0 */2 * * *',
      status: 'active',
      last_run: '10 минут назад',
      daily_usage: 45,
      daily_limit: 50,
      success_rate: 95
    },
    {
      id: 'lavkaigr_shop',
      name: 'Лавка Игр - Магазин',
      type: 'html',
      schedule: '0 */4 * * *',
      status: 'active',
      last_run: '25 минут назад',
      daily_usage: 32,
      daily_limit: 80,
      success_rate: 88
    },
    {
      id: 'nastolio_publications',
      name: 'Nastol.io - Публикации',
      type: 'html',
      schedule: '0 */1 * * *',
      status: 'error',
      last_run: '2 часа назад',
      daily_usage: 15,
      daily_limit: 50,
      success_rate: 65
    }
  ])

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <strong>{name}</strong>
    },
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeLabels: Record<string, { label: string; color: string }> = {
          'api': { label: 'API', color: 'blue' },
          'html': { label: 'HTML', color: 'green' },
          'headless': { label: 'Headless', color: 'orange' },
          'telegram_public': { label: 'Telegram', color: 'purple' }
        }
        const config = typeLabels[type] || { label: type, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      }
    },
    {
      title: 'Расписание',
      dataIndex: 'schedule',
      key: 'schedule',
      render: (schedule: string) => <Text code>{schedule}</Text>
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig: Record<string, { label: string; color: string }> = {
          'active': { label: 'Активен', color: 'success' },
          'inactive': { label: 'Неактивен', color: 'default' },
          'error': { label: 'Ошибка', color: 'error' }
        }
        const config = statusConfig[status] || { label: status, color: 'default' }
        return <Tag color={config.color}>{config.label}</Tag>
      }
    },
    {
      title: 'Последний запуск',
      dataIndex: 'last_run',
      key: 'last_run'
    },
    {
      title: 'Использование лимита',
      key: 'usage',
      render: (_, record: Agent) => (
        <div style={{ width: '120px' }}>
          <Progress
            percent={Math.round((record.daily_usage / record.daily_limit) * 100)}
            size="small"
            status={record.daily_usage >= record.daily_limit ? 'exception' : 'normal'}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.daily_usage}/{record.daily_limit}
          </Text>
        </div>
      )
    },
    {
      title: 'Успешность',
      dataIndex: 'success_rate',
      key: 'success_rate',
      render: (rate: number) => (
        <Text type={rate >= 90 ? 'success' : rate >= 70 ? 'warning' : 'danger'}>
          {rate}%
        </Text>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record: Agent) => (
        <Space>
          <Button
            type="text"
            icon={<PlayCircleOutlined />}
            onClick={() => handleRun(record.id)}
            disabled={record.status === 'error'}
          />
          <Button
            type="text"
            icon={<SettingOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button
            type="text"
            icon={<DownloadOutlined />}
            onClick={() => handleExport(record.id)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      )
    }
  ]

  const handleRun = (id: string) => {
    message.info(`Запуск агента ${id}`)
    // Здесь будет реальный запуск агента
  }

  const handleEdit = (agent: Agent) => {
    message.info(`Редактирование агента ${agent.name}`)
    // Здесь будет открытие модального окна редактирования
  }

  const handleExport = (id: string) => {
    message.info(`Экспорт агента ${id}`)
    // Здесь будет реальный экспорт
  }

  const handleDelete = (id: string) => {
    setAgents(agents.filter(agent => agent.id !== id))
    message.success('Агент удален')
  }

  const handleImport = () => {
    message.info('Импорт агента')
    // Здесь будет реальный импорт
  }

  const uploadProps = {
    name: 'file',
    accept: '.zip',
    showUploadList: false,
    beforeUpload: (file: File) => {
      if (file.type !== 'application/zip') {
        message.error('Файл должен быть в формате ZIP')
        return false
      }
      handleImport()
      return false
    },
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Агенты</Title>
        <Space>
          <Upload {...uploadProps}>
            <Button icon={<UploadOutlined />}>
              Импортировать агента
            </Button>
          </Upload>
          <Button type="primary" icon={<PlusOutlined />}>
            Создать агента
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={agents}
        rowKey="id"
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} агентов`
        }}
      />
    </div>
  )
}

export default Agents