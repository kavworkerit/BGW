import React, { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Tag,
  Typography,
  Card,
  Row,
  Col,
  InputNumber
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  BellOutlined
} from '@ant-design/icons'

const { Title, Text } = Typography
const { Option } = Select

interface AlertRule {
  id: string
  name: string
  logic: 'AND' | 'OR'
  conditions: any[]
  channels: string[]
  cooldown_hours: number
  enabled: boolean
  created_at: string
}

const Rules: React.FC = () => {
  const [rules, setRules] = useState<AlertRule[]>([
    {
      id: '1',
      name: 'Громкое дело - предзаказ/релиз',
      logic: 'OR',
      conditions: [
        { field: 'game', op: 'in', value: ['Громкое дело', 'Gromkoe Delo'] },
        { field: 'title', op: 'contains_any', value: ['предзаказ', 'в продаже'] }
      ],
      channels: ['webpush', 'telegram'],
      cooldown_hours: 12,
      enabled: true,
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: '2',
      name: 'Скидки 20%+ в основных магазинах',
      logic: 'AND',
      conditions: [
        { field: 'discount_pct', op: '>=', value: 20 },
        { field: 'store_id', op: 'in', value: ['lavkaigr', 'hobbygames'] }
      ],
      channels: ['webpush'],
      cooldown_hours: 6,
      enabled: true,
      created_at: '2024-01-10T14:20:00Z'
    }
  ])

  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => <strong>{name}</strong>
    },
    {
      title: 'Логика',
      dataIndex: 'logic',
      key: 'logic',
      render: (logic: string) => (
        <Tag color={logic === 'AND' ? 'blue' : 'green'}>
          {logic === 'AND' ? 'И' : 'ИЛИ'}
        </Tag>
      )
    },
    {
      title: 'Условия',
      dataIndex: 'conditions',
      key: 'conditions',
      render: (conditions: any[]) => (
        <div>
          {conditions.map((condition, index) => (
            <Tag key={index} style={{ marginBottom: '4px' }}>
              {condition.field} {condition.op} {Array.isArray(condition.value) ? condition.value.join(', ') : condition.value}
            </Tag>
          ))}
        </div>
      )
    },
    {
      title: 'Каналы',
      dataIndex: 'channels',
      key: 'channels',
      render: (channels: string[]) => (
        <Space>
          {channels.map(channel => (
            <Tag key={channel} color="purple">
              {channel === 'webpush' ? 'Web Push' : 'Telegram'}
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Перезарядка',
      dataIndex: 'cooldown_hours',
      key: 'cooldown_hours',
      render: (hours: number) => `${hours} ч`
    },
    {
      title: 'Статус',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'}>
          {enabled ? 'Включено' : 'Выключено'}
        </Tag>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record: AlertRule) => (
        <Space>
          <Button
            type="text"
            icon={<PlayCircleOutlined />}
            onClick={() => handleTest(record.id)}
            disabled={!record.enabled}
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
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

  const handleAdd = () => {
    setEditingRule(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (rule: AlertRule) => {
    setEditingRule(rule)
    form.setFieldsValue(rule)
    setModalVisible(true)
  }

  const handleDelete = (id: string) => {
    setRules(rules.filter(rule => rule.id !== id))
  }

  const handleTest = (id: string) => {
    // Здесь будет тестирование правила
    console.log('Test rule:', id)
  }

  const handleModalOk = () => {
    form.validateFields().then(values => {
      if (editingRule) {
        // Редактирование
        setRules(rules.map(rule =>
          rule.id === editingRule.id
            ? { ...rule, ...values }
            : rule
        ))
      } else {
        // Добавление
        const newRule: AlertRule = {
          id: Date.now().toString(),
          ...values,
          created_at: new Date().toISOString()
        }
        setRules([...rules, newRule])
      }
      setModalVisible(false)
      form.resetFields()
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Правила уведомлений</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Создать правило
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={rules}
        rowKey="id"
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} правил`
        }}
      />

      <Modal
        title={editingRule ? 'Редактировать правило' : 'Создать правило'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            logic: 'AND',
            conditions: [{}],
            channels: ['webpush'],
            cooldown_hours: 12,
            enabled: true
          }}
        >
          <Form.Item
            name="name"
            label="Название правила"
            rules={[{ required: true, message: 'Введите название правила' }]}
          >
            <Input placeholder="Например: Скидки на стратегические игры" />
          </Form.Item>

          <Form.Item
            name="logic"
            label="Логика условий"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="AND">И (все условия должны быть выполнены)</Option>
              <Option value="OR">ИЛИ (хотя бы одно условие должно быть выполнено)</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="channels"
            label="Каналы уведомлений"
            rules={[{ required: true, message: 'Выберите хотя бы один канал' }]}
          >
            <Select mode="multiple" placeholder="Выберите каналы">
              <Option value="webpush">Web Push</Option>
              <Option value="telegram">Telegram</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="cooldown_hours"
            label="Перезарядка (часы)"
            rules={[{ required: true, type: 'number', min: 1 }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              max={168}
              placeholder="Минимальный интервал между уведомлениями"
            />
          </Form.Item>

          <Form.Item
            name="enabled"
            label="Включено"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Rules