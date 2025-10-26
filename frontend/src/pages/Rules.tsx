import React, { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Tag,
  Typography,
  Card,
  Tabs,
  Alert,
  Spin
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  BellOutlined,
  EyeOutlined,
  SaveOutlined,
  CloseOutlined
} from '@ant-design/icons'

import RuleBuilder from '../components/RuleBuilder'
import RulePreview from '../components/RulePreview'

const { Title, Text } = Typography
const { TabPane } = Tabs

interface Condition {
  id: string
  field: string
  operator: string
  value: any
  enabled: boolean
}

interface AlertRule {
  id: string
  name: string
  logic: 'AND' | 'OR'
  conditions: Condition[]
  channels: string[]
  cooldownHours: number
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
        {
          id: 'condition-1-1',
          field: 'game',
          operator: 'in',
          value: ['Громкое дело', 'Gromkoe Delo'],
          enabled: true
        },
        {
          id: 'condition-1-2',
          field: 'title',
          operator: 'contains_any',
          value: ['предзаказ', 'в продаже'],
          enabled: true
        }
      ],
      channels: ['webpush', 'telegram'],
      cooldownHours: 12,
      enabled: true,
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: '2',
      name: 'Скидки 20%+ в основных магазинах',
      logic: 'AND',
      conditions: [
        {
          id: 'condition-2-1',
          field: 'discount_pct',
          operator: '>=',
          value: 20,
          enabled: true
        },
        {
          id: 'condition-2-2',
          field: 'store_id',
          operator: 'in',
          value: ['lavkaigr', 'hobbygames'],
          enabled: true
        }
      ],
      channels: ['webpush'],
      cooldownHours: 6,
      enabled: true,
      created_at: '2024-01-10T14:20:00Z'
    }
  ])

  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState<AlertRule | null>(null)
  const [currentRuleData, setCurrentRuleData] = useState<AlertRule | null>(null)
  const [activeTab, setActiveTab] = useState('builder')
  const [testLoading, setTestLoading] = useState(false)
  const [testResults, setTestResults] = useState<any[]>([])

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
      render: (conditions: Condition[]) => (
        <div>
          {conditions.map((condition, index) => (
            <Tag key={condition.id} style={{ marginBottom: '4px' }} color={!condition.enabled ? 'default' : 'blue'}>
              {condition.field} {condition.operator} {Array.isArray(condition.value) ? condition.value.join(', ') : condition.value}
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
      dataIndex: 'cooldownHours',
      key: 'cooldownHours',
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
    setCurrentRuleData(null)
    setActiveTab('builder')
    setTestResults([])
    setModalVisible(true)
  }

  const handleEdit = (rule: AlertRule) => {
    setEditingRule(rule)
    setCurrentRuleData({ ...rule })
    setActiveTab('builder')
    setTestResults([])
    setModalVisible(true)
  }

  const handleDelete = (id: string) => {
    setRules(rules.filter(rule => rule.id !== id))
  }

  const handleTest = async () => {
    if (!currentRuleData || !currentRuleData.conditions.length) {
      return
    }

    setTestLoading(true)
    try {
      // Симуляция запроса к API для тестирования правила
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Генерация тестовых событий
      const mockEvents = [
        {
          id: '1',
          game_title: 'Громкое дело',
          title: 'Предзаказ на Громкое дело стартовал!',
          price: 2990,
          discount_pct: 0,
          store_id: 'hobbygames',
          kind: 'preorder',
          in_stock: false,
          publisher: 'Студия "Игромаг"',
          tags: ['стратегия', 'партия'],
          created_at: new Date().toISOString()
        },
        {
          id: '2',
          game_title: 'Dune: Империум',
          title: 'Большая скидка 25% на Dune: Империум',
          price: 2250,
          discount_pct: 25,
          store_id: 'lavkaigr',
          kind: 'discount',
          in_stock: true,
          publisher: 'Galaxy Games',
          tags: ['стратегия', 'научная фантастика'],
          created_at: new Date().toISOString()
        }
      ]

      setTestResults(mockEvents)
    } catch (error) {
      console.error('Error testing rule:', error)
    } finally {
      setTestLoading(false)
    }
  }

  const handleRuleChange = (ruleData: AlertRule) => {
    setCurrentRuleData(ruleData)
  }

  const handleSaveRule = () => {
    if (!currentRuleData) {
      return
    }

    if (editingRule) {
      // Редактирование
      setRules(rules.map(rule =>
        rule.id === editingRule.id
          ? { ...currentRuleData, updated_at: new Date().toISOString() }
          : rule
      ))
    } else {
      // Добавление
      const newRule: AlertRule = {
        ...currentRuleData,
        id: Date.now().toString(),
        created_at: new Date().toISOString()
      }
      setRules([...rules, newRule])
    }

    setModalVisible(false)
    setCurrentRuleData(null)
    setTestResults([])
  }

  const handlePreviewTab = () => {
    setActiveTab('preview')
  }

  const handleBuilderTab = () => {
    setActiveTab('builder')
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
        onCancel={() => setModalVisible(false)}
        width={1200}
        footer={[
          <Button key="cancel" icon={<CloseOutlined />} onClick={() => setModalVisible(false)}>
            Отмена
          </Button>,
          <Button key="save" type="primary" icon={<SaveOutlined />} onClick={handleSaveRule} disabled={!currentRuleData}>
            Сохранить
          </Button>
        ]}
      >
        <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key)}>
          <TabPane tab="Конструктор" key="builder">
            <Alert
              message="Конструктор правил"
              description="Создайте сложные правила с помощью визуального конструктора. Перетаскивайте условия, настраивайте поля и операторы."
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />

            <RuleBuilder
              rule={currentRuleData || undefined}
              onChange={handleRuleChange}
              onTest={handleTest}
              onPreview={handlePreviewTab}
              showPreview={true}
            />
          </TabPane>

          <TabPane
            tab={
              <span>
                <EyeOutlined />
                Предпросмотр
              </span>
            }
            key="preview"
          >
            {currentRuleData ? (
              <Spin spinning={testLoading}>
                <RulePreview
                  rule={currentRuleData}
                  testEvents={testResults}
                  onTest={handleTest}
                  loading={testLoading}
                />
              </Spin>
            ) : (
              <Alert
                message="Нет данных для предпросмотра"
                description="Сначала настройте правило во вкладке 'Конструктор'"
                type="warning"
                showIcon
              />
            )}
          </TabPane>
        </Tabs>
      </Modal>
    </div>
  )
}

export default Rules