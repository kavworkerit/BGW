import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Sidebar from './components/Layout/Sidebar'
import Header from './components/Layout/Header'
import Dashboard from './pages/Dashboard'
import Games from './pages/Games'
import Agents from './pages/Agents'
import Events from './pages/Events'
import Rules from './pages/Rules'
import Settings from './pages/Settings'

const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header />
        <Content style={{ margin: '16px' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/games" element={<Games />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="/events" element={<Events />} />
            <Route path="/rules" element={<Rules />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App