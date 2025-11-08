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
  Tag,
  Tooltip,
} from 'antd'
import {
  DownloadOutlined,
  ReloadOutlined,
  TrophyOutlined,
  CodeOutlined,
  LineChartOutlined,
  TeamOutlined,
  UserOutlined,
  BankOutlined,
  EnvironmentOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { Column } from '@ant-design/charts'
import { authorsAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const AuthorsAnalyticsEnhanced = () => {
  const [authors, setAuthors] = useState([])
  const [filterOptions, setFilterOptions] = useState({
    ranks: [],
    reporting_managers: [],
    work_locations: [],
    staff_types: []
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dateRange, setDateRange] = useState([null, null])

  // New filters
  const [selectedRank, setSelectedRank] = useState(null)
  const [selectedManager, setSelectedManager] = useState(null)
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [selectedStaffType, setSelectedStaffType] = useState(null)

  useEffect(() => {
    fetchFilterOptions()
  }, [])

  useEffect(() => {
    fetchAuthors()
  }, [dateRange, selectedRank, selectedManager, selectedLocation, selectedStaffType])

  const fetchFilterOptions = async () => {
    try {
      const options = await authorsAPI.getFilterOptions()
      setFilterOptions(options)
    } catch (err) {
      console.error('Failed to fetch filter options:', err)
    }
  }

  const fetchAuthors = async () => {
    try {
      setLoading(true)
      const params = {}
      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD')
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD')
      if (selectedRank) params.rank = selectedRank
      if (selectedManager) params.reporting_manager = selectedManager
      if (selectedLocation) params.work_location = selectedLocation
      if (selectedStaffType) params.staff_type = selectedStaffType

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

  const clearFilters = () => {
    setDateRange([null, null])
    setSelectedRank(null)
    setSelectedManager(null)
    setSelectedLocation(null)
    setSelectedStaffType(null)
  }

  const handleDownload = () => {
    const headers = [
      'Author Name',
      'Email',
      'Staff Name',
      'Bank ID',
      'Rank',
      'Reporting Manager',
      'Work Location',
      'Staff Type',
      'Total Commits',
      'Lines Added',
      'Lines Deleted',
      'Total Lines',
      'Files Changed',
      'Repositories',
      'PRs Created',
      'PRs Approved',
      'Mapped',
    ]
    const csv = [
      headers.join(','),
      ...authors.map((a) =>
        [
          a.author_name,
          a.email,
          a.staff_name || '',
          a.bank_id || '',
          a.rank || '',
          a.reporting_manager_name || '',
          a.work_location || '',
          a.staff_type || '',
          a.total_commits,
          a.lines_added,
          a.lines_deleted,
          a.total_lines_changed,
          a.files_changed,
          a.repositories_count,
          a.prs_created,
          a.prs_approved,
          a.is_mapped ? 'Yes' : 'No',
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `author_statistics_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  const columns = [
    {
      title: 'Staff Name',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 200,
      fixed: 'left',
      sorter: (a, b) => a.author_name.localeCompare(b.author_name),
      render: (name, record) => (
        <Space direction="vertical" size={0}>
          <Space>
            <UserOutlined />
            <Text strong>{name}</Text>
          </Space>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 250,
      ellipsis: true,
    },
    {
      title: 'Bank ID',
      dataIndex: 'bank_id',
      key: 'bank_id',
      width: 100,
      render: (id) => id ? <Tag color="blue" icon={<BankOutlined />}>{id}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: 'Rank',
      dataIndex: 'rank',
      key: 'rank',
      width: 120,
      render: (rank) => rank ? <Tag color="purple">{rank}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: 'Manager',
      dataIndex: 'reporting_manager_name',
      key: 'reporting_manager_name',
      width: 180,
      ellipsis: true,
      render: (manager) => manager || <Text type="secondary">-</Text>,
    },
    {
      title: 'Location',
      dataIndex: 'work_location',
      key: 'work_location',
      width: 150,
      render: (location) => location ? (
        <Tag color="cyan" icon={<EnvironmentOutlined />}>{location}</Tag>
      ) : <Text type="secondary">-</Text>,
    },
    {
      title: 'Staff Type',
      dataIndex: 'staff_type',
      key: 'staff_type',
      width: 120,
      render: (type) => type ? <Tag color="orange">{type}</Tag> : <Text type="secondary">-</Text>,
    },
    {
      title: 'Commits',
      dataIndex: 'total_commits',
      key: 'total_commits',
      width: 100,
      align: 'right',
      sorter: (a, b) => a.total_commits - b.total_commits,
      defaultSortOrder: 'descend',
      render: (val) => <Tag color="blue">{val.toLocaleString()}</Tag>,
    },
    {
      title: 'Lines Changed',
      dataIndex: 'total_lines_changed',
      key: 'total_lines_changed',
      width: 140,
      align: 'right',
      sorter: (a, b) => a.total_lines_changed - b.total_lines_changed,
      render: (val) => <Tag color="purple">{val.toLocaleString()}</Tag>,
    },
    {
      title: 'Files',
      dataIndex: 'files_changed',
      key: 'files_changed',
      width: 100,
      align: 'right',
      sorter: (a, b) => a.files_changed - b.files_changed,
      render: (val) => val.toLocaleString(),
    },
    {
      title: 'Repos',
      dataIndex: 'repositories_count',
      key: 'repositories_count',
      width: 80,
      align: 'right',
      render: (val) => val,
    },
    {
      title: 'PRs',
      dataIndex: 'prs_created',
      key: 'prs_created',
      width: 80,
      align: 'right',
      render: (val) => val,
    },
    {
      title: 'Approvals',
      dataIndex: 'prs_approved',
      key: 'prs_approved',
      width: 100,
      align: 'right',
      render: (val) => val,
    },
  ]

  // Calculate statistics
  const totalCommits = authors.reduce((sum, a) => sum + a.total_commits, 0)
  const totalLinesChanged = authors.reduce((sum, a) => sum + a.total_lines_changed, 0)
  const mappedAuthors = authors.filter(a => a.is_mapped).length
  const mappingRate = authors.length > 0 ? ((mappedAuthors / authors.length) * 100).toFixed(1) : 0

  // Prepare chart data - top 10 by commits
  const top10ByCommits = [...authors]
    .sort((a, b) => b.total_commits - a.total_commits)
    .slice(0, 10)

  const chartData = top10ByCommits.flatMap((author) => [
    {
      author: author.author_name,
      value: author.lines_added,
      type: 'Lines Added',
    },
    {
      author: author.author_name,
      value: author.lines_deleted,
      type: 'Lines Deleted',
    },
  ])

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

  const hasActiveFilters = selectedRank || selectedManager || selectedLocation || selectedStaffType || dateRange[0] || dateRange[1]

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TeamOutlined style={{ color: '#52c41a' }} /> Staff Analytics
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Comprehensive Git contribution statistics by staff members (mapped authors only)
        </Text>
      </div>

      {/* Filters */}
      <Card title={<Space><FilterOutlined /> Filters</Space>} style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12} lg={6}>
            <Text strong>Date Range:</Text>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%', marginTop: 8 }}
              format="YYYY-MM-DD"
            />
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Text strong>Rank:</Text>
            <Select
              allowClear
              placeholder="Select rank"
              value={selectedRank}
              onChange={setSelectedRank}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Select.Option value={null}>All</Select.Option>
              {filterOptions.ranks.map(rank => (
                <Select.Option key={rank} value={rank}>{rank}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Text strong>Reporting Manager:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Select manager"
              value={selectedManager}
              onChange={setSelectedManager}
              style={{ width: '100%', marginTop: 8 }}
              filterOption={(input, option) =>
                (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
              }
            >
              <Select.Option value={null}>All</Select.Option>
              {filterOptions.reporting_managers.map(manager => (
                <Select.Option key={manager} value={manager}>{manager}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Text strong>Work Location:</Text>
            <Select
              allowClear
              placeholder="Select location"
              value={selectedLocation}
              onChange={setSelectedLocation}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Select.Option value={null}>All</Select.Option>
              {filterOptions.work_locations.map(location => (
                <Select.Option key={location} value={location}>{location}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <Text strong>Staff Type:</Text>
            <Select
              allowClear
              placeholder="Select staff type"
              value={selectedStaffType}
              onChange={setSelectedStaffType}
              style={{ width: '100%', marginTop: 8 }}
            >
              <Select.Option value={null}>All</Select.Option>
              {filterOptions.staff_types.map(type => (
                <Select.Option key={type} value={type}>{type}</Select.Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} md={12} lg={6}>
            <div style={{ marginTop: 28 }}>
              <Space>
                <Button onClick={fetchAuthors} icon={<ReloadOutlined />}>
                  Refresh
                </Button>
                {hasActiveFilters && (
                  <Button onClick={clearFilters}>
                    Clear Filters
                  </Button>
                )}
              </Space>
            </div>
          </Col>
        </Row>
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
              value={totalLinesChanged}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Staff"
              value={authors.length}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Staff with mapped Git activity
            </Text>
          </Card>
        </Col>
      </Row>

      {/* Chart */}
      {chartData.length > 0 && (
        <Card title="Top 10 Staff - Code Changes" style={{ marginBottom: 24 }}>
          <Column
            data={chartData}
            isGroup
            xField="author"
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
      )}

      {/* Detailed Table */}
      <Card
        title="Staff Contribution Details"
        extra={
          <Button icon={<DownloadOutlined />} onClick={handleDownload}>
            Download CSV
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={authors}
          rowKey="email"
          loading={loading}
          scroll={{ x: 2000 }}
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

export default AuthorsAnalyticsEnhanced
