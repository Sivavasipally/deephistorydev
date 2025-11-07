import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Spin,
  Alert,
  Typography,
  Select,
  Space,
  Tag,
  Tooltip,
  Row,
  Col,
  Statistic,
  message,
} from 'antd'
import {
  TrophyOutlined,
  CodeOutlined,
  UserOutlined,
  CalendarOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import { Column } from '@ant-design/charts'
import { commitsAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography

const TopCommits = () => {
  const [commits, setCommits] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [limit, setLimit] = useState(10)

  useEffect(() => {
    fetchTopCommits()
  }, [limit])

  const fetchTopCommits = async () => {
    try {
      setLoading(true)
      const data = await commitsAPI.getTopByLines({ limit })
      setCommits(data)
      setError(null)
    } catch (err) {
      setError(err.message)
      message.error('Failed to fetch top commits')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '#',
      key: 'rank',
      width: 60,
      render: (_, __, index) => (
        <Tag color={index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? 'bronze' : 'blue'}>
          {index + 1}
        </Tag>
      ),
    },
    {
      title: 'Commit Hash',
      dataIndex: 'commit_hash',
      key: 'commit_hash',
      width: 120,
      render: (hash, record) => (
        <Tooltip title={record.full_hash}>
          <Tag color="blue" style={{ fontFamily: 'monospace' }}>
            {hash}
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: 'Author',
      dataIndex: 'author',
      key: 'author',
      width: 150,
      render: (author) => (
        <Space>
          <UserOutlined />
          <Text>{author}</Text>
        </Space>
      ),
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      width: 180,
      render: (date) => (
        <Space>
          <CalendarOutlined />
          <Text>{dayjs(date).format('YYYY-MM-DD HH:mm')}</Text>
        </Space>
      ),
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
      render: (message) => (
        <Tooltip title={message}>
          <Text>{message}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'Lines Added',
      dataIndex: 'lines_added',
      key: 'lines_added',
      width: 120,
      align: 'right',
      render: (val) => <Tag color="success">+{val.toLocaleString()}</Tag>,
    },
    {
      title: 'Lines Deleted',
      dataIndex: 'lines_deleted',
      key: 'lines_deleted',
      width: 120,
      align: 'right',
      render: (val) => <Tag color="error">-{val.toLocaleString()}</Tag>,
    },
    {
      title: 'Total Lines',
      dataIndex: 'total_lines',
      key: 'total_lines',
      width: 130,
      align: 'right',
      sorter: (a, b) => a.total_lines - b.total_lines,
      defaultSortOrder: 'descend',
      render: (val) => (
        <Tag color="purple" style={{ fontSize: 14, fontWeight: 'bold' }}>
          {val.toLocaleString()}
        </Tag>
      ),
    },
    {
      title: 'Files',
      dataIndex: 'files_changed',
      key: 'files_changed',
      width: 80,
      align: 'right',
      render: (val) => (
        <Space>
          <FileTextOutlined />
          <Text>{val}</Text>
        </Space>
      ),
    },
    {
      title: 'Repository',
      dataIndex: 'repository',
      key: 'repository',
      width: 200,
      render: (repo) => (
        <Tag color="cyan" icon={<CodeOutlined />}>
          {repo}
        </Tag>
      ),
    },
  ]

  // Calculate summary stats
  const totalLinesChanged = commits.reduce((sum, c) => sum + c.total_lines, 0)
  const totalFilesChanged = commits.reduce((sum, c) => sum + c.files_changed, 0)
  const avgLinesPerCommit = commits.length > 0 ? Math.round(totalLinesChanged / commits.length) : 0

  // Prepare chart data for grouped column chart
  const chartData = commits.flatMap((commit, index) => [
    {
      commit: `#${index + 1}`,
      value: commit.lines_added,
      type: 'Lines Added',
    },
    {
      commit: `#${index + 1}`,
      value: commit.lines_deleted,
      type: 'Lines Deleted',
    },
  ])

  if (loading && !commits.length) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading top commits...">
          <div style={{ minHeight: '400px' }} />
        </Spin>
      </div>
    )
  }

  if (error && !commits.length) {
    return <Alert message="Error" description={error} type="error" showIcon />
  }

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TrophyOutlined style={{ color: '#faad14' }} /> Top Commits by Lines Changed
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Commits with the most code changes (additions + deletions)
        </Text>
      </div>

      {/* Controls */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>Show Top:</Text>
          <Select value={limit} onChange={setLimit} style={{ width: 120 }}>
            <Select.Option value={5}>Top 5</Select.Option>
            <Select.Option value={10}>Top 10</Select.Option>
            <Select.Option value={20}>Top 20</Select.Option>
            <Select.Option value={50}>Top 50</Select.Option>
            <Select.Option value={100}>Top 100</Select.Option>
          </Select>
        </Space>
      </Card>

      {/* Summary Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Commits"
              value={commits.length}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Lines Changed"
              value={totalLinesChanged}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Files Changed"
              value={totalFilesChanged}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Lines/Commit"
              value={avgLinesPerCommit}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Chart */}
      <Card title="📊 Visual Breakdown" style={{ marginBottom: 24 }}>
        <Column
          data={chartData}
          isGroup
          xField="commit"
          yField="value"
          seriesField="type"
          columnStyle={{
            radius: [8, 8, 0, 0],
          }}
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
          legend={{
            position: 'top-right',
          }}
          meta={{
            value: { alias: 'Lines' },
          }}
        />
      </Card>

      {/* Detailed Table */}
      <Card title="🏆 Top Commits Ranking">
        <Table
          columns={columns}
          dataSource={commits}
          rowKey="full_hash"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} commits`,
          }}
        />
      </Card>
    </div>
  )
}

export default TopCommits
