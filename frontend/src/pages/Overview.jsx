import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Spin, Alert, Typography } from 'antd'
import {
  CodeOutlined,
  TeamOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  PullRequestOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import { overviewAPI } from '../services/api'

const { Title, Paragraph } = Typography

const Overview = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      setLoading(true)
      const data = await overviewAPI.getStats()
      setStats(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <Spin size="large" tip="Loading overview statistics..." />
      </div>
    )
  }

  if (error) {
    return <Alert message="Error" description={error} type="error" showIcon />
  }

  const statCards = [
    {
      title: 'Total Commits',
      value: stats?.total_commits || 0,
      icon: <CodeOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
      color: '#e6f7ff',
    },
    {
      title: 'Total Authors',
      value: stats?.total_authors || 0,
      icon: <TeamOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
      color: '#f6ffed',
    },
    {
      title: 'Total Repositories',
      value: stats?.total_repositories || 0,
      icon: <DatabaseOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
      color: '#f9f0ff',
    },
    {
      title: 'Total Lines Changed',
      value: stats?.total_lines || 0,
      icon: <LineChartOutlined style={{ fontSize: 32, color: '#fa8c16' }} />,
      color: '#fff7e6',
    },
    {
      title: 'Total Pull Requests',
      value: stats?.total_prs || 0,
      icon: <PullRequestOutlined style={{ fontSize: 32, color: '#13c2c2' }} />,
      color: '#e6fffb',
    },
    {
      title: 'Total Approvals',
      value: stats?.total_approvals || 0,
      icon: <CheckCircleOutlined style={{ fontSize: 32, color: '#eb2f96' }} />,
      color: '#fff0f6',
    },
  ]

  return (
    <div>
      <div className="page-header">
        <Title level={2}>📊 Dashboard Overview</Title>
        <Paragraph style={{ fontSize: 16, color: '#666' }}>
          Quick statistics and summary of your Git repository data
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {statCards.map((stat, index) => (
          <Col xs={24} sm={12} lg={8} key={index}>
            <Card
              hoverable
              className="stat-card"
              style={{
                background: stat.color,
                border: 'none',
              }}
            >
              <Statistic
                title={<span style={{ fontSize: 16, fontWeight: 500 }}>{stat.title}</span>}
                value={stat.value}
                valueStyle={{ fontSize: 32, fontWeight: 'bold' }}
                prefix={stat.icon}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        style={{ marginTop: 24 }}
        title={
          <span style={{ fontSize: 18, fontWeight: 600 }}>
            🚀 Quick Start Guide
          </span>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card type="inner" title="📈 Explore Analytics">
              <ul style={{ paddingLeft: 20 }}>
                <li>Visit <strong>Authors Analytics</strong> to see contributor statistics</li>
                <li>Check <strong>Top Commits</strong> for the largest code changes</li>
                <li>Review <strong>Top Approvers</strong> for PR review activity</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card type="inner" title="🔍 Dive Deeper">
              <ul style={{ paddingLeft: 20 }}>
                <li>Use <strong>Table Viewer</strong> to browse raw data</li>
                <li>Run custom queries in <strong>SQL Executor</strong></li>
                <li>Map authors to staff in <strong>Author-Staff Mapping</strong></li>
              </ul>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default Overview
