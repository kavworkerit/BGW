import React, { useState } from 'react'
import {
  Card,
  Button,
  Space,
  Upload,
  message,
  Typography,
  Divider,
  Row,
  Col,
  Alert,
  Modal,
  Table,
  Tag,
  Progress
} from 'antd'
import {
  UploadOutlined,
  DownloadOutlined,
  FileZipOutlined,
  FileExcelOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons'

const { Title, Text, Paragraph } = Typography

interface ImportResult {
  added: number
  updated: number
  skipped: number
  errors: string[]
}

interface ExportFormat {
  key: string
  title: string
  description: string
  icon: React.ReactNode
  size?: string
  lastExport?: string
}

const ExportImport: React.FC = () => {
  const [importLoading, setImportLoading] = useState(false)
  const [exportLoading, setExportLoading] = useState(false)
  const [importResult, setImportResult] = useState<ImportResult | null>(null)
  const [previewData, setPreviewData] = useState<any[]>([])

  const exportFormats: ExportFormat[] = [
    {
      key: 'full',
      title: 'Полный экспорт',
      description: 'Все данные (игры, события, правила, история цен)',
      icon: <FileZipOutlined />,
      size: '~15-25 МБ',
      lastExport: '2024-01-20 14:30'
    },
    {
      key: 'games',
      title: 'Только игры',
      description: 'Watchlist игр с синонимами',
      icon: <FileExcelOutlined />,
      size: '~100-500 КБ'
    },
    {
      key: 'events',
      title: 'Только события',
      description: 'События за выбранный период',
      icon: <FileExcelOutlined />,
      size: '~1-5 МБ'
    },
    {
      key: 'prices',
      title: 'История цен',
      description: 'Данные по ценам для графиков',
      icon: <FileExcelOutlined />,
      size: '~2-10 МБ'
    }
  ]

  const handleExport = async (format: string) => {
    setExportLoading(true)
    try {
      const response = await fetch(`/api/export/${format}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `bgw-export-${format}-${new Date().toISOString().split('T')[0]}.${format === 'full' ? 'zip' : 'csv'}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        message.success('Экспорт выполнен успешно')
      } else {
        message.error('Ошибка при экспорте данных')
      }
    } catch (error) {
      message.error('Ошибка при экспорте данных')
    } finally {
      setExportLoading(false)
    }
  }

  const handleImport = async (file: File) => {
    setImportLoading(true)

    const formData = new FormData()
    formData.append('file', file)

    try {
      // Сначала проверка (dry run)
      const dryResponse = await fetch('/api/import/full?dry_run=true', {
        method: 'POST',
        body: formData
      })

      if (dryResponse.ok) {
        const dryResult = await dryResponse.json()
        setPreviewData(dryResult.preview || [])

        // Показываем превью
        Modal.confirm({
          title: 'Предпросмотр импорта',
          width: 800,
          content: (
            <div>
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={6}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#52c41a', fontWeight: 'bold' }}>
                        {dryResult.added || 0}
                      </div>
                      <div>Будет добавлено</div>
                    </div>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#1890ff', fontWeight: 'bold' }}>
                        {dryResult.updated || 0}
                      </div>
                      <div>Будет обновлено</div>
                    </div>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#faad14', fontWeight: 'bold' }}>
                        {dryResult.skipped || 0}
                      </div>
                      <div>Пропущено</div>
                    </div>
                  </Card>
                </Col>
                <Col span={6}>
                  <Card size="small">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, color: '#f5222d', fontWeight: 'bold' }}>
                        {dryResult.errors?.length || 0}
                      </div>
                      <div>Ошибок</div>
                    </div>
                  </Card>
                </Col>
              </Row>

              {dryResult.errors && dryResult.errors.length > 0 && (
                <Alert
                  message="Обнаружены ошибки"
                  description={
                    <ul>
                      {dryResult.errors.slice(0, 5).map((error: string, index: number) => (
                        <li key={index}>{error}</li>
                      ))}
                      {dryResult.errors.length > 5 && (
                        <li>... и еще {dryResult.errors.length - 5} ошибок</li>
                      )}
                    </ul>
                  }
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}

              <Paragraph>
                Продолжить импорт? Это действие может изменить существующие данные.
              </Paragraph>
            </div>
          ),
          onOk: async () => {
            // Выполняем реальный импорт
            const importResponse = await fetch('/api/import/full', {
              method: 'POST',
              body: formData
            })

            if (importResponse.ok) {
              const result = await importResponse.json()
              setImportResult(result)
              message.success('Импорт выполнен успешно')
            } else {
              message.error('Ошибка при импорте данных')
            }
          }
        })
      } else {
        message.error('Ошибка при проверке файла')
      }
    } catch (error) {
      message.error('Ошибка при импорте данных')
    } finally {
      setImportLoading(false)
    }

    return false // Предотвращаем автоматическую загрузку файла
  }

  const columns = [
    {
      title: 'Тип',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'game' ? 'blue' : type === 'event' ? 'green' : 'orange'}>
          {type}
        </Tag>
      )
    },
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title'
    },
    {
      title: 'Действие',
      dataIndex: 'action',
      key: 'action',
      render: (action: string) => (
        <Tag color={action === 'add' ? 'green' : action === 'update' ? 'blue' : 'default'}>
          {action === 'add' ? 'Добавление' : action === 'update' ? 'Обновление' : 'Пропуск'}
        </Tag>
      )
    }
  ]

  return (
    <div>
      <Title level={2}>Импорт и экспорт данных</Title>

      <Row gutter={24}>
        <Col span={12}>
          <Card
            title="Экспорт данных"
            extra={<FileZipOutlined style={{ fontSize: 24, color: '#1890ff' }} />}
          >
            <Paragraph>
              Создайте резервную копию или экспортируйте данные для внешнего анализа.
            </Paragraph>

            <Space direction="vertical" style={{ width: '100%' }}>
              {exportFormats.map(format => (
                <Card key={format.key} size="small" style={{ marginBottom: 8 }}>
                  <Row align="middle" justify="space-between">
                    <Col flex="auto">
                      <Space>
                        {format.icon}
                        <div>
                          <div style={{ fontWeight: 'bold' }}>{format.title}</div>
                          <div style={{ color: '#666', fontSize: '12px' }}>
                            {format.description}
                          </div>
                          <div style={{ color: '#999', fontSize: '11px' }}>
                            {format.size}
                            {format.lastExport && ` • Последний: ${format.lastExport}`}
                          </div>
                        </div>
                      </Space>
                    </Col>
                    <Col>
                      <Button
                        type="primary"
                        icon={<DownloadOutlined />}
                        loading={exportLoading}
                        onClick={() => handleExport(format.key)}
                      >
                        Экспортировать
                      </Button>
                    </Col>
                  </Row>
                </Card>
              ))}
            </Space>
          </Card>
        </Col>

        <Col span={12}>
          <Card
            title="Импорт данных"
            extra={<UploadOutlined style={{ fontSize: 24, color: '#52c41a' }} />}
          >
            <Paragraph>
              Загрузите ранее экспортированные данные для восстановления или синхронизации.
            </Paragraph>

            <Alert
              message="Внимание"
              description="Импорт изменит существующие данные. Рекомендуется создать резервную копию перед импортом."
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />

            <Upload
              accept=".zip,.csv"
              showUploadList={false}
              beforeUpload={handleImport}
              disabled={importLoading}
            >
              <Button
                icon={importLoading ? <LoadingOutlined /> : <UploadOutlined />}
                loading={importLoading}
                style={{ width: '100%' }}
              >
                {importLoading ? 'Обработка файла...' : 'Выбрать файл для импорта'}
              </Button>
            </Upload>

            <Divider />

            <div>
              <Text strong>Поддерживаемые форматы:</Text>
              <ul style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                <li>ZIP — полный экспорт системы</li>
                <li>CSV — данные для анализа (Excel, Google Sheets)</li>
              </ul>
            </div>
          </Card>
        </Col>
      </Row>

      {importResult && (
        <Card
          title="Результаты импорта"
          style={{ marginTop: 24 }}
          extra={
            <Space>
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
              <Text strong>Завершено</Text>
            </Space>
          }
        >
          <Row gutter={16}>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#52c41a', fontWeight: 'bold' }}>
                    {importResult.added}
                  </div>
                  <div>Добавлено</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#1890ff', fontWeight: 'bold' }}>
                    {importResult.updated}
                  </div>
                  <div>Обновлено</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#faad14', fontWeight: 'bold' }}>
                    {importResult.skipped}
                  </div>
                  <div>Пропущено</div>
                </div>
              </Card>
            </Col>
            <Col span={6}>
              <Card size="small">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 24, color: '#f5222d', fontWeight: 'bold' }}>
                    {importResult.errors.length}
                  </div>
                  <div>Ошибок</div>
                </div>
              </Card>
            </Col>
          </Row>

          {importResult.errors.length > 0 && (
            <>
              <Divider />
              <Alert
                message="Обнаружены ошибки при импорте"
                description={
                  <ul>
                    {importResult.errors.map((error, index) => (
                      <li key={index}>{error}</li>
                    ))}
                  </ul>
                }
                type="error"
                showIcon
              />
            </>
          )}
        </Card>
      )}
    </div>
  )
}

export default ExportImport