import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Button,
  Statistic,
  Typography,
  Space,
  Spin,
  Alert,
  message,
  Segmented,
  Tooltip,
  Tag,
  Tabs,
} from 'antd'
import {
  DownloadOutlined,
  ReloadOutlined,
  UserOutlined,
  CodeOutlined,
  BranchesOutlined,
  FileTextOutlined,
  BarChartOutlined,
  CalendarOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { Line, Column, Area } from '@ant-design/charts'
import { authorsAPI, staffAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const StaffProductivity = () => {
  // Filters
  const [staffList, setStaffList] = useState([])
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [granularity, setGranularity] = useState('monthly')
  const [dateRange, setDateRange] = useState([null, null])
  const [searchStaff, setSearchStaff] = useState('')

  // Data
  const [productivityData, setProductivityData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStaffList()
  }, [])

  const fetchStaffList = async () => {
    try {
      const data = await staffAPI.getStaffList({ limit: 1000 })
      setStaffList(data)
    } catch (err) {
      message.error('Failed to fetch staff list')
    }
  }

  const fetchProductivityData = async () => {
    if (!selectedStaff) {
      message.warning('Please select a staff member')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const params = {
        granularity,
      }

      if (dateRange[0]) params.start_date = dateRange[0].format('YYYY-MM-DD')
      if (dateRange[1]) params.end_date = dateRange[1].format('YYYY-MM-DD')

      const data = await authorsAPI.getProductivity(selectedStaff.bank_id_1, params)
      setProductivityData(data)
    } catch (err) {
      setError(err.message)
      message.error('Failed to fetch productivity data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedStaff) {
      fetchProductivityData()
    }
  }, [selectedStaff, granularity, dateRange])

  const handleClearFilters = () => {
    setDateRange([null, null])
    setGranularity('monthly')
  }

  const handleExportCSV = (dataType) => {
    if (!productivityData) return

    let csvData = []
    let filename = ''

    switch (dataType) {
      case 'commits':
        csvData = productivityData.timeseries.commits.map(row => ({
          Period: row.period,
          Commits: row.commits,
          'Lines Added': row.lines_added,
          'Lines Deleted': row.lines_deleted,
          'Files Changed': row.files_changed,
          'Repos Touched': row.repos_touched,
        }))
        filename = `${productivityData.staff.name}_commits_timeseries_${dayjs().format('YYYYMMDD')}.csv`
        break
      case 'prs':
        csvData = productivityData.timeseries.prs.map(row => ({
          Period: row.period,
          'PRs Opened': row.prs_opened,
        }))
        filename = `${productivityData.staff.name}_prs_timeseries_${dayjs().format('YYYYMMDD')}.csv`
        break
      case 'repos':
        csvData = productivityData.repository_breakdown.map(row => ({
          'Repository ID': row.repository_id,
          Commits: row.commits,
          'Lines Added': row.lines_added,
          'Lines Deleted': row.lines_deleted,
          'Files Changed': row.files_changed,
        }))
        filename = `${productivityData.staff.name}_repos_breakdown_${dayjs().format('YYYYMMDD')}.csv`
        break
      case 'calendar':
        csvData = productivityData.calendar_heatmap.map(row => ({
          Date: row.date,
          Commits: row.commits,
        }))
        filename = `${productivityData.staff.name}_calendar_heatmap_${dayjs().format('YYYYMMDD')}.csv`
        break
      default:
        return
    }

    if (csvData.length === 0) {
      message.warning('No data to export')
      return
    }

    const headers = Object.keys(csvData[0])
    const csv = [
      headers.join(','),
      ...csvData.map(row => headers.map(h => row[h] || 0).join(',')),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    message.success('CSV exported successfully!')
  }

  // Prepare chart data
  const commitsOverTimeData = productivityData?.timeseries.commits.map(row => ({
    period: row.period,
    value: row.commits,
    type: 'Commits',
  })) || []

  const linesChangedData = productivityData?.timeseries.commits.flatMap(row => [
    {
      period: row.period,
      value: row.lines_added,
      type: 'Lines Added',
    },
    {
      period: row.period,
      value: row.lines_deleted,
      type: 'Lines Deleted',
    },
  ]) || []

  const filesChangedData = productivityData?.timeseries.commits.map(row => ({
    period: row.period,
    value: row.files_changed,
  })) || []

  const reposTouchedData = productivityData?.timeseries.commits.map(row => ({
    period: row.period,
    value: row.repos_touched,
  })) || []

  const prActivityData = productivityData?.timeseries.prs.map(row => ({
    period: row.period,
    value: row.prs_opened,
  })) || []

  const repoBreakdownData = productivityData?.repository_breakdown.map(row => ({
    repository: `Repo ${row.repository_id}`,
    commits: row.commits,
    lines_added: row.lines_added,
    lines_deleted: row.lines_deleted,
    files_changed: row.files_changed,
  })) || []

  const calendarHeatmapData = productivityData?.calendar_heatmap || []

  // Calculate summary stats
  const totalCommits = productivityData?.timeseries.commits.reduce((sum, row) => sum + row.commits, 0) || 0
  const totalLinesAdded = productivityData?.timeseries.commits.reduce((sum, row) => sum + row.lines_added, 0) || 0
  const totalLinesDeleted = productivityData?.timeseries.commits.reduce((sum, row) => sum + row.lines_deleted, 0) || 0
  const totalPRs = productivityData?.timeseries.prs.reduce((sum, row) => sum + row.prs_opened, 0) || 0
  const uniqueRepos = productivityData?.repository_breakdown.length || 0

  if (loading && !productivityData) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading productivity data...">
          <div style={{ minHeight: '400px' }} />
        </Spin>
      </div>
    )
  }

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TrophyOutlined style={{ color: '#faad14' }} /> Staff Productivity Analytics
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Comprehensive productivity assessment for individual staff members
        </Text>
      </div>

      {/* Filters */}
      <Card title="🔍 Filters & Configuration" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} md={8}>
            <Text strong>Staff Member: <Text type="danger">*</Text></Text>
            <Select
              showSearch
              placeholder="Select staff member..."
              style={{ width: '100%', marginTop: 8 }}
              value={selectedStaff?.bank_id_1}
              onChange={(value) => {
                const staff = staffList.find(s => s.bank_id_1 === value)
                setSelectedStaff(staff)
              }}
              filterOption={(input, option) =>
                (option?.label?.toLowerCase() || '').includes(input.toLowerCase())
              }
              options={staffList
                .filter(s =>
                  !searchStaff ||
                  s.staff_name?.toLowerCase().includes(searchStaff.toLowerCase()) ||
                  s.email_address?.toLowerCase().includes(searchStaff.toLowerCase())
                )
                .map(s => ({
                  value: s.bank_id_1,
                  label: `${s.staff_name} (${s.email_address})`,
                }))}
            />
            {selectedStaff && (
              <div style={{ marginTop: 8 }}>
                <Tag color="blue">Rank: {selectedStaff.rank || 'N/A'}</Tag>
                <Tag color="cyan">Location: {selectedStaff.work_location || 'N/A'}</Tag>
              </div>
            )}
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Time Granularity:</Text>
            <Segmented
              options={[
                { label: 'Daily', value: 'daily' },
                { label: 'Weekly', value: 'weekly' },
                { label: 'Monthly', value: 'monthly' },
                { label: 'Yearly', value: 'yearly' },
              ]}
              value={granularity}
              onChange={setGranularity}
              block
              style={{ marginTop: 8 }}
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Date Range:</Text>
            <RangePicker
              value={dateRange}
              onChange={setDateRange}
              style={{ width: '100%', marginTop: 8 }}
              format="YYYY-MM-DD"
            />
          </Col>
        </Row>

        <Row style={{ marginTop: 16 }}>
          <Col span={24}>
            <Space>
              <Button onClick={fetchProductivityData} icon={<ReloadOutlined />} type="primary">
                Refresh
              </Button>
              <Button onClick={handleClearFilters}>Clear Filters</Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {error && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 24 }} />}

      {!selectedStaff && !productivityData && (
        <Alert
          message="No Staff Selected"
          description="Please select a staff member from the dropdown above to view their productivity analytics."
          type="info"
          showIcon
        />
      )}

      {productivityData && (
        <>
          {/* Staff Info Card */}
          <Card title="👤 Staff Profile" style={{ marginBottom: 24 }}>
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Text type="secondary">Name</Text>
                <div><Text strong>{productivityData.staff.name}</Text></div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text type="secondary">Bank ID</Text>
                <div><Tag color="blue">{productivityData.staff.bank_id}</Tag></div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text type="secondary">Rank</Text>
                <div><Tag color="purple">{productivityData.staff.rank || 'N/A'}</Tag></div>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Text type="secondary">Location</Text>
                <div><Tag color="cyan">{productivityData.staff.location || 'N/A'}</Tag></div>
              </Col>
            </Row>
          </Card>

          {/* Summary Statistics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Total Commits"
                  value={totalCommits}
                  prefix={<CodeOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Lines Added"
                  value={totalLinesAdded}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Lines Deleted"
                  value={totalLinesDeleted}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Total PRs"
                  value={totalPRs}
                  prefix={<BranchesOutlined />}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Repos Touched"
                  value={uniqueRepos}
                  prefix={<BranchesOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={4}>
              <Card>
                <Statistic
                  title="Avg Commits/{granularity}"
                  value={(totalCommits / (productivityData.timeseries.commits.length || 1)).toFixed(1)}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Time-Series Charts */}
          <Tabs
            defaultActiveKey="1"
            items={[
              {
                key: '1',
                label: 'Commits Over Time',
                children: (
                  <Card
                    title="📈 Commits Over Time"
                    extra={
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleExportCSV('commits')}
                      >
                        Export CSV
                      </Button>
                    }
                  >
                    <Line
                      data={commitsOverTimeData}
                      xField="period"
                      yField="value"
                      seriesField="type"
                      smooth
                      point={{
                        size: 4,
                        shape: 'circle',
                      }}
                      tooltip={{
                        shared: true,
                      }}
                      animation={{
                        appear: {
                          animation: 'path-in',
                          duration: 1000,
                        },
                      }}
                      xAxis={{
                        label: {
                          autoRotate: true,
                          autoHide: true,
                        },
                      }}
                    />
                  </Card>
                ),
              },
              {
                key: '2',
                label: 'Lines Changed',
                children: (
                  <Card
                    title="📊 Lines Changed Over Time"
                    extra={
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleExportCSV('commits')}
                      >
                        Export CSV
                      </Button>
                    }
                  >
                    <Column
                      data={linesChangedData}
                      isStack
                      xField="period"
                      yField="value"
                      seriesField="type"
                      color={['#52c41a', '#ff4d4f']}
                      columnStyle={{
                        radius: [4, 4, 0, 0],
                      }}
                      legend={{
                        position: 'top-right',
                      }}
                      xAxis={{
                        label: {
                          autoRotate: true,
                          autoHide: true,
                        },
                      }}
                    />
                  </Card>
                ),
              },
              {
                key: '3',
                label: 'Files Changed',
                children: (
                  <Card title="📁 Files Changed Over Time">
                    <Area
                      data={filesChangedData}
                      xField="period"
                      yField="value"
                      smooth
                      areaStyle={{
                        fill: 'l(270) 0:#ffffff 1:#1890ff',
                      }}
                      xAxis={{
                        label: {
                          autoRotate: true,
                          autoHide: true,
                        },
                      }}
                    />
                  </Card>
                ),
              },
              {
                key: '4',
                label: 'Repos Touched',
                children: (
                  <Card title="🗂️ Repositories Touched Over Time">
                    <Column
                      data={reposTouchedData}
                      xField="period"
                      yField="value"
                      color="#faad14"
                      columnStyle={{
                        radius: [4, 4, 0, 0],
                      }}
                      xAxis={{
                        label: {
                          autoRotate: true,
                          autoHide: true,
                        },
                      }}
                    />
                  </Card>
                ),
              },
              {
                key: '5',
                label: 'PR Activity',
                children: (
                  <Card
                    title="🔀 Pull Request Activity"
                    extra={
                      <Button
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={() => handleExportCSV('prs')}
                      >
                        Export CSV
                      </Button>
                    }
                  >
                    <Line
                      data={prActivityData}
                      xField="period"
                      yField="value"
                      color="#722ed1"
                      smooth
                      point={{
                        size: 5,
                        shape: 'diamond',
                      }}
                      xAxis={{
                        label: {
                          autoRotate: true,
                          autoHide: true,
                        },
                      }}
                    />
                  </Card>
                ),
              },
            ]}
          />

          {/* Repository Breakdown */}
          <Card
            title="📦 Repository Breakdown"
            style={{ marginTop: 24 }}
            extra={
              <Button
                size="small"
                icon={<DownloadOutlined />}
                onClick={() => handleExportCSV('repos')}
              >
                Export CSV
              </Button>
            }
          >
            <Column
              data={repoBreakdownData}
              xField="repository"
              yField="commits"
              color="#13c2c2"
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
              tooltip={{
                customContent: (title, items) => {
                  if (!items || items.length === 0) return null
                  const data = items[0]?.data
                  return (
                    <div style={{ padding: '8px' }}>
                      <div><strong>{title}</strong></div>
                      <div>Commits: {data?.commits}</div>
                      <div>Lines Added: {data?.lines_added}</div>
                      <div>Lines Deleted: {data?.lines_deleted}</div>
                      <div>Files Changed: {data?.files_changed}</div>
                    </div>
                  )
                },
              }}
            />
          </Card>

          {/* Calendar Heatmap - Only for daily granularity */}
          {granularity === 'daily' && calendarHeatmapData.length > 0 && (
            <Card
              title="📅 Commit Calendar Heatmap"
              style={{ marginTop: 24 }}
              extra={
                <Button
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={() => handleExportCSV('calendar')}
                >
                  Export CSV
                </Button>
              }
            >
              <div style={{ overflowX: 'auto' }}>
                {calendarHeatmapData.map((day, index) => (
                  <Tooltip key={index} title={`${day.date}: ${day.commits} commits`}>
                    <div
                      style={{
                        display: 'inline-block',
                        width: 12,
                        height: 12,
                        margin: 1,
                        backgroundColor:
                          day.commits === 0
                            ? '#ebedf0'
                            : day.commits < 3
                            ? '#9be9a8'
                            : day.commits < 5
                            ? '#40c463'
                            : day.commits < 10
                            ? '#30a14e'
                            : '#216e39',
                        borderRadius: 2,
                      }}
                    />
                  </Tooltip>
                ))}
              </div>
              <div style={{ marginTop: 16 }}>
                <Text type="secondary">
                  <Space>
                    <div style={{ width: 12, height: 12, backgroundColor: '#ebedf0', display: 'inline-block' }} />
                    0
                    <div style={{ width: 12, height: 12, backgroundColor: '#9be9a8', display: 'inline-block' }} />
                    1-2
                    <div style={{ width: 12, height: 12, backgroundColor: '#40c463', display: 'inline-block' }} />
                    3-4
                    <div style={{ width: 12, height: 12, backgroundColor: '#30a14e', display: 'inline-block' }} />
                    5-9
                    <div style={{ width: 12, height: 12, backgroundColor: '#216e39', display: 'inline-block' }} />
                    10+
                  </Space>
                </Text>
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  )
}

export default StaffProductivity
