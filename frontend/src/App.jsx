import React, { useState } from 'react'
import { Layout, Menu, theme, Breadcrumb, Switch, Tooltip } from 'antd'
import { Routes, Route, Link, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  TeamOutlined,
  CodeOutlined,
  PullRequestOutlined,
  TrophyOutlined,
  UserOutlined,
  LinkOutlined,
  TableOutlined,
  ConsoleSqlOutlined,
  BulbOutlined,
  MoonOutlined,
  SunOutlined,
  HomeOutlined,
  BarChartOutlined,
} from '@ant-design/icons'

// Import pages
import Overview from './pages/Overview'
import AuthorsAnalytics from './pages/AuthorsAnalyticsEnhanced'
import CommitsView from './pages/CommitsView'
import PullRequestsView from './pages/PullRequestsView'
import TopCommits from './pages/TopCommits'
import TopApprovers from './pages/TopApprovers'
import AuthorMapping from './pages/AuthorMapping'
import TableViewer from './pages/TableViewer'
import SQLExecutor from './pages/SQLExecutor'
import StaffProductivity from './pages/StaffProductivity'
import TeamComparison from './pages/TeamComparison'
import Dashboard360 from './pages/Dashboard360'

const { Header, Content, Sider } = Layout

// Menu items configuration
const menuItems = [
  {
    key: '/',
    icon: <HomeOutlined />,
    label: <Link to="/">Overview</Link>,
    breadcrumb: 'Overview'
  },
  {
    key: '/authors',
    icon: <TeamOutlined />,
    label: <Link to="/authors">Authors Analytics</Link>,
    breadcrumb: 'Authors Analytics'
  },
  {
    key: '/360-dashboard',
    icon: <DashboardOutlined />,
    label: <Link to="/360-dashboard">360° Dashboards</Link>,
    breadcrumb: '360° Dashboards'
  },
  {
    key: '/productivity',
    icon: <BarChartOutlined />,
    label: <Link to="/productivity">Staff Productivity</Link>,
    breadcrumb: 'Staff Productivity'
  },
  {
    key: '/team-comparison',
    icon: <TeamOutlined />,
    label: <Link to="/team-comparison">Team Comparison</Link>,
    breadcrumb: 'Team Comparison'
  },
  {
    key: '/commits',
    icon: <CodeOutlined />,
    label: <Link to="/commits">Commits View</Link>,
    breadcrumb: 'Commits'
  },
  {
    key: '/pull-requests',
    icon: <PullRequestOutlined />,
    label: <Link to="/pull-requests">Pull Requests</Link>,
    breadcrumb: 'Pull Requests'
  },
  {
    key: '/top-commits',
    icon: <TrophyOutlined />,
    label: <Link to="/top-commits">Top Commits</Link>,
    breadcrumb: 'Top Commits'
  },
  {
    key: '/top-approvers',
    icon: <UserOutlined />,
    label: <Link to="/top-approvers">Top Approvers</Link>,
    breadcrumb: 'Top Approvers'
  },
  {
    key: '/mapping',
    icon: <LinkOutlined />,
    label: <Link to="/mapping">Author-Staff Mapping</Link>,
    breadcrumb: 'Author-Staff Mapping'
  },
  {
    key: '/tables',
    icon: <TableOutlined />,
    label: <Link to="/tables">Table Viewer</Link>,
    breadcrumb: 'Table Viewer'
  },
  {
    key: '/sql',
    icon: <ConsoleSqlOutlined />,
    label: <Link to="/sql">SQL Executor</Link>,
    breadcrumb: 'SQL Executor'
  },
]

function App() {
  const [collapsed, setCollapsed] = useState(false)
  const [darkMode, setDarkMode] = useState(false)
  const location = useLocation()
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken()

  // Get current breadcrumb
  const currentMenuItem = menuItems.find(item => item.key === location.pathname)
  const breadcrumbItems = [
    { title: <HomeOutlined /> },
    currentMenuItem && { title: currentMenuItem.breadcrumb }
  ].filter(Boolean)

  return (
    <Layout style={{ minHeight: '100vh' }} className={darkMode ? 'dark-theme' : ''}>
      {/* Sidebar */}
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        breakpoint="lg"
        width={240}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 18,
            fontWeight: 'bold',
            borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          }}
        >
          {collapsed ? <CodeOutlined /> : '📊 Git Analytics'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ borderRight: 0 }}
        />
      </Sider>

      {/* Main Layout */}
      <Layout style={{ marginLeft: collapsed ? 80 : 240, transition: 'all 0.2s' }}>
        {/* Header */}
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
            position: 'sticky',
            top: 0,
            zIndex: 1,
          }}
        >
          <h2 style={{ margin: 0, fontWeight: 600, color: '#1890ff' }}>
            Git History Analysis Dashboard
          </h2>
          <Tooltip title={darkMode ? 'Light Mode' : 'Dark Mode'}>
            <Switch
              checked={darkMode}
              onChange={setDarkMode}
              checkedChildren={<MoonOutlined />}
              unCheckedChildren={<SunOutlined />}
            />
          </Tooltip>
        </Header>

        {/* Breadcrumb */}
        <div className="breadcrumb-container">
          <Breadcrumb items={breadcrumbItems} />
        </div>

        {/* Content */}
        <Content
          style={{
            margin: '24px',
            padding: 24,
            minHeight: 'calc(100vh - 160px)',
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/authors" element={<AuthorsAnalytics />} />
            <Route path="/commits" element={<CommitsView />} />
            <Route path="/pull-requests" element={<PullRequestsView />} />
            <Route path="/top-commits" element={<TopCommits />} />
            <Route path="/top-approvers" element={<TopApprovers />} />
            <Route path="/productivity" element={<StaffProductivity />} />
            <Route path="/team-comparison" element={<TeamComparison />} />
            <Route path="/360-dashboard" element={<Dashboard360 />} />
            <Route path="/mapping" element={<AuthorMapping />} />
            <Route path="/tables" element={<TableViewer />} />
            <Route path="/sql" element={<SQLExecutor />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App
