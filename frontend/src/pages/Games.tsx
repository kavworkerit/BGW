import React, { useEffect, useState } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Tag,
  Typography,
  Popconfirm,
  Select,
  InputNumber,
  message,
  Card,
  Row,
  Col,
  Statistic,
  Tooltip,
  Badge
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  BgColorsOutlined,
  LineChartOutlined
} from '@ant-design/icons'
import { useGameStore } from '../store/useGameStore'
import PriceChart from '../components/PriceChart'

const { Title, Text } = Typography
const { Search } = Input
const { TextArea } = Input
const { Option } = Select

interface Game {
  id: string
  title: string
  description?: string
  synonyms: string[]
  bgg_id?: string
  publisher?: string
  min_players?: number
  max_players?: number
  min_playtime?: number
  max_playtime?: number
  language?: string
  complexity?: number
  rating?: number
  image_url?: string
  tags: string[]
  created_at: string
  updated_at: string
}

const Games: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [editingGame, setEditingGame] = useState<Game | null>(null)
  const [searchText, setSearchText] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedGameForChart, setSelectedGameForChart] = useState<Game | null>(null)
  const [showPriceChart, setShowPriceChart] = useState(false)
  const [form] = Form.useForm()

  // Store hooks
  const {
    games,
    loading,
    error,
    stats,
    fetchGames,
    createGame,
    updateGame,
    deleteGame,
    searchGames,
    getStats
  } = useGameStore()

  // Load games on component mount
  useEffect(() => {
    loadGames()
    loadStats()
  }, [])

  const loadGames = async () => {
    try {
      await fetchGames()
    } catch (error) {
      message.error('Не удалось загрузить игры')
    }
  }

  const loadStats = async () => {
    try {
      await getStats()
    } catch (error) {
      console.error('Failed to load stats:', error)
    }
  }

  const handleCreate = () => {
    setEditingGame(null)
    form.resetFields()
    setIsModalVisible(true)
  }

  const handleEdit = (game: Game) => {
    setEditingGame(game)
    form.setFieldsValue({
      ...game,
      synonyms: game.synonyms.join(', '),
      tags: game.tags.join(', ')
    })
    setIsModalVisible(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteGame(id)
      message.success('Игра удалена')
      await loadGames()
      await loadStats()
    } catch (error) {
      message.error('Не удалось удалить игру')
    }
  }

  const handleSearch = async (value: string) => {
    setSearchText(value)
    try {
      await searchGames(value)
    } catch (error) {
      message.error('Не удалось выполнить поиск')
    }
  }

  const handleTagFilter = (tags: string[]) => {
    setSelectedTags(tags)
    // Здесь можно добавить фильтрацию по тегам
  }

  const handleShowPriceChart = (game: Game) => {
    setSelectedGameForChart(game)
    setShowPriceChart(true)
  }

  const handleSubmit = async (values: any) => {
    try {
      const gameData = {
        ...values,
        synonyms: values.synonyms ? values.synonyms.split(',').map((s: string) => s.trim()).filter(Boolean) : [],
        tags: values.tags ? values.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : []
      }

      if (editingGame) {
        await updateGame(editingGame.id, gameData)
        message.success('Игра обновлена')
      } else {
        await createGame(gameData)
        message.success('Игра создана')
      }

      setIsModalVisible(false)
      form.resetFields()
      await loadGames()
      await loadStats()
    } catch (error) {
      message.error('Не удалось сохранить игру')
    }
  }

  const columns = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: Game) => (
        <div>
          <Text strong>{title}</Text>
          {record.bgg_id && (
            <div>
              <Tooltip title="BoardGameGeek ID">
                <BgColorsOutlined style={{ marginRight: 4 }} />
                <Text type="secondary">{record.bgg_id}</Text>
              </Tooltip>
            </div>
          )}
        </div>
      ),
      sorter: (a: Game, b: Game) => a.title.localeCompare(b.title)
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string) => (
        <Tooltip title={description}>
          <Text>{description}</Text>
        </Tooltip>
      )
    },
    {
      title: 'Игроки',
      key: 'players',
      render: (record: Game) => (
        <Text>
          {record.min_players || '?'}-{record.max_players || '?'}
        </Text>
      ),
      width: 80
    },
    {
      title: 'Время',
      key: 'playtime',
      render: (record: Game) => (
        <Text>
          {record.min_playtime || '?'}-{record.max_playtime || '?'} мин
        </Text>
      ),
      width: 100
    },
    {
      title: 'Сложность',
      dataIndex: 'complexity',
      key: 'complexity',
      width: 100,
      render: (complexity?: number) => {
        if (!complexity) return <Text>-</Text>
        let color = 'green'
        if (complexity > 3) color = 'orange'
        if (complexity > 4) color = 'red'
        return <Badge count={complexity.toFixed(1)} style={{ backgroundColor: color }} />
      }
    },
    {
      title: 'Рейтинг',
      dataIndex: 'rating',
      key: 'rating',
      width: 80,
      render: (rating?: number) => rating ? rating.toFixed(1) : '-'
    },
    {
      title: 'Теги',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <div>
          {tags.slice(0, 3).map(tag => (
            <Tag key={tag} size="small">{tag}</Tag>
          ))}
          {tags.length > 3 && (
            <Tag size="small">+{tags.length - 3}</Tag>
          )}
        </div>
      )
    },
    {
      title: 'График цен',
      key: 'chart',
      width: 100,
      render: (record: Game) => (
        <Tooltip title="Показать график цен">
          <Button
            size="small"
            icon={<LineChartOutlined />}
            onClick={() => handleShowPriceChart(record)}
          />
        </Tooltip>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (record: Game) => (
        <Space>
          <Tooltip title="Редактировать">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Удалить игру?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Tooltip title="Удалить">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>Игры</Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadGames}
            loading={loading}
          >
            Обновить
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Добавить игру
          </Button>
        </Space>
      </div>

      {/* Статистика */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Всего игр"
              value={stats?.total_games || 0}
              prefix={<InfoCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="С BGG ID"
              value={stats?.games_with_bgg || 0}
              prefix={<BgColorsOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Уникальных издателей"
              value={stats?.unique_publishers || 0}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Уникальных тегов"
              value={stats?.unique_tags || 0}
            />
          </Card>
        </Col>
      </Row>

      {/* Фильтры */}
      <Card style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col flex="auto">
            <Search
              placeholder="Поиск по названию, синонимам..."
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={handleSearch}
              onChange={(e) => !e.target.value && setSearchText('')}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Таблица игр */}
      <Card>
        <Table
          columns={columns}
          dataSource={games}
          rowKey="id"
          loading={loading}
          pagination={{
            total: games.length,
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} игр`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Модальное окно создания/редактирования */}
      <Modal
        title={editingGame ? 'Редактировать игру' : 'Добавить игру'}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Название"
                name="title"
                rules={[{ required: true, message: 'Введите название игры' }]}
              >
                <Input placeholder="Название игры" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="BoardGameGeek ID"
                name="bgg_id"
              >
                <Input placeholder="123456" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Описание"
            name="description"
          >
            <TextArea rows={3} placeholder="Краткое описание игры" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Издатель"
                name="publisher"
              >
                <Input placeholder="Название издателя" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Язык"
                name="language"
              >
                <Input placeholder="Русский, английский и т.д." />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={6}>
              <Form.Item
                label="Мин. игроков"
                name="min_players"
              >
                <InputNumber min={1} placeholder="1" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="Макс. игроков"
                name="max_players"
              >
                <InputNumber min={1} placeholder="4" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="Мин. время (мин)"
                name="min_playtime"
              >
                <InputNumber min={1} placeholder="30" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item
                label="Макс. время (мин)"
                name="max_playtime"
              >
                <InputNumber min={1} placeholder="60" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Сложность (1-5)"
                name="complexity"
              >
                <InputNumber
                  min={1}
                  max={5}
                  step={0.1}
                  placeholder="2.5"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Рейтинг (1-10)"
                name="rating"
              >
                <InputNumber
                  min={1}
                  max={10}
                  step={0.1}
                  placeholder="7.5"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Синонимы"
            name="synonyms"
          >
            <Input placeholder="Через запятую: Gromkoe Delo, Loud Deal" />
          </Form.Item>

          <Form.Item
            label="Теги"
            name="tags"
          >
            <Input placeholder="Через запятую: стратегия, карточная, детектив" />
          </Form.Item>

          <Form.Item
            label="URL изображения"
            name="image_url"
          >
            <Input placeholder="https://example.com/image.jpg" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setIsModalVisible(false)}>
                Отмена
              </Button>
              <Button type="primary" htmlType="submit">
                {editingGame ? 'Сохранить' : 'Создать'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно с графиком цен */}
      <Modal
        title={`График цен: ${selectedGameForChart?.title}`}
        open={showPriceChart}
        onCancel={() => setShowPriceChart(false)}
        footer={null}
        width={1200}
        destroyOnClose
      >
        {selectedGameForChart && (
          <PriceChart
            gameId={selectedGameForChart.id}
            gameTitle={selectedGameForChart.title}
          />
        )}
      </Modal>
    </div>
  )
}

export default Games