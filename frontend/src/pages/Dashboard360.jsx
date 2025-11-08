import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Tabs,
  Select,
  DatePicker,
  Segmented,
  Typography,
  Statistic,
  Table,
  Tag,
  Space,
  message,
  Alert,
  Tooltip,
  Progress,
} from 'antd'
import {
  DashboardOutlined,
  UserOutlined,
  TeamOutlined,
  GlobalOutlined,
  ClockCircleOutlined,
  FireOutlined,
  RocketOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { Line, Column, Area, Heatmap, Scatter, Funnel } from '@ant-design/charts'
import { authorsAPI, staffAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const Dashboard360 = () => {
  // Filters
  const [staffList, setStaffList] = useState([])
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [selectedRepo, setSelectedRepo] = useState(null)
  const [granularity, setGranularity] = useState('monthly')
  const [dateRange, setDateRange] = useState([null, null])

  // Advanced Filters
  const [filterRank, setFilterRank] = useState(null)
  const [filterLocation, setFilterLocation] = useState(null)
  const [filterStaffType, setFilterStaffType] = useState(null)
  const [filterManager, setFilterManager] = useState(null)
  const [filterSubPlatform, setFilterSubPlatform] = useState(null)

  // Data states
  const [developerData, setDeveloperData] = useState(null)
  const [repoData, setRepoData] = useState(null)
  const [orgData, setOrgData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Active dashboard type
  const [dashboardType, setDashboardType] = useState('developer')

  // Filter options
  const rankOptions = [...new Set(staffList.map(s => s.rank).filter(Boolean))].map(rank => ({ label: rank, value: rank }))
  const locationOptions = [...new Set(staffList.map(s => s.work_location).filter(Boolean))].map(loc => ({ label: loc, value: loc }))
  const staffTypeOptions = [...new Set(staffList.map(s => s.staff_type).filter(Boolean))].map(type => ({ label: type, value: type }))
  const managerOptions = [...new Set(staffList.map(s => s.reporting_manager_name).filter(Boolean))].map(mgr => ({ label: mgr, value: mgr }))
  const subPlatformOptions = [...new Set(staffList.map(s => s.sub_platform).filter(Boolean))].map(sp => ({ label: sp, value: sp }))

  // Filtered staff list
  const filteredStaffList = staffList.filter(staff => {
    if (filterRank && staff.rank !== filterRank) return false
    if (filterLocation && staff.work_location !== filterLocation) return false
    if (filterStaffType && staff.staff_type !== filterStaffType) return false
    if (filterManager && staff.reporting_manager_name !== filterManager) return false
    if (filterSubPlatform && staff.sub_platform !== filterSubPlatform) return false
    return true
  })

  useEffect(() => {
    fetchStaffList()
  }, [])

  const fetchStaffList = async () => {
    try {
      const response = await staffAPI.getStaffList({ limit: 1000 })
      setStaffList(response)
    } catch (err) {
      message.error(`Failed to fetch staff list: ${err.message}`)
    }
  }

  const fetchDashboardData = async () => {
    if (dashboardType === 'developer' && !selectedStaff) {
      message.warning('Please select a staff member for Developer 360 Dashboard')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const params = {
        granularity,
        start_date: dateRange[0] ? dayjs(dateRange[0]).format('YYYY-MM-DD') : undefined,
        end_date: dateRange[1] ? dayjs(dateRange[1]).format('YYYY-MM-DD') : undefined,
      }

      if (dashboardType === 'developer') {
        const data = await authorsAPI.getProductivity(selectedStaff, params)
        setDeveloperData(data)
      } else if (dashboardType === 'repo') {
        // Fetch repo/team data
        // TODO: Implement repo-specific API call
        message.info('Repo 360 Dashboard - Coming soon')
      } else if (dashboardType === 'org') {
        // Fetch org overview data
        // TODO: Implement org overview API call
        message.info('Org Overview Dashboard - Coming soon')
      }
    } catch (err) {
      setError(err.message)
      message.error(`Failed to fetch dashboard data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleClearFilters = () => {
    setSelectedStaff(null)
    setSelectedRepo(null)
    setDateRange([null, null])
    setGranularity('monthly')
    setFilterRank(null)
    setFilterLocation(null)
    setFilterStaffType(null)
    setFilterManager(null)
    setFilterSubPlatform(null)
    setDeveloperData(null)
    setRepoData(null)
    setOrgData(null)
  }

  // Developer 360 Dashboard Components
  const renderDeveloper360 = () => {
    if (!developerData) {
      return (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Text type="secondary">Select a developer and fetch data to view the 360° Dashboard</Text>
        </div>
      )
    }

    // Prepare trend data
    const commitsTrendData = developerData.timeseries.commits.map(item => ({
      period: item.period,
      value: item.commits,
      type: 'Commits',
    }))

    const prsTrendData = developerData.timeseries.prs.flatMap(item => [
      { period: item.period, value: item.prs_opened, type: 'PRs Opened' },
      { period: item.period, value: item.prs_merged, type: 'PRs Merged' },
    ])

    const mergeRateData = developerData.timeseries.prs.map(item => ({
      period: item.period,
      rate: item.prs_opened > 0 ? (item.prs_merged / item.prs_opened * 100) : 0,
    }))

    // Calendar heatmap data - day of week x hour
    const calendarData = []
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    const hours = Array.from({ length: 24 }, (_, i) => `${i}:00`)

    // Generate sample heatmap data (in production, this would come from actual commit times)
    days.forEach(day => {
      hours.forEach(hour => {
        calendarData.push({
          day,
          hour,
          commits: Math.floor(Math.random() * 10), // Replace with actual data
        })
      })
    })

    // Repository focus data
    const repoFocusData = developerData.repository_breakdown.map(repo => ({
      repository: repo.slug_name,
      commits: repo.commits,
      ownership: repo.commits, // Percentage of repo commits
    }))

    return (
      <div>
        {/* Key Metrics */}
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Total Commits"
                value={developerData.summary.total_commits}
                prefix={<FireOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Total PRs"
                value={developerData.summary.total_prs}
                prefix={<RocketOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Merge Rate"
                value={developerData.summary.merge_rate * 100}
                precision={1}
                suffix="%"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col xs={12} sm={8} md={6}>
            <Card>
              <Statistic
                title="Repositories"
                value={developerData.repository_breakdown.length}
                prefix={<GlobalOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Trends */}
        <Card title="📈 Productivity Trends" style={{ marginBottom: 24 }}>
          <Tabs
            items={[
              {
                key: '1',
                label: 'Commits & PRs',
                children: (
                  <Line
                    data={[...commitsTrendData, ...prsTrendData]}
                    xField="period"
                    yField="value"
                    seriesField="type"
                    smooth
                    point={{
                      size: 5,
                      shape: 'circle',
                    }}
                    legend={{ position: 'top-right' }}
                    xAxis={{
                      title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                      label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                    }}
                    yAxis={{
                      title: { text: 'Count', style: { fontSize: 14, fontWeight: 'bold' } },
                      label: { style: { fontSize: 12 } }
                    }}
                    tooltip={{
                      showTitle: true,
                      customContent: (title, data) => {
                        if (!data || data.length === 0) return null
                        return `
                          <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px;">
                            <div style="font-weight: bold; margin-bottom: 8px;">📅 ${title}</div>
                            ${data.map(item => `
                              <div style="margin: 4px 0;">
                                <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                <strong>${item.name}:</strong> <span style="font-weight: bold; color: ${item.color};">${item.value}</span>
                              </div>
                            `).join('')}
                          </div>
                        `
                      }
                    }}
                  />
                ),
              },
              {
                key: '2',
                label: 'Merge Rate Trend',
                children: (
                  <Line
                    data={mergeRateData}
                    xField="period"
                    yField="rate"
                    smooth
                    point={{ size: 5, shape: 'diamond' }}
                    color="#52c41a"
                    xAxis={{
                      title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                      label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                    }}
                    yAxis={{
                      title: { text: 'Merge Rate (%)', style: { fontSize: 14, fontWeight: 'bold' } },
                      label: { style: { fontSize: 12 } },
                      min: 0,
                      max: 100,
                    }}
                    annotations={[
                      {
                        type: 'line',
                        start: ['min', 80],
                        end: ['max', 80],
                        style: {
                          stroke: '#52c41a',
                          lineDash: [4, 4],
                        },
                        text: {
                          content: 'Target: 80%',
                          position: 'end',
                          style: { fill: '#52c41a', fontSize: 12 },
                        },
                      },
                    ]}
                    tooltip={{
                      customContent: (title, data) => {
                        if (!data || data.length === 0) return null
                        const item = data[0]
                        return `
                          <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px;">
                            <div style="font-weight: bold; margin-bottom: 8px;">📅 ${title}</div>
                            <div>Merge Rate: <strong style="color: #52c41a;">${item.value.toFixed(1)}%</strong></div>
                          </div>
                        `
                      }
                    }}
                  />
                ),
              },
            ]}
          />
        </Card>

        {/* Calendar Heatmap */}
        <Card title="📅 Activity Calendar - Commits by Day & Hour" style={{ marginBottom: 24 }}>
          <Heatmap
            data={calendarData}
            xField="hour"
            yField="day"
            colorField="commits"
            color={['#f7fbff', '#deebf7', '#c6dbef', '#9ecae1', '#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b']}
            legend={{
              position: 'bottom',
            }}
            xAxis={{
              title: { text: 'Hour of Day', style: { fontSize: 14, fontWeight: 'bold' } },
              label: { style: { fontSize: 10 } }
            }}
            yAxis={{
              title: { text: 'Day of Week', style: { fontSize: 14, fontWeight: 'bold' } },
            }}
            tooltip={{
              customContent: (title, data) => {
                if (!data || data.length === 0) return null
                const item = data[0].data
                return `
                  <div style="padding: 10px; background: white; border: 1px solid #ddd; border-radius: 4px;">
                    <div style="font-weight: bold;">${item.day} at ${item.hour}</div>
                    <div style="margin-top: 4px;">Commits: <strong style="color: #1890ff;">${item.commits}</strong></div>
                  </div>
                `
              }
            }}
          />
        </Card>

        {/* Repository Focus */}
        <Card title="🎯 Repository Focus & Ownership" style={{ marginBottom: 24 }}>
          <Column
            data={repoFocusData}
            xField="repository"
            yField="commits"
            label={{
              position: 'top',
              style: { fill: '#000', fontSize: 12 },
              formatter: (v) => v.commits,
            }}
            color="#1890ff"
            xAxis={{
              title: { text: 'Repository', style: { fontSize: 14, fontWeight: 'bold' } },
              label: { autoRotate: true, autoHide: true, style: { fontSize: 11 } }
            }}
            yAxis={{
              title: { text: 'Number of Commits', style: { fontSize: 14, fontWeight: 'bold' } },
            }}
            tooltip={{
              customContent: (title, data) => {
                if (!data || data.length === 0) return null
                const item = data[0].data
                return `
                  <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px;">
                    <div style="font-weight: bold; margin-bottom: 8px;">📦 ${item.repository}</div>
                    <div>Total Commits: <strong style="color: #1890ff;">${item.commits}</strong></div>
                  </div>
                `
              }
            }}
          />
        </Card>

        {/* Reviews Section */}
        <Row gutter={[16, 16]}>
          <Col xs={24} md={12}>
            <Card title="👥 Code Reviews Given">
              <Text type="secondary">Coming soon: Reviews given statistics</Text>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card title="📝 Code Reviews Received">
              <Text type="secondary">Coming soon: Reviews received statistics</Text>
            </Card>
          </Col>
        </Row>
      </div>
    )
  }

  // Repo/Team 360 Dashboard
  const renderRepo360 = () => {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>Repo/Team 360° Dashboard</Title>
        <Text type="secondary">Select a repository to view comprehensive team analytics</Text>
      </div>
    )
  }

  // Org Overview Dashboard
  const renderOrgOverview = () => {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Title level={3}>Organization Overview Dashboard</Title>
        <Text type="secondary">Organization-wide productivity metrics and insights</Text>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <Title level={2}>
          <DashboardOutlined style={{ color: '#1890ff' }} /> 360° Dashboards
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Comprehensive multi-dimensional analytics for developers, teams, and organization
        </Text>
      </div>

      {/* Error Display */}
      {error && (
        <Alert
          message="Error Loading Data"
          description={error}
          type="error"
          closable
          onClose={() => setError(null)}
          style={{ marginBottom: 24 }}
          showIcon
        />
      )}

      {/* Dashboard Type Selector */}
      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Text strong style={{ marginBottom: 8, display: 'block' }}>Select Dashboard Type:</Text>
            <Segmented
              options={[
                { label: '👤 Developer 360', value: 'developer', icon: <UserOutlined /> },
                { label: '📦 Repo/Team 360', value: 'repo', icon: <TeamOutlined /> },
                { label: '🌍 Org Overview', value: 'org', icon: <GlobalOutlined /> },
              ]}
              value={dashboardType}
              onChange={setDashboardType}
              block
              size="large"
            />
          </div>
        </Space>
      </Card>

      {/* Filters */}
      <Card title="🔍 Filters & Configuration" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {/* Advanced Filters */}
          <Col xs={24} md={8}>
            <Text strong>Rank:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by rank..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterRank}
              onChange={setFilterRank}
              options={rankOptions}
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Location:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by location..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterLocation}
              onChange={setFilterLocation}
              options={locationOptions}
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Staff Type:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by staff type..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterStaffType}
              onChange={setFilterStaffType}
              options={staffTypeOptions}
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Manager:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by manager..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterManager}
              onChange={setFilterManager}
              options={managerOptions}
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Sub Platform:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by sub platform..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterSubPlatform}
              onChange={setFilterSubPlatform}
              options={subPlatformOptions}
            />
          </Col>

          {/* Developer Selection (for Developer 360) */}
          {dashboardType === 'developer' && (
            <Col xs={24} md={8}>
              <Text strong>Select Developer: <Text type="danger">*</Text></Text>
              <Select
                showSearch
                placeholder="Select a developer..."
                style={{ width: '100%', marginTop: 8 }}
                value={selectedStaff}
                onChange={setSelectedStaff}
                filterOption={(input, option) =>
                  (option?.label?.toLowerCase() || '').includes(input.toLowerCase())
                }
                options={filteredStaffList.map(s => ({
                  value: s.bank_id_1,
                  label: `${s.staff_name} (${s.rank || 'N/A'})`,
                }))}
              />
            </Col>
          )}

          {/* Date Range */}
          <Col xs={24} md={8}>
            <Text strong>Date Range:</Text>
            <RangePicker
              style={{ width: '100%', marginTop: 8 }}
              value={dateRange}
              onChange={setDateRange}
              format="YYYY-MM-DD"
            />
          </Col>

          {/* Granularity */}
          <Col xs={24} md={8}>
            <Text strong>Granularity:</Text>
            <Segmented
              options={['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']}
              value={granularity.charAt(0).toUpperCase() + granularity.slice(1)}
              onChange={(value) => setGranularity(value.toLowerCase())}
              block
              style={{ marginTop: 8 }}
            />
          </Col>

          {/* Action Buttons */}
          <Col xs={24}>
            <Space>
              <button
                onClick={fetchDashboardData}
                disabled={loading}
                className="primary-button"
              >
                {loading ? 'Loading...' : '📊 Fetch Dashboard Data'}
              </button>
              <button onClick={handleClearFilters} className="secondary-button">
                Clear Filters
              </button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Dashboard Content */}
      {loading ? (
        <Card loading={true} style={{ minHeight: 400 }} />
      ) : (
        <>
          {dashboardType === 'developer' && renderDeveloper360()}
          {dashboardType === 'repo' && renderRepo360()}
          {dashboardType === 'org' && renderOrgOverview()}
        </>
      )}
    </div>
  )
}

export default Dashboard360
