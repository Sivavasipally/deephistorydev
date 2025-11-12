import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Input,
  Select,
  DatePicker,
  Button,
  Space,
  message,
  Tag,
  Typography,
  Row,
  Col,
  Statistic,
  Tooltip,
  Badge,
  Collapse,
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  ReloadOutlined,
  PullRequestOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BranchesOutlined,
  FileTextOutlined,
  DownOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { pullRequestsAPI } from '../services/api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Title, Text } = Typography

const PullRequestsView = () => {
  const [pullRequests, setPullRequests] = useState([])
  const [loading, setLoading] = useState(false)
  const [filters, setFilters] = useState({})
  const [searchAuthor, setSearchAuthor] = useState('')
  const [searchRepo, setSearchRepo] = useState('')
  const [selectedState, setSelectedState] = useState(null)
  const [dateRange, setDateRange] = useState([
    dayjs().startOf('year'),
    dayjs()
  ])

  useEffect(() => {
    fetchPullRequests()
  }, [])

  const fetchPullRequests = async () => {
    try {
      setLoading(true)
      const params = {
        limit: 100,
        ...filters,
      }

      if (searchAuthor) params.author = searchAuthor
      if (searchRepo) params.repository = searchRepo
      if (selectedState) params.state = selectedState
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD')
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD')

      const data = await pullRequestsAPI.getPullRequests(params)
      setPullRequests(data)
    } catch (err) {
      message.error('Failed to fetch pull requests')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = () => {
    fetchPullRequests()
  }

  const handleReset = () => {
    setSearchAuthor('')
    setSearchRepo('')
    setSelectedState(null)
    setDateRange([null, null])
    setFilters({})
    setTimeout(() => fetchPullRequests(), 100)
  }

  const handleDownload = () => {
    const headers = [
      'PR Number',
      'Title',
      'Author',
      'State',
      'Created Date',
      'Merged Date',
      'Repository',
      'Lines Added',
      'Lines Deleted',
      'Commits',
      'Approvals',
    ]
    const csv = [
      headers.join(','),
      ...pullRequests.map((pr) =>
        [
          pr.pr_number,
          `"${pr.title.replace(/"/g, '""')}"`,
          pr.author_name,
          pr.state,
          pr.created_date,
          pr.merged_date || '',
          `${pr.project_key}/${pr.repository}`,
          pr.lines_added,
          pr.lines_deleted,
          pr.commits_count,
          pr.approvals_count,
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pull_requests_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  const columns = [
    {
      title: 'PR #',
      dataIndex: 'pr_number',
      key: 'pr_number',
      width: 80,
      fixed: 'left',
      render: (num) => <Tag color="blue">#{num}</Tag>,
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      width: 300,
      ellipsis: true,
      render: (title) => (
        <Tooltip title={title}>
          <Text strong>{title}</Text>
        </Tooltip>
      ),
    },
    {
      title: 'State',
      dataIndex: 'state',
      key: 'state',
      width: 100,
      filters: [
        { text: 'MERGED', value: 'MERGED' },
        { text: 'OPEN', value: 'OPEN' },
        { text: 'DECLINED', value: 'DECLINED' },
      ],
      onFilter: (value, record) => record.state === value,
      render: (state) => {
        const colors = {
          MERGED: 'success',
          OPEN: 'processing',
          DECLINED: 'error',
          CLOSED: 'default',
        }
        const icons = {
          MERGED: <CheckCircleOutlined />,
          OPEN: <ClockCircleOutlined />,
          DECLINED: <ClockCircleOutlined />,
        }
        return (
          <Tag color={colors[state] || 'default'} icon={icons[state]}>
            {state}
          </Tag>
        )
      },
    },
    {
      title: 'Author',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Created',
      dataIndex: 'created_date',
      key: 'created_date',
      width: 180,
      sorter: (a, b) => new Date(a.created_date) - new Date(b.created_date),
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Merged',
      dataIndex: 'merged_date',
      key: 'merged_date',
      width: 180,
      render: (date) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : <Text type="secondary">-</Text>,
    },
    {
      title: 'Source → Target',
      key: 'branches',
      width: 250,
      render: (_, record) => (
        <Space size="small">
          <Tag icon={<BranchesOutlined />} color="cyan">
            {record.source_branch}
          </Tag>
          →
          <Tag icon={<BranchesOutlined />} color="purple">
            {record.target_branch}
          </Tag>
        </Space>
      ),
    },
    {
      title: 'Lines +/-',
      key: 'lines',
      width: 140,
      render: (_, record) => (
        <Space>
          <Tag color="success">+{record.lines_added}</Tag>
          <Tag color="error">-{record.lines_deleted}</Tag>
        </Space>
      ),
    },
    {
      title: 'Commits',
      dataIndex: 'commits_count',
      key: 'commits_count',
      width: 90,
      align: 'center',
      render: (count) => <Badge count={count} showZero color="#1890ff" />,
    },
    {
      title: 'Approvals',
      dataIndex: 'approvals_count',
      key: 'approvals_count',
      width: 100,
      align: 'center',
      render: (count) => <Badge count={count} showZero color="#52c41a" />,
    },
    {
      title: 'Repository',
      key: 'repository',
      width: 200,
      render: (_, record) => (
        <Tag color="geekblue" icon={<FileTextOutlined />}>
          {record.project_key}/{record.repository}
        </Tag>
      ),
    },
  ]

  // Calculate summary stats
  const totalPRs = pullRequests.length
  const mergedPRs = pullRequests.filter((pr) => pr.state === 'MERGED').length
  const openPRs = pullRequests.filter((pr) => pr.state === 'OPEN').length
  const totalApprovals = pullRequests.reduce((sum, pr) => sum + pr.approvals_count, 0)

  const hasActiveFilters = searchAuthor || searchRepo || selectedState || dateRange[0] || dateRange[1]

  return (
    <div>
      <Title level={2}>
        <PullRequestOutlined style={{ color: '#1890ff' }} /> Pull Requests View
      </Title>

      {/* Filters */}
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
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={8} lg={6}>
                <Input
                  placeholder="Search author..."
                  prefix={<SearchOutlined />}
                  value={searchAuthor}
                  onChange={(e) => setSearchAuthor(e.target.value)}
                  onPressEnter={handleSearch}
                />
              </Col>
              <Col xs={24} sm={12} md={8} lg={6}>
                <Input
                  placeholder="Search repository..."
                  prefix={<SearchOutlined />}
                  value={searchRepo}
                  onChange={(e) => setSearchRepo(e.target.value)}
                  onPressEnter={handleSearch}
                />
              </Col>
              <Col xs={24} sm={12} md={8} lg={6}>
                <Select
                  style={{ width: '100%' }}
                  placeholder="Filter by state"
                  allowClear
                  value={selectedState}
                  onChange={setSelectedState}
                >
                  <Select.Option value="MERGED">Merged</Select.Option>
                  <Select.Option value="OPEN">Open</Select.Option>
                  <Select.Option value="DECLINED">Declined</Select.Option>
                </Select>
              </Col>
              <Col xs={24} sm={12} md={8} lg={6}>
                <RangePicker
                  style={{ width: '100%' }}
                  value={dateRange}
                  onChange={setDateRange}
                  format="YYYY-MM-DD"
                />
              </Col>
            </Row>
            <Row gutter={[8, 8]}>
              <Col>
                <Button type="primary" icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>
                  Search
                </Button>
              </Col>
              <Col>
                <Button icon={<ReloadOutlined />} onClick={handleReset}>
                  Reset
                </Button>
              </Col>
              <Col>
                <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                  Download CSV
                </Button>
              </Col>
            </Row>
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
                  📋 Pull Requests Analytics Dashboard
                </Text>
                <Text style={{ color: '#f0f0f0', fontSize: 13 }}>
                  {searchAuthor && !searchRepo && !selectedState && `Showing pull requests by author: ${searchAuthor}`}
                  {searchRepo && !searchAuthor && !selectedState && `Showing pull requests for repository: ${searchRepo}`}
                  {selectedState && !searchAuthor && !searchRepo && `Showing ${selectedState.toLowerCase()} pull requests`}
                  {searchAuthor && searchRepo && `Showing pull requests by ${searchAuthor} in ${searchRepo}`}
                  {searchAuthor && selectedState && !searchRepo && `Showing ${selectedState.toLowerCase()} pull requests by ${searchAuthor}`}
                  {searchRepo && selectedState && !searchAuthor && `Showing ${selectedState.toLowerCase()} pull requests in ${searchRepo}`}
                  {searchAuthor && searchRepo && selectedState && `Showing ${selectedState.toLowerCase()} pull requests by ${searchAuthor} in ${searchRepo}`}
                  {!searchAuthor && !searchRepo && !selectedState && 'Comprehensive view of all pull requests across repositories including merge status, code changes, and approval metrics'}
                </Text>
              </Space>
            </Col>
            <Col>
              <Space>
                {dateRange[0] && dateRange[1] && (
                  <Tag color="purple" style={{ fontSize: 12 }}>
                    {dateRange[0].format('MMM D, YYYY')} - {dateRange[1].format('MMM D, YYYY')}
                  </Tag>
                )}
                <Tag color="blue" style={{ fontSize: 12 }}>
                  {pullRequests.length} PRs
                </Tag>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* Summary Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total PRs"
              value={totalPRs}
              prefix={<PullRequestOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Merged"
              value={mergedPRs}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Open"
              value={openPRs}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Approvals"
              value={totalApprovals}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={pullRequests}
          rowKey={(record) => `${record.pr_number}-${record.repository}`}
          loading={loading}
          scroll={{ x: 1800 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} pull requests`,
          }}
        />
      </Card>
    </div>
  )
}

export default PullRequestsView
