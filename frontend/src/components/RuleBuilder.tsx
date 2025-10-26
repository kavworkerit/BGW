import React, { useState, useCallback } from 'react'
import {
  Card,
  Select,
  Input,
  InputNumber,
  Button,
  Space,
  Typography,
  Row,
  Col,
  Tag,
  Switch,
  Tooltip,
  Divider
} from 'antd'
import {
  PlusOutlined,
  DeleteOutlined,
  DragOutlined,
  CopyOutlined,
  EyeOutlined
} from '@ant-design/icons'
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd'
import './RuleBuilder.css'

const { Title, Text } = Typography
const { Option } = Select

interface Condition {
  id: string
  field: string
  operator: string
  value: any
  enabled: boolean
}

interface RuleData {
  name: string
  logic: 'AND' | 'OR'
  conditions: Condition[]
  channels: string[]
  cooldownHours: number
  enabled: boolean
}

interface RuleBuilderProps {
  rule?: RuleData
  onChange: (rule: RuleData) => void
  onTest?: () => void
  onPreview?: () => void
  showPreview?: boolean
}

const FIELD_OPTIONS = [
  { value: 'game', label: 'Игра', description: 'Название игры или ID' },
  { value: 'title', label: 'Заголовок', description: 'Заголовок события' },
  { value: 'price', label: 'Цена', description: 'Цена товара' },
  { value: 'discount_pct', label: 'Скидка', description: 'Процент скидки' },
  { value: 'store_id', label: 'Магазин', description: 'ID или название магазина' },
  { value: 'kind', label: 'Тип', description: 'Тип события (announce, preorder, release, discount)' },
  { value: 'in_stock', label: 'Наличие', description: 'В наличии ли товар' },
  { value: 'publisher', label: 'Издатель', description: 'Издатель игры' },
  { value: 'tags', label: 'Теги', description: 'Теги игры' }
]

const OPERATOR_OPTIONS = {
  game: [
    { value: 'in', label: 'в списке', description: 'Значение содержится в списке' },
    { value: 'contains', label: 'содержит', description: 'Текст содержит значение' },
    { value: 'contains_any', label: 'содержит любое', description: 'Текст содержит любое из значений' },
    { value: 'equals', label: 'равно', description: 'Точное совпадение' }
  ],
  title: [
    { value: 'contains', label: 'содержит', description: 'Текст содержит значение' },
    { value: 'contains_any', label: 'содержит любое', description: 'Текст содержит любое из значений' },
    { value: 'equals', label: 'равно', description: 'Точное совпадение' },
    { value: 'starts_with', label: 'начинается с', description: 'Текст начинается со значения' }
  ],
  price: [
    { value: '>=', label: '≥ или больше', description: 'Больше или равно' },
    { value: '<=', label: '≤ или меньше', description: 'Меньше или равно' },
    { value: '=', label: 'равно', description: 'Точно равно' },
    { value: 'between', label: 'в диапазоне', description: 'Между двумя значениями' }
  ],
  discount_pct: [
    { value: '>=', label: '≥ или больше', description: 'Больше или равно' },
    { value: '<=', label: '≤ или меньше', description: 'Меньше или равно' },
    { value: '=', label: 'равно', description: 'Точно равно' },
    { value: 'between', label: 'в диапазоне', description: 'Между двумя значениями' }
  ],
  store_id: [
    { value: 'in', label: 'в списке', description: 'Магазин в списке' },
    { value: 'equals', label: 'равно', description: 'Точно равно' }
  ],
  kind: [
    { value: 'in', label: 'в списке', description: 'Тип в списке' },
    { value: 'equals', label: 'равно', description: 'Точно равно' }
  ],
  in_stock: [
    { value: 'equals', label: 'равно', description: 'Точно равно' }
  ],
  publisher: [
    { value: 'contains', label: 'содержит', description: 'Текст содержит значение' },
    { value: 'equals', label: 'равно', description: 'Точно равно' },
    { value: 'in', label: 'в списке', description: 'В списке издателей' }
  ],
  tags: [
    { value: 'contains_any', label: 'содержит любое', description: 'Содержит любой из тегов' },
    { value: 'contains_all', label: 'содержит все', description: 'Содержит все теги' }
  ]
}

const VALUE_INPUTS = {
  text: (field: string, value: any, onChange: (val: any) => void, operator: string) => {
    if (operator === 'in' || operator === 'contains_any') {
      return (
        <Select
          mode="tags"
          value={value || []}
          onChange={onChange}
          placeholder="Введите значения"
          style={{ width: '100%' }}
          tokenSeparators={[',']}
        />
      )
    }
    return (
      <Input
        value={value || ''}
        onChange={e => onChange(e.target.value)}
        placeholder="Введите значение"
      />
    )
  },
  number: (field: string, value: any, onChange: (val: any) => void, operator: string) => {
    if (operator === 'between') {
      return (
        <Space.Compact style={{ width: '100%' }}>
          <InputNumber
            value={value?.[0] || null}
            onChange={val => onChange([val, value?.[1] || null])}
            placeholder="От"
            style={{ width: '50%' }}
          />
          <InputNumber
            value={value?.[1] || null}
            onChange={val => onChange([value?.[0] || null, val])}
            placeholder="До"
            style={{ width: '50%' }}
          />
        </Space.Compact>
      )
    }
    return (
      <InputNumber
        value={value || null}
        onChange={onChange}
        placeholder="Введите число"
        style={{ width: '100%' }}
      />
    )
  },
  boolean: (field: string, value: any, onChange: (val: any) => void, operator: string) => (
    <Select
      value={value !== undefined ? value : null}
      onChange={onChange}
      placeholder="Выберите значение"
      style={{ width: '100%' }}
    >
      <Option value={true}>Да</Option>
      <Option value={false}>Нет</Option>
    </Select>
  )
}

const getValueType = (field: string): 'text' | 'number' | 'boolean' => {
  if (['price', 'discount_pct'].includes(field)) return 'number'
  if (field === 'in_stock') return 'boolean'
  return 'text'
}

const RuleBuilder: React.FC<RuleBuilderProps> = ({
  rule,
  onChange,
  onTest,
  onPreview,
  showPreview = true
}) => {
  const [expandedConditions, setExpandedConditions] = useState<Set<string>>(new Set())

  const initialRule: RuleData = {
    name: '',
    logic: 'AND',
    conditions: [],
    channels: ['webpush'],
    cooldownHours: 12,
    enabled: true,
    ...rule
  }

  const [ruleData, setRuleData] = useState<RuleData>(initialRule)

  const updateRuleData = useCallback((updates: Partial<RuleData>) => {
    const newData = { ...ruleData, ...updates }
    setRuleData(newData)
    onChange?.(newData)
  }, [ruleData, onChange])

  const addCondition = useCallback(() => {
    const newCondition: Condition = {
      id: `condition-${Date.now()}`,
      field: 'title',
      operator: 'contains',
      value: '',
      enabled: true
    }
    updateRuleData({
      conditions: [...ruleData.conditions, newCondition]
    })
  }, [ruleData.conditions, updateRuleData])

  const updateCondition = useCallback((index: number, updates: Partial<Condition>) => {
    const newConditions = [...ruleData.conditions]
    newConditions[index] = { ...newConditions[index], ...updates }
    updateRuleData({ conditions: newConditions })
  }, [ruleData.conditions, updateRuleData])

  const removeCondition = useCallback((index: number) => {
    const newConditions = ruleData.conditions.filter((_, i) => i !== index)
    updateRuleData({ conditions: newConditions })
  }, [ruleData.conditions, updateRuleData])

  const duplicateCondition = useCallback((index: number) => {
    const condition = ruleData.conditions[index]
    const newCondition: Condition = {
      ...condition,
      id: `condition-${Date.now()}`
    }
    const newConditions = [...ruleData.conditions]
    newConditions.splice(index + 1, 0, newCondition)
    updateRuleData({ conditions: newConditions })
  }, [ruleData.conditions, updateRuleData])

  const onDragEnd = useCallback((result: any) => {
    if (!result.destination) return

    const items = Array.from(ruleData.conditions)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    updateRuleData({ conditions: items })
  }, [ruleData.conditions, updateRuleData])

  const toggleConditionExpanded = useCallback((conditionId: string) => {
    const newExpanded = new Set(expandedConditions)
    if (newExpanded.has(conditionId)) {
      newExpanded.delete(conditionId)
    } else {
      newExpanded.add(conditionId)
    }
    setExpandedConditions(newExpanded)
  }, [expandedConditions])

  const renderConditionValue = (condition: Condition, index: number) => {
    const valueType = getValueType(condition.field)
    const ValueInput = VALUE_INPUTS[valueType]

    return ValueInput(condition.field, condition.value, (value) => {
      updateCondition(index, { value })
    }, condition.operator)
  }

  const renderCondition = (condition: Condition, index: number) => {
    const fieldInfo = FIELD_OPTIONS.find(f => f.value === condition.field)
    const operatorOptions = OPERATOR_OPTIONS[condition.field as keyof typeof OPERATOR_OPTIONS] || []

    return (
      <Card
        key={condition.id}
        size="small"
        style={{ marginBottom: '8px' }}
        title={
          <Space>
            <DragOutlined style={{ cursor: 'grab' }} />
            <Text strong>
              Условие {index + 1}: {fieldInfo?.label || condition.field}
            </Text>
            {!condition.enabled && <Tag color="default">Отключено</Tag>}
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="Дублировать">
              <Button
                type="text"
                size="small"
                icon={<CopyOutlined />}
                onClick={() => duplicateCondition(index)}
              />
            </Tooltip>
            <Tooltip title="Удалить">
              <Button
                type="text"
                size="small"
                danger
                icon={<DeleteOutlined />}
                onClick={() => removeCondition(index)}
              />
            </Tooltip>
          </Space>
        }
      >
        <Row gutter={[8, 8]}>
          <Col span={6}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Поле
            </label>
            <Select
              value={condition.field}
              onChange={(value) => updateCondition(index, {
                field: value,
                operator: OPERATOR_OPTIONS[value as keyof typeof OPERATOR_OPTIONS]?.[0]?.value || 'equals',
                value: null
              })}
              style={{ width: '100%' }}
              size="small"
            >
              {FIELD_OPTIONS.map(field => (
                <Option key={field.value} value={field.value}>
                  <Tooltip title={field.description}>
                    {field.label}
                  </Tooltip>
                </Option>
              ))}
            </Select>
          </Col>

          <Col span={6}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Оператор
            </label>
            <Select
              value={condition.operator}
              onChange={(value) => updateCondition(index, { operator: value, value: null })}
              style={{ width: '100%' }}
              size="small"
            >
              {operatorOptions.map(op => (
                <Option key={op.value} value={op.value}>
                  <Tooltip title={op.description}>
                    {op.label}
                  </Tooltip>
                </Option>
              ))}
            </Select>
          </Col>

          <Col span={8}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Значение
            </label>
            {renderConditionValue(condition, index)}
          </Col>

          <Col span={4}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Вкл
            </label>
            <Switch
              size="small"
              checked={condition.enabled}
              onChange={(enabled) => updateCondition(index, { enabled })}
            />
          </Col>
        </Row>
      </Card>
    )
  }

  return (
    <div>
      <Card size="small" style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 8]}>
          <Col span={12}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Название правила
            </label>
            <Input
              value={ruleData.name}
              onChange={(e) => updateRuleData({ name: e.target.value })}
              placeholder="Например: Скидки на стратегические игры"
            />
          </Col>

          <Col span={6}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Логика
            </label>
            <Select
              value={ruleData.logic}
              onChange={(value) => updateRuleData({ logic: value as 'AND' | 'OR' })}
              style={{ width: '100%' }}
            >
              <Option value="AND">
                <Tooltip title="Все условия должны быть выполнены">
                  И (AND)
                </Tooltip>
              </Option>
              <Option value="OR">
                <Tooltip title="Хотя бы одно условие должно быть выполнено">
                  ИЛИ (OR)
                </Tooltip>
              </Option>
            </Select>
          </Col>

          <Col span={6}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Перевызывается через (часы)
            </label>
            <InputNumber
              value={ruleData.cooldownHours}
              onChange={(value) => updateRuleData({ cooldownHours: value || 12 })}
              min={1}
              max={168}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>

        <Row style={{ marginTop: '12px' }}>
          <Col span={12}>
            <label style={{ display: 'block', marginBottom: '4px', fontSize: '12px', color: '#666' }}>
              Каналы уведомлений
            </label>
            <Select
              mode="multiple"
              value={ruleData.channels}
              onChange={(value) => updateRuleData({ channels: value })}
              style={{ width: '100%' }}
              placeholder="Выберите каналы"
            >
              <Option value="webpush">Web Push</Option>
              <Option value="telegram">Telegram</Option>
            </Select>
          </Col>

          <Col span={6} style={{ display: 'flex', alignItems: 'center', paddingTop: '24px' }}>
            <Space>
              <Text>Включено:</Text>
              <Switch
                checked={ruleData.enabled}
                onChange={(enabled) => updateRuleData({ enabled })}
              />
            </Space>
          </Col>

          {showPreview && (
            <Col span={6} style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', paddingTop: '24px' }}>
              <Space>
                {onPreview && (
                  <Button icon={<EyeOutlined />} onClick={onPreview}>
                    Предпросмотр
                  </Button>
                )}
                {onTest && (
                  <Button type="primary" onClick={onTest} disabled={!ruleData.enabled || ruleData.conditions.length === 0}>
                    Тест
                  </Button>
                )}
              </Space>
            </Col>
          )}
        </Row>
      </Card>

      <Divider>
        <Space>
          <Text strong>Условия ({ruleData.conditions.length})</Text>
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={addCondition}
            size="small"
          >
            Добавить условие
          </Button>
        </Space>
      </Divider>

      {ruleData.conditions.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '32px', backgroundColor: '#fafafa' }}>
          <Text type="secondary">
            Нет условий. Нажмите "Добавить условие" чтобы начать создавать правило.
          </Text>
        </Card>
      ) : (
        <DragDropContext onDragEnd={onDragEnd}>
          <Droppable droppableId="conditions">
            {(provided) => (
              <div {...provided.droppableProps} ref={provided.innerRef}>
                {ruleData.conditions.map((condition, index) => (
                  <Draggable key={condition.id} draggableId={condition.id} index={index}>
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        style={{
                          ...provided.draggableProps.style,
                          transform: snapshot.isDragging
                            ? provided.draggableProps.style?.transform
                            : provided.draggableProps.style?.transform?.replace(/scale\((\d+)\)/, 'scale(1)')
                        }}
                      >
                        {renderCondition(condition, index)}
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      )}
    </div>
  )
}

export default RuleBuilder