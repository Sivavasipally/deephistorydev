import React, { useEffect, useState } from 'react'
import { Card, Table, Input, Select, DatePicker, Button, Space, message, Tag, Typography, Collapse, Row, Col, Tooltip } from 'antd'
import { SearchOutlined, DownloadOutlined, DownOutlined, FilterOutlined } from '@ant-design/icons'
import { commitsAPI } from '../services/api'
import dayjs from 'dayjs'
import { formatFileTypes } from '../utils/fileTypeUtils'

const { RangePicker } = DatePicker
const { Title, Text } = Typography

const CommitsView = () => {
  const [commits, setCommits] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({})

  useEffect(() => {
    fetchCommits()
  }, [])

  const fetchCommits = async () => {
    try {
      setLoading(true)
      const data = await commitsAPI.getCommits({ limit: 100, ...filters })
      setCommits(data)
    } catch (err) {
      message.error('Failed to fetch commits')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: 'Hash',
      dataIndex: 'commit_hash',
      key: 'commit_hash',
      width: 100,
      render: (hash) => <Tag color="blue">{hash.substring(0, 8)}</Tag>,
    },
    {
      title: 'Author',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 150,
    },
    {
      title: 'Date',
      dataIndex: 'commit_date',
      key: 'commit_date',
      width: 180,
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
    {
      title: 'Lines +',
      dataIndex: 'lines_added',
      key: 'lines_added',
      width: 100,
      render: (val) => <Tag color="success">+{val}</Tag>,
    },
    {
      title: 'Lines -',
      dataIndex: 'lines_deleted',
      key: 'lines_deleted',
      width: 100,
      render: (val) => <Tag color="error">-{val}</Tag>,
    },
    {
      title: 'Files',
      dataIndex: 'files_changed',
      key: 'files_changed',
      width: 80,
    },
    {
      title: 'File Types',
      dataIndex: 'file_types',
      key: 'file_types',
      width: 180,
      render: (fileTypes) => {
        if (!fileTypes) return <Tag>-</Tag>
        const formatted = formatFileTypes(fileTypes)
        return (
          <Space wrap size={[0, 4]}>
            {formatted.slice(0, 3).map((ft, idx) => (
              <Tag key={idx} color={ft.color} style={{ fontSize: 11 }}>
                {ft.label}
              </Tag>
            ))}
            {formatted.length > 3 && (
              <Tooltip title={formatted.slice(3).map(ft => ft.label).join(', ')}>
                <Tag style={{ fontSize: 11 }}>+{formatted.length - 3}</Tag>
              </Tooltip>
            )}
          </Space>
        )
      },
    },
    {
      title: 'Characters',
      key: 'chars',
      width: 140,
      render: (_, record) => (
        <Tooltip title={`Added: ${record.chars_added || 0} | Deleted: ${record.chars_deleted || 0}`}>
          <Space size={4}>
            <Text type="success" style={{ fontSize: 12 }}>+{record.chars_added || 0}</Text>
            <Text type="secondary">/</Text>
            <Text type="danger" style={{ fontSize: 12 }}>-{record.chars_deleted || 0}</Text>
          </Space>
        </Tooltip>
      ),
      sorter: (a, b) =>
        ((a.chars_added || 0) + (a.chars_deleted || 0)) - ((b.chars_added || 0) + (b.chars_deleted || 0)),
    },
    {
      title: 'Repository',
      dataIndex: 'repository',
      key: 'repository',
      width: 150,
    },
  ]

  const hasActiveFilters = filters.author || filters.file_type

  return (
    <div>
      <Title level={2}>📝 Commits View</Title>

      <Collapse
        defaultActiveKey={[]}
        style={{ marginBottom: 24 }}
        expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
      >
        <Collapse.Panel
          header={
            <Space>
              <FilterOutlined />
              <span>Filters</span>
              {hasActiveFilters && <Tag color="blue">Active</Tag>}
            </Space>
          }
          key="1"
        >
          <Space wrap>
            <Input
              placeholder="Search author..."
              prefix={<SearchOutlined />}
              onChange={(e) => setFilters({ ...filters, author: e.target.value })}
              style={{ width: 200 }}
            />
            <Select
              placeholder="Filter by file type"
              allowClear
              style={{ width: 200 }}
              onChange={(value) => setFilters({ ...filters, file_type: value })}
              options={[
                { label: 'All Files', value: null },
                { label: '📝 Code Files', value: 'code' },
                { label: '⚙️ Configuration', value: 'config' },
                { label: '📚 Documentation', value: 'docs' },
                { label: '☕ Java', value: 'java' },
                { label: '📜 JavaScript', value: 'js' },
                { label: '⚛️ React JSX', value: 'jsx' },
                { label: '🔷 TypeScript', value: 'tsx' },
                { label: '📋 YAML', value: 'yml' },
                { label: '📄 XML', value: 'xml' },
                { label: '🐍 Python', value: 'py' },
              ]}
            />
            <Button type="primary" onClick={fetchCommits} loading={loading}>
              Search
            </Button>
            <Button icon={<DownloadOutlined />}>Download CSV</Button>
          </Space>
        </Collapse.Panel>
      </Collapse>

      {/* Data Explanation Header */}
      {!loading && (
        <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
          <Row align="middle" gutter={16}>
            <Col flex="auto">
              <Space direction="vertical" size={4}>
                <Text strong style={{ color: '#fff', fontSize: 16 }}>
                  📝 Commits History Dashboard
                </Text>
                <Text style={{ color: '#f0f0f0', fontSize: 13 }}>
                  {filters.author && `Showing commits by author: ${filters.author}`}
                  {!filters.author && 'Comprehensive commit history across all repositories showing code changes, contributors, and development activity'}
                </Text>
              </Space>
            </Col>
            <Col>
              <Space>
                <Tag color="blue" style={{ fontSize: 12 }}>
                  {commits.length} Commits
                </Tag>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={commits}
          rowKey="commit_hash"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  )
}

export default CommitsView
