import React from 'react'
import { Layout, Typography, Space, Badge } from 'antd'
import { BellOutlined } from '@ant-design/icons'

const { Header: AntHeader } = Layout
const { Title } = Typography

const Header: React.FC = () => {
  return (
    <AntHeader style={{
      padding: '0 24px',
      background: '#fff',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      <Title level={4} style={{ margin: 0 }}>
        Мониторинг настольных игр
      </Title>
      <Space>
        <Badge count={5} size="small">
          <BellOutlined style={{ fontSize: '18px', color: '#666' }} />
        </Badge>
      </Space>
    </AntHeader>
  )
}

export default Header