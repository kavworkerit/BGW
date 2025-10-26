import React, { useState, useEffect } from 'react'
import {
  Card,
  Button,
  Input,
  Select,
  Space,
  Typography,
  Alert,
  Spin,
  Tabs,
  Tag,
  Divider,
  Row,
  Col,
  message
} from 'antd'
import {
  ApiOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  PlayCircleOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input
const { Option } = Select
const { TabPane } = Tabs

interface LLMStatus {
  available: boolean
  url?: string
  models: string[]
  current_model?: string
  error?: string
}

interface LLMTestResult {
  success: boolean
  result?: any
  error?: string
  processing_time?: number
}

const LLMTester: React.FC = () => {
  const [status, setStatus] = useState<LLMStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [testResults, setTestResults] = useState<{ [key: string]: LLMTestResult }>({})

  // Формы для разных тестов
  const [extractText, setExtractText] = useState('')
  const [normalizeTitle, setNormalizeTitle] = useState('')
  const [categorizeTitle, setCategorizeTitle] = useState('')
  const [synonymsTitle, setSynonymsTitle] = useState('')
  const [synonymsDescription, setSynonymsDescription] = useState('')
  const [selectedModel, setSelectedModel] = useState('')

  useEffect(() => {
    checkLLMStatus()
  }, [])

  const checkLLMStatus = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/llm/status')
      const data: LLMStatus = await response.json()
      setStatus(data)
      if (data.current_model) {
        setSelectedModel(data.current_model)
      }
    } catch (error) {
      console.error('Error checking LLM status:', error)
      setStatus({
        available: false,
        error: 'Failed to check LLM status'
      })
    } finally {
      setLoading(false)
    }
  }

  const switchModel = async (modelName: string) => {
    try {
      const response = await fetch('/api/llm/models/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ model_name: modelName })
      })

      if (response.ok) {
        message.success(`Модель переключена на: ${modelName}`)
        await checkLLMStatus()
      } else {
        const error = await response.json()
        message.error(`Ошибка: ${error.detail}`)
      }
    } catch (error) {
      message.error('Не удалось переключить модель')
    }
  }

  const runTest = async (testType: string, data: any) => {
    setLoading(true)
    try {
      const response = await fetch('/api/llm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task: testType,
          text: data.text,
          ...(data.html_fragment && { html_fragment: data.html_fragment })
        })
      })

      const result: LLMTestResult = await response.json()
      setTestResults(prev => ({
        ...prev,
        [testType]: result
      }))

      if (result.success) {
        message.success(`Тест "${testType}" выполнен успешно`)
      } else {
        message.error(`Тест "${testType}" завершился с ошибкой`)
      }
    } catch (error) {
      message.error('Не удалось выполнить тест')
      setTestResults(prev => ({
        ...prev,
        [testType]: {
          success: false,
          error: 'Network error'
        }
      }))
    } finally {
      setLoading(false)
    }
  }

  const renderStatus = () => {
    if (!status) return null

    const statusIcon = status.available
      ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
      : <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />

    const statusText = status.available ? 'Доступен' : 'Недоступен'
    const statusColor = status.available ? 'success' : 'error'

    return (
      <Alert
        message={
          <Space>
            {statusIcon}
            <Text strong>Статус LLM: {statusText}</Text>
          </Space>
        }
        description={
          <div>
            <div>URL: {status.url}</div>
            {status.error && <Text type="danger">Ошибка: {status.error}</Text>}
          </div>
        }
        type={statusColor}
        showIcon
        style={{ marginBottom: 16 }}
      />
    )
  }

  const renderModels = () => {
    if (!status?.models.length) return null

    return (
      <Card title="Доступные модели" size="small" style={{ marginBottom: 16 }}>
        <Space wrap>
          {status.models.map(model => (
            <Tag
              key={model}
              color={model === status.current_model ? 'blue' : 'default'}
              style={{ cursor: 'pointer' }}
              onClick={() => model !== status.current_model && switchModel(model)}
            >
              {model} {model === status.current_model && '(текущая)'}
            </Tag>
          ))}
        </Space>
      </Card>
    )
  }

  const renderTestResult = (testType: string) => {
    const result = testResults[testType]
    if (!result) return null

    const statusIcon = result.success
      ? <CheckCircleOutlined style={{ color: '#52c41a' }} />
      : <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />

    return (
      <div style={{ marginTop: 16 }}>
        <Space>
          {statusIcon}
          <Text strong>
            {result.success ? 'Успешно' : 'Ошибка'}
            {result.processing_time && ` (${result.processing_time.toFixed(2)}с)`}
          </Text>
        </Space>

        {result.success && result.result && (
          <div style={{ marginTop: 8 }}>
            <Text code>
              {JSON.stringify(result.result, null, 2)}
            </Text>
          </div>
        )}

        {result.error && (
          <Alert
            message={result.error}
            type="error"
            size="small"
            style={{ marginTop: 8 }}
          />
        )}
      </div>
    )
  }

  return (
    <div>
      <Title level={2}>
        <ApiOutlined /> Тестирование LLM (Ollama)
      </Title>

      <Spin spinning={loading}>
        {renderStatus()}
        {renderModels()}

        <Tabs defaultActiveKey="extract" type="card">
          <TabPane tab="Извлечение информации" key="extract">
            <Card>
              <Title level={4}>Извлечение информации об игре</Title>
              <Paragraph>
                Проверьте способность LLM извлекать структурированную информацию из текста.
              </Paragraph>

              <TextArea
                rows={6}
                placeholder="Введите текст с информацией об игре..."
                value={extractText}
                onChange={(e) => setExtractText(e.target.value)}
                style={{ marginBottom: 16 }}
              />

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => runTest('extract_game_info', { text: extractText })}
                disabled={!extractText || !status?.available}
              >
                Выполнить тест
              </Button>

              {renderTestResult('extract_game_info')}
            </Card>
          </TabPane>

          <TabPane tab="Нормализация названий" key="normalize">
            <Card>
              <Title level={4}>Нормализация названий игр</Title>
              <Paragraph>
                Проверьте способность LLM приводить названия к стандартному виду.
              </Paragraph>

              <Input
                placeholder="Введите название игры..."
                value={normalizeTitle}
                onChange={(e) => setNormalizeTitle(e.target.value)}
                style={{ marginBottom: 16 }}
              />

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => runTest('normalize_title', { text: normalizeTitle })}
                disabled={!normalizeTitle || !status?.available}
              >
                Выполнить тест
              </Button>

              {renderTestResult('normalize_title')}
            </Card>
          </TabPane>

          <TabPane tab="Категоризация событий" key="categorize">
            <Card>
              <Title level={4}>Определение типа события</Title>
              <Paragraph>
                Проверьте способность LLM классифицировать события (announce, preorder, release, discount, price).
              </Paragraph>

              <Input
                placeholder="Введите заголовок события..."
                value={categorizeTitle}
                onChange={(e) => setCategorizeTitle(e.target.value)}
                style={{ marginBottom: 16 }}
              />

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => runTest('categorize_event', { text: categorizeTitle })}
                disabled={!categorizeTitle || !status?.available}
              >
                Выполнить тест
              </Button>

              {renderTestResult('categorize_event')}
            </Card>
          </TabPane>

          <TabPane tab="Генерация синонимов" key="synonyms">
            <Card>
              <Title level={4}>Генерация синонимов</Title>
              <Paragraph>
                Проверьте способность LLM генерировать синонимы для названий игр.
              </Paragraph>

              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={12}>
                  <Input
                    placeholder="Название игры..."
                    value={synonymsTitle}
                    onChange={(e) => setSynonymsTitle(e.target.value)}
                  />
                </Col>
                <Col span={12}>
                  <Input
                    placeholder="Описание (опционально)..."
                    value={synonymsDescription}
                    onChange={(e) => setSynonymsDescription(e.target.value)}
                  />
                </Col>
              </Row>

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={() => runTest('suggest_synonyms', {
                  text: synonymsTitle,
                  ...(synonymsDescription && { description: synonymsDescription })
                })}
                disabled={!synonymsTitle || !status?.available}
              >
                Выполнить тест
              </Button>

              {renderTestResult('suggest_synonyms')}
            </Card>
          </TabPane>
        </Tabs>

        <Divider />

        <Space>
          <Button onClick={checkLLMStatus} icon={<ApiOutlined />}>
            Обновить статус
          </Button>
        </Space>
      </Spin>
    </div>
  )
}

export default LLMTester