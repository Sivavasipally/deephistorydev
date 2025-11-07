import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  DatePicker,
  Button,
  Row,
  Col,
  Statistic,
  Spin,
  Alert,
  Typography,
  Select,
  Space,
  message,
} from 'antd'
import {
  DownloadOutlined,
  ReloadOutlined,
  TrophyOutlined,
  CodeOutlined,
  LineChartOutlined,
  TeamOutlined,
} from '@ant-design/icons'
import { Column } from '@ant-design/charts'
import { authorsAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title } = Typography
const { RangePicker } = DatePicker

const AuthorsAnalytics = () => {
  const [authors, setAuthors] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateRange, setDateRange] = useState([null, null])
  const [sortBy, setSortBy] = useState('total_commits')
  const [sortOrder, setSortOrder] = useState('descend')

  useEffect(() => {
    fetchAuthors()
  }, [dateRange])

  const fetchAuthors = async () => {
    try {
      setLoading(true)
      const params = {}
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD')
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD')

      const data = await authorsAPI.getStatistics(params)
      setAuthors(data)
      setError(null)
    } catch (err) {
      setError(err.message)
      message.error('Failed to fetch author statistics')
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    // Convert to CSV
    const headers = [
      'Author Name',
      'Email',
      'Total Commits',
      'Lines Added',
      'Lines Deleted',
      'Total Lines',
      'Files Changed',
      'Repositories',
      'PRs Created',
      'PRs Approved',
    ]
    const csv = [
      headers.join(','),
      ...authors.map((a) =>
        [
          a.author_name,
          a.email,
          a.total_commits,
          a.lines_added,
          a.lines_deleted,
          a.total_lines_changed,
          a.files_changed,
          a.repositories_count,
          a.prs_created,
          a.prs_approved,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `authors_analytics_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  const columns = [
    {
      title: 'Author Name',
      dataIndex: 'author_name',
      key: 'author_name',
      fixed: 'left',
      width: 200,
      sorter: (a, b) => a.author_name.localeCompare(b.author_name),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 250,
    },
    {
      title: 'Commits',
      dataIndex: 'total_commits',
      key: 'total_commits',
      sorter: (a, b) => a.total_commits - b.total_commits,
      defaultSortOrder: 'descend',
    },
    {
      title: 'Lines Added',
      dataIndex: 'lines_added',
      key: 'lines_added',
      sorter: (a, b) => a.lines_added - b.lines_added,
      render: (val) => val.toLocaleString(),
    },
    {
      title: 'Lines Deleted',
      dataIndex: 'lines_deleted',
      key: 'lines_deleted',
      sorter: (a, b) => a.lines_deleted - b.lines_deleted,
      render: (val) => val.toLocaleString(),
    },
    {
      title: 'Total Lines',
      dataIndex: 'total_lines_changed',
      key: 'total_lines_changed',
      sorter: (a, b) => a.total_lines_changed - b.total_lines_changed,
      render: (val) => val.toLocaleString(),
    },
    {
      title: 'Files',
      dataIndex: 'files_changed',
      key: 'files_changed',
      sorter: (a, b) => a.files_changed - b.files_changed,
      render: (val) => val.toLocaleString(),
    },
    {
      title: 'Repos',
      dataIndex: 'repositories_count',
      key: 'repositories_count',
      sorter: (a, b) => a.repositories_count - b.repositories_count,
    },
    {
      title: 'PRs Created',
      dataIndex: 'prs_created',
      key: 'prs_created',
      sorter: (a, b) => a.prs_created - b.prs_created,
    },
    {
      title: 'PRs Approved',
      dataIndex: 'prs_approved',
      key: 'prs_approved',
      sorter: (a, b) => a.prs_approved - b.prs_approved,
    },
  ]

  // Calculate summary stats
  const totalCommits = authors.reduce((sum, a) => sum + a.total_commits, 0)
  const totalLines = authors.reduce((sum, a) => sum + a.total_lines_changed, 0)
  const totalPRs = authors.reduce((sum, a) => sum + a.prs_created + a.prs_approved, 0)

  // Top 10 for charts
  const top10ByCommits = [...authors]
    .sort((a, b) => b.total_commits - a.total_commits)
    .slice(0, 10)

  if (loading && !authors.length) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading author statistics...">
          <div style={{ minHeight: '400px' }} />
        </Spin>
      </div>
    )
  }

  if (error && !authors.length) {
    return <Alert message="Error" description={error} type="error" showIcon />
  }

  return (
    <div>
      <div className="page-header">
        <Title level={2}>👨‍💻 Authors Analytics</Title>
      </div>

      {/* Date Range Filter */}
      <Card style={{ marginBottom: 24 }}>
        <Space size="large" wrap>
          <RangePicker
            value={dateRange}
            onChange={setDateRange}
            format="YYYY-MM-DD"
            style={{ width: 300 }}
          />
          <Button icon={<ReloadOutlined />} onClick={fetchAuthors} loading={loading}>
            Refresh
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleDownload} type="primary">
            Download CSV
          </Button>
        </Space>
      </Card>

      {/* Summary Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Authors"
              value={authors.length}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Commits"
              value={totalCommits}
              prefix={<CodeOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Lines Changed"
              value={totalLines}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total PRs"
              value={totalPRs}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Top 10 Chart */}
      <Card title="📊 Top 10 Contributors by Commits" style={{ marginBottom: 24 }}>
        <Column
          data={top10ByCommits.map((a) => ({
            author: a.author_name,
            commits: a.total_commits,
          }))}
          xField="author"
          yField="commits"
          label={{
            position: 'top',
            style: {
              fill: '#000',
              opacity: 0.6,
            },
          }}
          xAxis={{
            label: {
              autoRotate: true,
              autoHide: true,
            },
          }}
          meta={{
            commits: { alias: 'Commits' },
          }}
        />
      </Card>

      {/* Detailed Table */}
      <Card title="📋 Detailed Author Statistics">
        <Table
          columns={columns}
          dataSource={authors}
          rowKey="email"
          loading={loading}
          scroll={{ x: 1500 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} authors`,
          }}
        />
      </Card>
    </div>
  )
}

export default AuthorsAnalytics
