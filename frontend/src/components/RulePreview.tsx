import React from 'react'
import {
  Card,
  Table,
  Tag,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Button
} from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  PlayCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'

const { Text, Title } = Typography

interface Condition {
  field: string
  operator: string
  value: any
  enabled: boolean
}

interface Rule {
  name: string
  logic: 'AND' | 'OR'
  conditions: Condition[]
  channels: string[]
  cooldownHours: number
  enabled: boolean
}

interface MockEvent {
  id: string
  game_title: string
  title: string
  price: number
  discount_pct: number
  store_id: string
  kind: string
  in_stock: boolean
  publisher: string
  tags: string[]
  created_at: string
}

interface RulePreviewProps {
  rule: Rule
  testEvents?: MockEvent[]
  onTest?: () => void
  loading?: boolean
}

const FIELD_LABELS: Record<string, string> = {
  game: 'Игра',
  title: 'Заголовок',
  price: 'Цена',
  discount_pct: 'Скидка',
  store_id: 'Магазин',
  kind: 'Тип',
  in_stock: 'Наличие',
  publisher: 'Издатель',
  tags: 'Теги'
}

const OPERATOR_LABELS: Record<string, string> = {
  'in': 'в списке',
  'contains': 'содержит',
  'contains_any': 'содержит любое',
  'equals': 'равно',
  'starts_with': 'начинается с',
  '>=': '≥',
  '<=': '≤',
  '=': '=',
  'between': 'в диапазоне',
  'contains_all': 'содержит все'
}

const KIND_LABELS: Record<string, string> = {
  announce: 'Анонс',
  preorder: 'Предзаказ',
  release: 'Релиз',
  discount: 'Скидка',
  price: 'Цена'
}

const STORE_LABELS: Record<string, string> = {
  lavkaigr: 'Лавка Игр',
  hobbygames: 'Hobby Games',
  nastolio: 'Nastol.io',
  evrikus: 'Evrikus',
  crowdgames: 'CrowdGames',
  gaga: 'GaGa',
  zvezda: 'Звезда',
  choochoogames: 'ChooChooGames'
}

const RulePreview: React.FC<RulePreviewProps> = ({
  rule,
  testEvents = [],
  onTest,
  loading = false
}) => {
  const evaluateCondition = (event: MockEvent, condition: Condition): boolean => {
    if (!condition.enabled) return true

    const fieldValue = event[condition.field as keyof MockEvent]
    const conditionValue = condition.value

    switch (condition.operator) {
      case 'in':
        return Array.isArray(conditionValue) && conditionValue.includes(fieldValue)
      case 'contains':
        return typeof fieldValue === 'string' &&
               typeof conditionValue === 'string' &&
               fieldValue.toLowerCase().includes(conditionValue.toLowerCase())
      case 'contains_any':
        return Array.isArray(conditionValue) &&
               conditionValue.some((val: string) =>
                 typeof fieldValue === 'string' &&
                 fieldValue.toLowerCase().includes(val.toLowerCase())
               )
      case 'contains_all':
        return Array.isArray(conditionValue) &&
               Array.isArray(fieldValue) &&
               conditionValue.every((val: string) => fieldValue.includes(val))
      case 'equals':
        return fieldValue === conditionValue
      case 'starts_with':
        return typeof fieldValue === 'string' &&
               typeof conditionValue === 'string' &&
               fieldValue.toLowerCase().startsWith(conditionValue.toLowerCase())
      case '>=':
        return typeof fieldValue === 'number' &&
               typeof conditionValue === 'number' &&
               fieldValue >= conditionValue
      case '<=':
        return typeof fieldValue === 'number' &&
               typeof conditionValue === 'number' &&
               fieldValue <= conditionValue
      case 'between':
        return typeof fieldValue === 'number' &&
               Array.isArray(conditionValue) &&
               conditionValue.length === 2 &&
               fieldValue >= conditionValue[0] &&
               fieldValue <= conditionValue[1]
      default:
        return false
    }
  }

  const evaluateRule = (event: MockEvent): boolean => {
    const results = rule.conditions.map(condition => evaluateCondition(event, condition))
    return rule.logic === 'AND' ? results.every(r => r) : results.some(r => r)
  }

  const mockTestEvents: MockEvent[] = testEvents.length > 0 ? testEvents : [
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
      created_at: '2024-01-15T10:30:00Z'
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
      created_at: '2024-01-15T09:15:00Z'
    },
    {
      id: '3',
      game_title: 'Колонизаторы Марса',
      title: 'Новый поступление Колонизаторы Марса',
      price: 4500,
      discount_pct: 10,
      store_id: 'evrikus',
      kind: 'release',
      in_stock: true,
      publisher: 'Stronghold Games',
      tags: ['стратегия', 'экономическая'],
      created_at: '2024-01-15T08:45:00Z'
    }
  ]

  const results = mockTestEvents.map(event => ({
    ...event,
    matches: evaluateRule(event)
  }))

  const matchCount = results.filter(r => r.matches).length
  const totalCount = results.length

  const conditionColumns = [
    {
      title: 'Поле',
      dataIndex: 'field',
      key: 'field',
      render: (field: string) => FIELD_LABELS[field] || field
    },
    {
      title: 'Оператор',
      dataIndex: 'operator',
      key: 'operator',
      render: (operator: string) => OPERATOR_LABELS[operator] || operator
    },
    {
      title: 'Значение',
      dataIndex: 'value',
      key: 'value',
      render: (value: any) => {
        if (Array.isArray(value)) {
          return value.join(', ')
        }
        return value?.toString() || ''
      }
    },
    {
      title: 'Статус',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled: boolean) => (
        <Tag color={enabled ? 'success' : 'default'} icon={enabled ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {enabled ? 'Активно' : 'Отключено'}
        </Tag>
      )
    }
  ]

  const testColumns = [
    {
      title: 'Игра',
      dataIndex: 'game_title',
      key: 'game_title',
      render: (title: string) => <Text strong>{title}</Text>
    },
    {
      title: 'Тип',
      dataIndex: 'kind',
      key: 'kind',
      render: (kind: string) => <Tag>{KIND_LABELS[kind] || kind}</Tag>
    },
    {
      title: 'Магазин',
      dataIndex: 'store_id',
      key: 'store_id',
      render: (storeId: string) => STORE_LABELS[storeId] || storeId
    },
    {
      title: 'Цена',
      dataIndex: 'price',
      key: 'price',
      render: (price: number, record: any) => (
        <div>
          {price} ₽
          {record.discount_pct > 0 && (
            <Tag color="red" style={{ marginLeft: 8 }}>
              -{record.discount_pct}%
            </Tag>
          )}
        </div>
      )
    },
    {
      title: 'Результат',
      dataIndex: 'matches',
      key: 'matches',
      render: (matches: boolean) => (
        <Tag color={matches ? 'success' : 'default'} icon={matches ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {matches ? 'Сработает' : 'Не сработает'}
        </Tag>
      )
    }
  ]

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Всего условий"
              value={rule.conditions.length}
              suffix={rule.conditions.length > 0 && (
                <Text type="secondary">
                  ({rule.conditions.filter(c => c.enabled).length} активных)
                </Text>
              )}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Тип логики"
              value={rule.logic}
              render={(value) => (
                <Tag color={value === 'AND' ? 'blue' : 'green'}>
                  {value === 'AND' ? 'И (все условия)' : 'ИЛИ (хотя бы одно)'}
                </Tag>
              )}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Каналы уведомлений"
              value={rule.channels.length}
              render={() => (
                <Space size="small">
                  {rule.channels.map(channel => (
                    <Tag key={channel} color="purple">
                      {channel === 'webpush' ? 'Web Push' : 'Telegram'}
                    </Tag>
                  ))}
                </Space>
              )}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card size="small">
            <Statistic
              title="Перезарядка"
              value={rule.cooldownHours}
              suffix="ч"
            />
          </Card>
        </Col>
      </Row>

      <Card title="Условия правила" size="small" style={{ marginBottom: '16px' }}>
        {rule.conditions.length === 0 ? (
          <Alert
            message="Нет условий"
            description="Добавьте хотя бы одно условие для создания рабочего правила."
            type="info"
            showIcon
          />
        ) : (
          <Table
            columns={conditionColumns}
            dataSource={rule.conditions}
            rowKey="id"
            pagination={false}
            size="small"
          />
        )}
      </Card>

      <Card
        title={
          <Space>
            <Text>Тестирование на примерах</Text>
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={onTest}
              loading={loading}
              disabled={rule.conditions.length === 0}
            >
              Запустить тест
            </Button>
          </Space>
        }
        size="small"
      >
        {rule.conditions.length === 0 ? (
          <Alert
            message="Нечего тестировать"
            description="Добавьте условия в правило, чтобы протестировать его работу."
            type="warning"
            showIcon
          />
        ) : (
          <>
            <Row style={{ marginBottom: '16px' }}>
              <Col span={8}>
                <Statistic
                  title="Сработает на"
                  value={matchCount}
                  suffix={`/ ${totalCount}`}
                  valueStyle={{ color: matchCount > 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Процент срабатывания"
                  value={totalCount > 0 ? Math.round((matchCount / totalCount) * 100) : 0}
                  suffix="%"
                  valueStyle={{ color: matchCount > 0 ? '#3f8600' : '#cf1322' }}
                />
              </Col>
              <Col span={8}>
                <div style={{ textAlign: 'center', paddingTop: '8px' }}>
                  {matchCount === 0 && (
                    <Alert
                      message="Правило не сработает ни на одном примере"
                      type="warning"
                      showIcon
                      style={{ marginBottom: 0 }}
                    />
                  )}
                  {matchCount === totalCount && (
                    <Alert
                      message="Правило сработает на всех примерах"
                      type="success"
                      showIcon
                      style={{ marginBottom: 0 }}
                    />
                  )}
                  {matchCount > 0 && matchCount < totalCount && (
                    <Alert
                      message="Правило сработает на части примеров"
                      type="info"
                      showIcon
                      style={{ marginBottom: 0 }}
                    />
                  )}
                </div>
              </Col>
            </Row>

            <Table
              columns={testColumns}
              dataSource={results}
              rowKey="id"
              pagination={false}
              size="small"
              rowClassName={(record) => record.matches ? 'ant-table-row-success' : 'ant-table-row-disabled'}
            />
          </>
        )}
      </Card>

      <style>{`
        .ant-table-row-success {
          background-color: #f6ffed;
        }
        .ant-table-row-disabled {
          background-color: #fafafa;
          opacity: 0.6;
        }
      `}</style>
    </div>
  )
}

export default RulePreview