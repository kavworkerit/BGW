import React from 'react'
import { Layout, Menu } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  DatabaseOutlined,
  RobotOutlined,
  BellOutlined,
  SettingOutlined,
  CalendarOutlined
} from '@ant-design/icons'

const { Sider } = Layout

const menuItems = [
  {
    key: '/',
    icon: <DashboardOutlined />,
    label: 'Дашборд',
  },
  {
    key: '/games',
    icon: <DatabaseOutlined />,
    label: 'Игры',
  },
  {
    key: '/agents',
    icon: <RobotOutlined />,
    label: 'Агенты',
  },
  {
    key: '/events',
    icon: <CalendarOutlined />,
    label: 'События',
  },
  {
    key: '/rules',
    icon: <BellOutlined />,
    label: 'Правила',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Настройки',
  },
]

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  return (
    <Sider
      collapsible
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <div className="logo">
        🎲 Мониторинг
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={({ key }) => navigate(key)}
      />
    </Sider>
  )
}

export default Sidebar