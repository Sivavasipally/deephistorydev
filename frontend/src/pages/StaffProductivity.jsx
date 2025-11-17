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
  Collapse,
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
  QuestionCircleOutlined,
  DownOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { Line, Column, Area, Radar, Pie } from '@ant-design/charts'
import { authorsAPI, staffAPI } from '../services/api'
import dayjs from 'dayjs'
import {
  getTopFileTypes,
  getCodeVsNonCodeRatio,
  getLanguageExpertise,
  getCategoryColor,
  formatFileTypes
} from '../utils/fileTypeUtils'
import {
  exportMultipleSheetsToExcel,
  prepareStaffProductivityExport
} from '../utils/excelExport'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const StaffProductivity = () => {
  // Filters
  const [staffList, setStaffList] = useState([])
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [granularity, setGranularity] = useState('quarterly')
  const [dateRange, setDateRange] = useState([
    dayjs().startOf('year'),
    dayjs()
  ])
  const [searchStaff, setSearchStaff] = useState('')

  // Data
  const [productivityData, setProductivityData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Analytics Data
  const [fileTypeStats, setFileTypeStats] = useState(null)
  const [characterMetrics, setCharacterMetrics] = useState(null)
  const [fileTypeDistribution, setFileTypeDistribution] = useState(null)

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

      // Fetch analytics data
      await Promise.all([
        fetchFileTypeAnalytics(),
        fetchCharacterMetrics(),
        fetchFileTypeDistribution()
      ])
    } catch (err) {
      setError(err.message)
      message.error('Failed to fetch productivity data')
    } finally {
      setLoading(false)
    }
  }

  const fetchFileTypeAnalytics = async () => {
    if (!selectedStaff) return

    try {
      const params = new URLSearchParams({
        staff_id: selectedStaff.bank_id_1,
        limit: 10
      })

      if (dateRange[0]) params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
      if (dateRange[1]) params.append('end_date', dateRange[1].format('YYYY-MM-DD'))

      const response = await fetch(`/api/analytics/file-types/top?${params}`)
      const data = await response.json()
      setFileTypeStats(data)
    } catch (err) {
      console.error('Error fetching file type stats:', err)
    }
  }

  const fetchCharacterMetrics = async () => {
    if (!selectedStaff) return

    try {
      const params = new URLSearchParams({
        staff_id: selectedStaff.bank_id_1
      })

      if (dateRange[0]) params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
      if (dateRange[1]) params.append('end_date', dateRange[1].format('YYYY-MM-DD'))

      const response = await fetch(`/api/analytics/characters/metrics?${params}`)
      const data = await response.json()
      setCharacterMetrics(data)
    } catch (err) {
      console.error('Error fetching character metrics:', err)
    }
  }

  const fetchFileTypeDistribution = async () => {
    if (!selectedStaff) return

    try {
      const params = new URLSearchParams({
        staff_id: selectedStaff.bank_id_1
      })

      if (dateRange[0]) params.append('start_date', dateRange[0].format('YYYY-MM-DD'))
      if (dateRange[1]) params.append('end_date', dateRange[1].format('YYYY-MM-DD'))

      const response = await fetch(`/api/analytics/file-types/distribution?${params}`)
      const data = await response.json()
      setFileTypeDistribution(data)
    } catch (err) {
      console.error('Error fetching file type distribution:', err)
    }
  }

  useEffect(() => {
    if (selectedStaff) {
      fetchProductivityData()
    }
  }, [selectedStaff, granularity, dateRange])

  const handleClearFilters = () => {
    setDateRange([null, null])
    setGranularity('quarterly')
  }

  const handleExportToExcel = () => {
    if (!productivityData) {
      message.warning('No data available to export')
      return
    }

    const sheets = prepareStaffProductivityExport(productivityData, fileTypeStats, characterMetrics)
    const filename = `${productivityData.staff.name}_productivity_${dayjs().format('YYYYMMDD')}`

    exportMultipleSheetsToExcel(sheets, filename)
    message.success('Excel file exported successfully!')
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
  const totalFilesChanged = productivityData?.timeseries.commits.reduce((sum, row) => sum + row.files_changed, 0) || 0

  // Developer DNA Radar Chart Data - normalized scores (0-100)
  const calculateRadarData = () => {
    if (!productivityData) return []

    // Calculate average values per period for normalization
    const avgCommitsPerPeriod = totalCommits / (productivityData.timeseries.commits.length || 1)
    const avgLinesPerPeriod = (totalLinesAdded + totalLinesDeleted) / (productivityData.timeseries.commits.length || 1)
    const avgFilesPerPeriod = totalFilesChanged / (productivityData.timeseries.commits.length || 1)
    const avgPRsPerPeriod = totalPRs / (productivityData.timeseries.prs.length || 1)

    // Normalize to 0-100 scale (using reasonable max values)
    const commitFrequency = Math.min(100, (avgCommitsPerPeriod / 10) * 100) // 10 commits per period = 100
    const codeVolume = Math.min(100, (avgLinesPerPeriod / 500) * 100) // 500 lines per period = 100
    const fileScope = Math.min(100, (avgFilesPerPeriod / 20) * 100) // 20 files per period = 100
    const prActivity = Math.min(100, (avgPRsPerPeriod / 5) * 100) // 5 PRs per period = 100
    const repoBreadth = Math.min(100, (uniqueRepos / 10) * 100) // 10 repos = 100
    const codeChurn = Math.min(100, (totalLinesDeleted / (totalLinesAdded || 1)) * 100) // 100% deletion rate = 100

    return [
      { metric: 'Commit Frequency', value: commitFrequency },
      { metric: 'Code Volume', value: codeVolume },
      { metric: 'File Scope', value: fileScope },
      { metric: 'PR Activity', value: prActivity },
      { metric: 'Repo Breadth', value: repoBreadth },
      { metric: 'Code Churn', value: codeChurn },
    ]
  }

  const radarData = calculateRadarData()

  if (loading && !productivityData) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading productivity data...">
          <div style={{ minHeight: '400px' }} />
        </Spin>
      </div>
    )
  }

  const hasActiveFilters = selectedStaff || dateRange[0] || dateRange[1] || granularity !== 'quarterly'

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
      <Collapse
        defaultActiveKey={[]}
        style={{ marginBottom: 24 }}
        expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
      >
        <Collapse.Panel
          header={
            <Space>
              <FilterOutlined />
              <span>Filters & Configuration</span>
              {hasActiveFilters && <Tag color="blue">Active</Tag>}
            </Space>
          }
          key="1"
        >
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
                  { label: 'Quarterly', value: 'quarterly' },
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
                {productivityData && (
                  <Button
                    onClick={handleExportToExcel}
                    icon={<DownloadOutlined />}
                    type="default"
                  >
                    Export to Excel
                  </Button>
                )}
              </Space>
            </Col>
          </Row>
        </Collapse.Panel>
      </Collapse>

      {/* Data Explanation Header */}
      {!loading && selectedStaff && productivityData && (
        <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
          <Row align="middle" gutter={16}>
            <Col flex="auto">
              <Space direction="vertical" size={4}>
                <Text strong style={{ color: '#fff', fontSize: 16 }}>
                  📈 Individual Productivity Dashboard - {productivityData.staff.name || selectedStaff.staff_name}
                </Text>
                <Text style={{ color: '#f0f0f0', fontSize: 13 }}>
                  Analyzing {granularity} productivity trends and contribution metrics for {productivityData.staff.rank || selectedStaff.rank || 'staff member'} in {productivityData.staff.work_location || selectedStaff.work_location || 'the organization'}
                </Text>
              </Space>
            </Col>
            <Col>
              <Space>
                <Tag color="blue" style={{ fontSize: 12 }}>
                  {granularity.charAt(0).toUpperCase() + granularity.slice(1)} View
                </Tag>
                {dateRange[0] && dateRange[1] && (
                  <Tag color="purple" style={{ fontSize: 12 }}>
                    {dateRange[0].format('MMM D, YYYY')} - {dateRange[1].format('MMM D, YYYY')}
                  </Tag>
                )}
              </Space>
            </Col>
          </Row>
        </Card>
      )}

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

          {/* Progress Rings */}
          <Card title="🎯 Activity Rings - Daily Goals" style={{ marginBottom: 24 }}>
            <Row gutter={[24, 24]} justify="center">
              <Col xs={24} sm={8}>
                <Tooltip
                  title={
                    <div>
                      <strong>Commits Ring</strong>
                      <div>Track your commit activity goal. Each period should aim for 10 commits to achieve 100% completion.</div>
                      <div style={{ marginTop: 4 }}>Current: {(totalCommits / (productivityData.timeseries.commits.length || 1)).toFixed(1)} commits/{granularity}</div>
                    </div>
                  }
                  placement="top"
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ position: 'relative', display: 'inline-block' }}>
                      {(() => {
                        const avgPerPeriod = totalCommits / (productivityData.timeseries.commits.length || 1)
                        const progress = Math.min(100, (avgPerPeriod / 10) * 100)
                        return (
                          <svg width="120" height="120" viewBox="0 0 120 120">
                            <circle
                              cx="60"
                              cy="60"
                              r="50"
                              fill="none"
                              stroke="#f0f0f0"
                              strokeWidth="10"
                            />
                            <circle
                              cx="60"
                              cy="60"
                              r="50"
                              fill="none"
                              stroke="#1890ff"
                              strokeWidth="10"
                              strokeDasharray={`${(progress / 100) * 314.16} 314.16`}
                              strokeLinecap="round"
                              transform="rotate(-90 60 60)"
                            />
                          </svg>
                        )
                      })()}
                      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                        <Text strong style={{ fontSize: 20 }}>{Math.min(100, (totalCommits / (productivityData.timeseries.commits.length * 10)) * 100).toFixed(0)}%</Text>
                      </div>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Text strong>Commits Ring</Text>
                      <br />
                      <Text type="secondary">Goal: 10/{granularity}</Text>
                    </div>
                  </div>
                </Tooltip>
              </Col>
              <Col xs={24} sm={8}>
                <Tooltip
                  title={
                    <div>
                      <strong>Pull Requests Ring</strong>
                      <div>Track your PR collaboration goal. Creating and participating in 5 PRs per period shows active code review involvement.</div>
                      <div style={{ marginTop: 4 }}>Current: {(totalPRs / (productivityData.timeseries.prs.length || 1)).toFixed(1)} PRs/{granularity}</div>
                    </div>
                  }
                  placement="top"
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ position: 'relative', display: 'inline-block' }}>
                      <svg width="120" height="120" viewBox="0 0 120 120">
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke="#f0f0f0"
                          strokeWidth="10"
                        />
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke="#52c41a"
                          strokeWidth="10"
                          strokeDasharray={`${(Math.min(100, (totalPRs / (productivityData.timeseries.prs.length * 5)) * 100) / 100) * 314.16} 314.16`}
                          strokeLinecap="round"
                          transform="rotate(-90 60 60)"
                        />
                      </svg>
                      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                        <Text strong style={{ fontSize: 20 }}>{Math.min(100, (totalPRs / (productivityData.timeseries.prs.length * 5)) * 100).toFixed(0)}%</Text>
                      </div>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Text strong>PRs Ring</Text>
                      <br />
                      <Text type="secondary">Goal: 5/{granularity}</Text>
                    </div>
                  </div>
                </Tooltip>
              </Col>
              <Col xs={24} sm={8}>
                <Tooltip
                  title={
                    <div>
                      <strong>Collaboration Ring</strong>
                      <div>Track your cross-repository involvement. Contributing to 10 different repositories demonstrates versatility and team collaboration.</div>
                      <div style={{ marginTop: 4 }}>Current: {uniqueRepos} repositories</div>
                    </div>
                  }
                  placement="top"
                >
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ position: 'relative', display: 'inline-block' }}>
                      <svg width="120" height="120" viewBox="0 0 120 120">
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke="#f0f0f0"
                          strokeWidth="10"
                        />
                        <circle
                          cx="60"
                          cy="60"
                          r="50"
                          fill="none"
                          stroke="#faad14"
                          strokeWidth="10"
                          strokeDasharray={`${(Math.min(100, (uniqueRepos / 10) * 100) / 100) * 314.16} 314.16`}
                          strokeLinecap="round"
                          transform="rotate(-90 60 60)"
                        />
                      </svg>
                      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)' }}>
                        <Text strong style={{ fontSize: 20 }}>{Math.min(100, (uniqueRepos / 10) * 100).toFixed(0)}%</Text>
                      </div>
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <Text strong>Collaboration Ring</Text>
                      <br />
                      <Text type="secondary">Goal: 10 repos</Text>
                    </div>
                  </div>
                </Tooltip>
              </Col>
            </Row>
            <Alert
              message="Close Your Rings Daily!"
              description="Aim to complete all three rings each day: consistent commits, active PR participation, and broad collaboration across repositories."
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>

          {/* Achievement Badges */}
          <Card title="🏆 Achievement Badges & Milestones" style={{ marginBottom: 24 }}>
            <Row gutter={[16, 16]}>
              {(() => {
                const badges = []
                const periods = productivityData.timeseries.commits.length
                const avgCommitsPerPeriod = totalCommits / periods

                // Commit Streak Badge
                if (avgCommitsPerPeriod >= 10) {
                  badges.push({
                    icon: '🔥',
                    title: 'Commit Streak Master',
                    description: `${avgCommitsPerPeriod.toFixed(0)} avg commits per period`,
                    color: '#ff4d4f',
                  })
                }

                // High Volume Contributor
                if (totalCommits >= 100) {
                  badges.push({
                    icon: '💯',
                    title: 'Century Club',
                    description: `${totalCommits} total commits`,
                    color: '#faad14',
                  })
                }

                // Code Volume Champion
                if (totalLinesAdded + totalLinesDeleted >= 10000) {
                  badges.push({
                    icon: '📝',
                    title: 'Code Volume Champion',
                    description: `${((totalLinesAdded + totalLinesDeleted) / 1000).toFixed(1)}K lines changed`,
                    color: '#52c41a',
                  })
                }

                // PR Master
                if (totalPRs >= 20) {
                  badges.push({
                    icon: '🎯',
                    title: 'PR Master',
                    description: `${totalPRs} pull requests opened`,
                    color: '#722ed1',
                  })
                }

                // Cross-Project Collaborator
                if (uniqueRepos >= 5) {
                  badges.push({
                    icon: '🤝',
                    title: 'Cross-Project Collaborator',
                    description: `Active in ${uniqueRepos} repositories`,
                    color: '#13c2c2',
                  })
                }

                // Refactoring Hero
                if (totalLinesDeleted > totalLinesAdded * 0.5) {
                  badges.push({
                    icon: '🧹',
                    title: 'Refactoring Hero',
                    description: `${((totalLinesDeleted / (totalLinesAdded || 1)) * 100).toFixed(0)}% deletion ratio`,
                    color: '#1890ff',
                  })
                }

                // Consistency Champion
                const avgCommits = totalCommits / periods
                const commitConsistency = (1 - (Math.sqrt(productivityData.timeseries.commits.reduce((sum, r) => sum + Math.pow(r.commits - avgCommits, 2), 0) / periods) / (avgCommits || 1))) * 100
                if (commitConsistency > 70) {
                  badges.push({
                    icon: '⚡',
                    title: 'Consistency Champion',
                    description: `${commitConsistency.toFixed(0)}% consistency score`,
                    color: '#eb2f96',
                  })
                }

                // Quality First (if PR merge rate is high - uses actual merge data)
                const mergeRate = productivityData.summary?.merge_rate || 0
                if (mergeRate > 0.75 && totalPRs >= 5) {
                  badges.push({
                    icon: '✅',
                    title: 'Quality First',
                    description: `${(mergeRate * 100).toFixed(0)}% PR merge rate`,
                    color: '#52c41a',
                  })
                }

                return badges.length > 0 ? (
                  badges.map((badge, index) => (
                    <Col xs={12} sm={8} md={6} lg={4} key={index}>
                      <Card
                        style={{
                          textAlign: 'center',
                          borderColor: badge.color,
                          borderWidth: 2,
                          background: `linear-gradient(135deg, ${badge.color}22, ${badge.color}11)`,
                        }}
                      >
                        <div style={{ fontSize: 40 }}>{badge.icon}</div>
                        <Title level={5} style={{ marginTop: 8, marginBottom: 4, color: badge.color }}>
                          {badge.title}
                        </Title>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {badge.description}
                        </Text>
                      </Card>
                    </Col>
                  ))
                ) : (
                  <Col span={24}>
                    <div style={{ textAlign: 'center', padding: '20px' }}>
                      <Text type="secondary">
                        🌟 Keep contributing to unlock achievement badges! Reach milestones in commits, PRs, code volume, and consistency.
                      </Text>
                    </div>
                  </Col>
                )
              })()}
            </Row>
          </Card>

          {/* Summary Statistics */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Total Commits"
                  value={totalCommits}
                  prefix={<CodeOutlined />}
                  valueStyle={{ color: '#1890ff', fontSize: '18px' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Lines Added"
                  value={totalLinesAdded}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#52c41a', fontSize: '18px' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Lines Deleted"
                  value={totalLinesDeleted}
                  prefix={<FileTextOutlined />}
                  valueStyle={{ color: '#ff4d4f', fontSize: '18px' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Characters Added"
                  value={characterMetrics?.total_chars_added || 0}
                  valueStyle={{ color: '#52c41a', fontSize: '18px' }}
                  prefix={<CodeOutlined />}
                  suffix={
                    <Tooltip title="Total characters added across all commits">
                      <QuestionCircleOutlined style={{ fontSize: 12 }} />
                    </Tooltip>
                  }
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Avg Chars/Commit"
                  value={characterMetrics?.avg_chars_per_commit || 0}
                  valueStyle={{ color: '#1890ff', fontSize: '18px' }}
                  prefix={<FileTextOutlined />}
                  precision={0}
                  suffix={
                    <Tooltip title="Average characters per commit">
                      <QuestionCircleOutlined style={{ fontSize: 12 }} />
                    </Tooltip>
                  }
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Total PRs"
                  value={totalPRs}
                  prefix={<BranchesOutlined />}
                  valueStyle={{ color: '#722ed1', fontSize: '18px' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title="Repos Touched"
                  value={uniqueRepos}
                  prefix={<BranchesOutlined />}
                  valueStyle={{ color: '#faad14', fontSize: '18px' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={12} md={8} lg={4}>
              <Card>
                <Statistic
                  title={`Avg Commits/${granularity}`}
                  value={(totalCommits / (productivityData.timeseries.commits.length || 1)).toFixed(1)}
                  prefix={<BarChartOutlined />}
                  valueStyle={{ color: '#13c2c2', fontSize: '18px' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Developer DNA Radar Chart */}
          <Card title="🧬 Developer DNA - Performance Profile" style={{ marginBottom: 24 }}>
            <Row gutter={[24, 24]}>
              <Col xs={24} lg={12}>
                <Radar
                  data={radarData}
                  xField="metric"
                  yField="value"
                  appendPadding={[0, 10, 0, 10]}
                  meta={{
                    value: {
                      alias: 'Score',
                      min: 0,
                      max: 100,
                    },
                  }}
                  xAxis={{
                    line: null,
                    tickLine: null,
                    grid: {
                      line: {
                        style: {
                          lineDash: null,
                        },
                      },
                    },
                  }}
                  yAxis={{
                    line: null,
                    tickLine: null,
                    grid: {
                      line: {
                        type: 'line',
                        style: {
                          lineDash: null,
                        },
                      },
                      alternateColor: 'rgba(0, 0, 0, 0.04)',
                    },
                  }}
                  point={{
                    size: 4,
                  }}
                  area={{}}
                  color="#1890ff"
                  tooltip={{
                    customContent: (title, data) => {
                      if (!data || data.length === 0) return null
                      const item = data[0]
                      const metricExplanations = {
                        'Commit Frequency': 'Average commits per period. Higher scores indicate consistent code contributions. (10+ commits/period = 100%)',
                        'Code Volume': 'Total lines changed per period. Measures overall code output volume. (500+ lines/period = 100%)',
                        'File Scope': 'Average files modified per period. Shows breadth of work across the codebase. (20+ files/period = 100%)',
                        'PR Activity': 'Pull requests opened per period. Indicates collaboration and code review activity. (5+ PRs/period = 100%)',
                        'Repo Breadth': 'Number of repositories touched. Shows cross-project involvement and versatility. (10+ repos = 100%)',
                        'Code Churn': 'Deletion to addition ratio. High ratio indicates refactoring and code cleanup work. (100% deletions = 100%)'
                      }
                      const explanation = metricExplanations[item.data.metric] || ''
                      return `
                        <div style="padding: 12px; max-width: 300px;">
                          <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px;">${item.data.metric}</div>
                          <div style="font-size: 20px; color: #1890ff; margin-bottom: 8px;">${item.data.value.toFixed(1)}/100</div>
                          <div style="color: #666; font-size: 12px; line-height: 1.5;">${explanation}</div>
                        </div>
                      `
                    }
                  }}
                />
              </Col>
              <Col xs={24} lg={12}>
                <Title level={5}>Profile Interpretation</Title>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <Tag color="blue">Commit Frequency</Tag>
                    <Text>Average commits per {granularity} period</Text>
                  </div>
                  <div>
                    <Tag color="green">Code Volume</Tag>
                    <Text>Total lines changed per period</Text>
                  </div>
                  <div>
                    <Tag color="cyan">File Scope</Tag>
                    <Text>Average files modified per period</Text>
                  </div>
                  <div>
                    <Tag color="purple">PR Activity</Tag>
                    <Text>Pull requests opened per period</Text>
                  </div>
                  <div>
                    <Tag color="orange">Repo Breadth</Tag>
                    <Text>Number of repositories contributed to</Text>
                  </div>
                  <div>
                    <Tag color="red">Code Churn</Tag>
                    <Text>Ratio of deletions to additions (refactoring indicator)</Text>
                  </div>
                </Space>
                <Alert
                  message="Developer DNA Signature"
                  description="This radar chart shows your unique productivity profile. A balanced hexagon indicates well-rounded contributions, while spikes show areas of specialization."
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              </Col>
            </Row>
          </Card>

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
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              ${data.map(item => `
                                <div style="margin: 4px 0;">
                                  <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                  <strong>${item.name}:</strong> ${item.value} commits
                                </div>
                              `).join('')}
                              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0; color: #666; font-size: 12px;">
                                Track your commit frequency over time. Consistent patterns indicate steady productivity.
                              </div>
                            </div>
                          `
                        }
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
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const total = data.reduce((sum, item) => sum + item.value, 0)
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              ${data.map(item => `
                                <div style="margin: 4px 0;">
                                  <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                  <strong>${item.name}:</strong> ${item.value.toLocaleString()} lines
                                </div>
                              `).join('')}
                              <div style="margin-top: 4px; padding-top: 4px; border-top: 1px solid #f0f0f0;">
                                <strong>Total:</strong> ${total.toLocaleString()} lines changed
                              </div>
                              <div style="margin-top: 8px; color: #666; font-size: 12px;">
                                Green shows additions, red shows deletions. High deletion ratios indicate refactoring and code cleanup.
                              </div>
                            </div>
                          `
                        }
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
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const item = data[0]
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              <div style="margin: 4px 0;">
                                <strong>Files Changed:</strong> ${item.value}
                              </div>
                              <div style="margin-top: 8px; color: #666; font-size: 12px;">
                                Shows the breadth of your work. Higher numbers indicate wide-ranging changes across the codebase.
                              </div>
                            </div>
                          `
                        }
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
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const item = data[0]
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              <div style="margin: 4px 0;">
                                <strong>Repositories:</strong> ${item.value}
                              </div>
                              <div style="margin-top: 8px; color: #666; font-size: 12px;">
                                Measures cross-project collaboration. Working across multiple repositories shows versatility and team support.
                              </div>
                            </div>
                          `
                        }
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
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const item = data[0]
                          const mergeRate = productivityData.summary?.merge_rate || 0
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              <div style="margin: 4px 0;">
                                <strong>PRs Opened:</strong> ${item.value}
                              </div>
                              <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #f0f0f0;">
                                <div><strong>Overall Merge Rate:</strong> ${(mergeRate * 100).toFixed(1)}%</div>
                              </div>
                              <div style="margin-top: 8px; color: #666; font-size: 12px;">
                                Active PR participation demonstrates code review engagement and collaboration quality.
                              </div>
                            </div>
                          `
                        }
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
                key: '6',
                label: '📂 File Types & Languages',
                children: (
                  <div>
                    {/* Code vs Config vs Docs Distribution */}
                    <Card title="📊 Code vs Configuration vs Documentation" style={{ marginBottom: 24 }}>
                      {fileTypeDistribution && fileTypeDistribution.length > 0 ? (
                        <Column
                          data={fileTypeDistribution}
                          xField="category"
                          yField="percentage"
                          label={{
                            position: 'top',
                            formatter: (datum) => `${datum.percentage}%`,
                          }}
                          color={({ category }) => getCategoryColor(category)}
                          columnStyle={{
                            radius: [8, 8, 0, 0],
                          }}
                          tooltip={{
                            customContent: (title, items) => {
                              if (!items || items.length === 0) return null
                              const data = items[0]?.data
                              return (
                                <div style={{ padding: '12px' }}>
                                  <div style={{ fontWeight: 'bold', marginBottom: 8 }}>{data?.category}</div>
                                  <div>Commits: {data?.commits}</div>
                                  <div>Percentage: {data?.percentage}%</div>
                                  <div>Chars Added: {data?.chars_added?.toLocaleString()}</div>
                                  <div>Chars Deleted: {data?.chars_deleted?.toLocaleString()}</div>
                                </div>
                              )
                            }
                          }}
                        />
                      ) : (
                        <Alert message="No file type distribution data available" type="info" />
                      )}
                    </Card>

                    <Row gutter={[16, 16]}>
                      {/* Top File Types Pie Chart */}
                      <Col xs={24} lg={12}>
                        <Card title="📁 Top File Types Modified">
                          {fileTypeStats && fileTypeStats.length > 0 ? (
                            <Pie
                              data={fileTypeStats.map(ft => ({
                                type: ft.file_type,
                                value: ft.commits,
                              }))}
                              angleField="value"
                              colorField="type"
                              radius={0.8}
                              innerRadius={0.6}
                              label={{
                                type: 'outer',
                                content: '{name}\n{percentage}',
                              }}
                              statistic={{
                                title: {
                                  content: 'Total',
                                },
                                content: {
                                  content: `${fileTypeStats.reduce((sum, ft) => sum + ft.commits, 0)} commits`,
                                },
                              }}
                              interactions={[
                                { type: 'element-selected' },
                                { type: 'element-active' },
                              ]}
                            />
                          ) : (
                            <Alert message="No file type data available" type="info" />
                          )}
                        </Card>
                      </Col>

                      {/* Character Churn by File Type */}
                      <Col xs={24} lg={12}>
                        <Card title="📝 Character Changes by File Type">
                          {fileTypeStats && fileTypeStats.length > 0 ? (
                            <Column
                              data={fileTypeStats.slice(0, 5).flatMap(ft => [
                                { file_type: ft.file_type, type: 'Added', value: ft.chars_added },
                                { file_type: ft.file_type, type: 'Deleted', value: ft.chars_deleted },
                              ])}
                              isGroup
                              xField="file_type"
                              yField="value"
                              seriesField="type"
                              color={['#52c41a', '#ff4d4f']}
                              columnStyle={{
                                radius: [4, 4, 0, 0],
                              }}
                              legend={{
                                position: 'top-right',
                              }}
                              tooltip={{
                                customContent: (title, items) => {
                                  if (!items || items.length === 0) return null
                                  return (
                                    <div style={{ padding: '12px' }}>
                                      <div style={{ fontWeight: 'bold', marginBottom: 8 }}>{title}</div>
                                      {items.map(item => (
                                        <div key={item.name} style={{ margin: '4px 0' }}>
                                          <span style={{
                                            display: 'inline-block',
                                            width: 10,
                                            height: 10,
                                            background: item.color,
                                            borderRadius: '50%',
                                            marginRight: 8
                                          }}></span>
                                          <strong>{item.name}:</strong> {item.value?.toLocaleString()} chars
                                        </div>
                                      ))}
                                    </div>
                                  )
                                }
                              }}
                            />
                          ) : (
                            <Alert message="No character churn data available" type="info" />
                          )}
                        </Card>
                      </Col>

                      {/* File Type Breakdown Table */}
                      <Col span={24}>
                        <Card title="🔍 Detailed File Type Breakdown">
                          {fileTypeStats && fileTypeStats.length > 0 ? (
                            <div style={{ overflowX: 'auto' }}>
                              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                  <tr style={{ borderBottom: '2px solid #f0f0f0' }}>
                                    <th style={{ padding: '12px 8px', textAlign: 'left' }}>File Type</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Commits</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Chars Added</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Chars Deleted</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Total Churn</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Lines Added</th>
                                    <th style={{ padding: '12px 8px', textAlign: 'right' }}>Lines Deleted</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {fileTypeStats.map((ft, idx) => (
                                    <tr key={idx} style={{ borderBottom: '1px solid #f0f0f0' }}>
                                      <td style={{ padding: '12px 8px' }}>
                                        <Tag color="blue">{ft.file_type}</Tag>
                                      </td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right' }}>{ft.commits}</td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right', color: '#52c41a' }}>
                                        {ft.chars_added.toLocaleString()}
                                      </td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right', color: '#ff4d4f' }}>
                                        {ft.chars_deleted.toLocaleString()}
                                      </td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 'bold' }}>
                                        {ft.total_churn.toLocaleString()}
                                      </td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                                        {ft.lines_added.toLocaleString()}
                                      </td>
                                      <td style={{ padding: '12px 8px', textAlign: 'right' }}>
                                        {ft.lines_deleted.toLocaleString()}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          ) : (
                            <Alert message="No file type statistics available" type="info" />
                          )}
                        </Card>
                      </Col>

                      {/* Character Metrics Summary */}
                      <Col span={24}>
                        <Card title="📈 Character-Level Metrics Summary">
                          {characterMetrics ? (
                            <Row gutter={[16, 16]}>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Total Characters Added"
                                  value={characterMetrics.total_chars_added}
                                  valueStyle={{ color: '#52c41a' }}
                                  prefix={<CodeOutlined />}
                                />
                              </Col>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Total Characters Deleted"
                                  value={characterMetrics.total_chars_deleted}
                                  valueStyle={{ color: '#ff4d4f' }}
                                  prefix={<CodeOutlined />}
                                />
                              </Col>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Total Code Churn"
                                  value={characterMetrics.total_churn}
                                  prefix={<BarChartOutlined />}
                                />
                              </Col>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Avg Chars per Commit"
                                  value={characterMetrics.avg_chars_per_commit}
                                  precision={0}
                                  prefix={<FileTextOutlined />}
                                />
                              </Col>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Commits with Data"
                                  value={characterMetrics.commits_with_data}
                                  suffix={`/ ${characterMetrics.total_commits}`}
                                />
                              </Col>
                              <Col xs={12} sm={8} md={6}>
                                <Statistic
                                  title="Coverage"
                                  value={((characterMetrics.commits_with_data / characterMetrics.total_commits) * 100).toFixed(1)}
                                  suffix="%"
                                  valueStyle={{
                                    color: (characterMetrics.commits_with_data / characterMetrics.total_commits) > 0.5 ? '#52c41a' : '#faad14'
                                  }}
                                />
                              </Col>
                            </Row>
                          ) : (
                            <Alert message="No character metrics available" type="info" />
                          )}
                        </Card>
                      </Col>
                    </Row>
                  </div>
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
