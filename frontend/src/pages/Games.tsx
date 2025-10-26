import React, { useState } from 'react'
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Tag,
  Typography,
  Popconfirm
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined
} from '@ant-design/icons'

const { Title } = Typography
const { Search } = Input

interface Game {
  id: string
  title: string
  synonyms: string[]
  bgg_id?: string
  publisher?: string
  tags: string[]
  created_at: string
}

const Games: React.FC = () => {
  const [games, setGames] = useState<Game[]>([
    {
      id: '1',
      title: 'Громкое дело',
      synonyms: ['Gromkoe Delo', 'Loud Deal'],
      bgg_id: '123456',
      publisher: 'Hobby Games',
      tags: ['детектив', 'расследование'],
      created_at: '2024-01-15T10:30:00Z'
    },
    {
      id: '2',
      title: 'Dune: Imperium',
      synonyms: ['Dune Империум'],
      bgg_id: '316906',
      publisher: 'Dire Wolf',
      tags: ['стратегия', 'карточная'],
      created_at: '2024-01-10T14:20:00Z'
    }
  ])

  const [modalVisible, setModalVisible] = useState(false)
  const [editingGame, setEditingGame] = useState<Game | null>(null)
  const [form] = Form.useForm()

  const columns = [
    {
      title: 'Название',
      dataIndex: 'title',
      key: 'title',
      render: (title: string) => <strong>{title}</strong>
    },
    {
      title: 'Синонимы',
      dataIndex: 'synonyms',
      key: 'synonyms',
      render: (synonyms: string[]) => (
        <>
          {synonyms.map((synonym, index) => (
            <Tag key={index} style={{ marginBottom: '4px' }}>
              {synonym}
            </Tag>
          ))}
        </>
      )
    },
    {
      title: 'BGG ID',
      dataIndex: 'bgg_id',
      key: 'bgg_id',
      render: (bgg_id: string) => (
        bgg_id ? (
          <a href={`https://boardgamegeek.com/boardgame/${bgg_id}`} target="_blank" rel="noopener noreferrer">
            {bgg_id}
          </a>
        ) : '-'
      )
    },
    {
      title: 'Издатель',
      dataIndex: 'publisher',
      key: 'publisher'
    },
    {
      title: 'Теги',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <>
          {tags.map((tag, index) => (
            <Tag key={index} color="blue" style={{ marginBottom: '4px' }}>
              {tag}
            </Tag>
          ))}
        </>
      )
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record: Game) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Удалить игру?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const handleAdd = () => {
    setEditingGame(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (game: Game) => {
    setEditingGame(game)
    form.setFieldsValue(game)
    setModalVisible(true)
  }

  const handleDelete = (id: string) => {
    setGames(games.filter(game => game.id !== id))
  }

  const handleModalOk = () => {
    form.validateFields().then(values => {
      if (editingGame) {
        // Редактирование
        setGames(games.map(game =>
          game.id === editingGame.id
            ? { ...game, ...values }
            : game
        ))
      } else {
        // Добавление
        const newGame: Game = {
          id: Date.now().toString(),
          ...values,
          created_at: new Date().toISOString()
        }
        setGames([...games, newGame])
      }
      setModalVisible(false)
      form.resetFields()
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <Title level={2}>Игры</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
          Добавить игру
        </Button>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <Search
          placeholder="Поиск по названию или синонимам"
          allowClear
          style={{ width: 300 }}
          prefix={<SearchOutlined />}
        />
      </div>

      <Table
        columns={columns}
        dataSource={games}
        rowKey="id"
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} игр`
        }}
      />

      <Modal
        title={editingGame ? 'Редактировать игру' : 'Добавить игру'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            synonyms: [],
            tags: []
          }}
        >
          <Form.Item
            name="title"
            label="Название"
            rules={[{ required: true, message: 'Введите название игры' }]}
          >
            <Input placeholder="Например: Громкое дело" />
          </Form.Item>

          <Form.Item
            name="synonyms"
            label="Синонимы"
          >
            <Input.TextArea
              placeholder="Введите синонимы через запятую"
              rows={2}
            />
          </Form.Item>

          <Form.Item
            name="bgg_id"
            label="BGG ID"
          >
            <Input placeholder="ID с BoardGameGeek" />
          </Form.Item>

          <Form.Item
            name="publisher"
            label="Издатель"
          >
            <Input placeholder="Например: Hobby Games" />
          </Form.Item>

          <Form.Item
            name="tags"
            label="Теги"
          >
            <Input.TextArea
              placeholder="Введите теги через запятую"
              rows={2}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Games