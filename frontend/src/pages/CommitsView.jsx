import React, { useEffect, useState } from 'react'
import { Card, Table, Input, Select, DatePicker, Button, Space, message, Tag, Typography } from 'antd'
import { SearchOutlined, DownloadOutlined } from '@ant-design/icons'
import { commitsAPI } from '../services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Title } = Typography

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
      title: 'Repository',
      dataIndex: 'repository',
      key: 'repository',
      width: 150,
    },
  ]

  return (
    <div>
      <Title level={2}>📝 Commits View</Title>

      <Card style={{ marginBottom: 24 }}>
        <Space wrap>
          <Input
            placeholder="Search author..."
            prefix={<SearchOutlined />}
            onChange={(e) => setFilters({ ...filters, author: e.target.value })}
            style={{ width: 200 }}
          />
          <Button type="primary" onClick={fetchCommits} loading={loading}>
            Search
          </Button>
          <Button icon={<DownloadOutlined />}>Download CSV</Button>
        </Space>
      </Card>

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
