import React, { useState, useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  DatePicker,
  Button,
  Typography,
  Space,
  Spin,
  Alert,
  message,
  Segmented,
  Table,
  Tag,
  Tooltip,
  Statistic,
  Tabs,
  Collapse,
} from 'antd'
import {
  ReloadOutlined,
  TeamOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
  DownOutlined,
  FilterOutlined,
} from '@ant-design/icons'
import { Scatter, Radar, Column, Line } from '@ant-design/charts'
import { authorsAPI, staffAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { RangePicker } = DatePicker

const TeamComparison = () => {
  // Filters
  const [staffList, setStaffList] = useState([])
  const [selectedStaff, setSelectedStaff] = useState([])
  const [granularity, setGranularity] = useState('quarterly')
  const [dateRange, setDateRange] = useState([
    dayjs().startOf('year'),
    dayjs()
  ])
  const [filterLocation, setFilterLocation] = useState(null)
  const [filterRank, setFilterRank] = useState(null)
  const [filterStaffType, setFilterStaffType] = useState(null)
  const [filterManager, setFilterManager] = useState(null)
  const [filterSubPlatform, setFilterSubPlatform] = useState(null)
  const [filterStaffGrouping, setFilterStaffGrouping] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Data
  const [teamData, setTeamData] = useState([])
  const [timeSeriesData, setTimeSeriesData] = useState([])

  // Filter options (derived from staffList)
  const locationOptions = [...new Set(staffList.map(s => s.work_location).filter(Boolean))].map(loc => ({ label: loc, value: loc }))
  const rankOptions = [...new Set(staffList.map(s => s.rank).filter(Boolean))].map(rank => ({ label: rank, value: rank }))
  const staffTypeOptions = [...new Set(staffList.map(s => s.staff_type).filter(Boolean))].map(type => ({ label: type, value: type }))
  const managerOptions = [...new Set(staffList.map(s => s.reporting_manager_name).filter(Boolean))].map(mgr => ({ label: mgr, value: mgr }))
  const subPlatformOptions = [...new Set(staffList.map(s => s.sub_platform).filter(Boolean))].map(sp => ({ label: sp, value: sp }))
  const staffGroupingOptions = [...new Set(staffList.map(s => s.staff_grouping).filter(Boolean))].map(sg => ({ label: sg, value: sg }))

  // Fetch staff list on mount
  useEffect(() => {
    fetchStaffList()
  }, [])

  // Auto-select staff when filters change
  useEffect(() => {
    if (filterLocation || filterRank || filterStaffType || filterManager || filterSubPlatform || filterStaffGrouping) {
      // Get all staff that match the current filters
      const matchingStaff = staffList.filter(staff => {
        if (filterLocation && staff.work_location !== filterLocation) return false
        if (filterRank && staff.rank !== filterRank) return false
        if (filterStaffType && staff.staff_type !== filterStaffType) return false
        if (filterManager && staff.reporting_manager_name !== filterManager) return false
        if (filterSubPlatform && staff.sub_platform !== filterSubPlatform) return false
        if (filterStaffGrouping && staff.staff_grouping !== filterStaffGrouping) return false
        return true
      })
      // Auto-select all matching staff
      setSelectedStaff(matchingStaff.map(s => s.bank_id_1))
    }
  }, [filterLocation, filterRank, filterStaffType, filterManager, filterSubPlatform, filterStaffGrouping, staffList])

  const fetchStaffList = async () => {
    try {
      const response = await staffAPI.getStaffList({ limit: 1000 })
      setStaffList(response)
    } catch (err) {
      message.error(`Failed to fetch staff list: ${err.message}`)
    }
  }

  const fetchTeamData = async () => {
    if (selectedStaff.length === 0) {
      message.warning('Please select at least one staff member')
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

      // Fetch productivity data for all selected staff
      const promises = selectedStaff.map(bankId =>
        authorsAPI.getProductivity(bankId, params).catch(err => ({
          error: true,
          bankId,
          message: err.message
        }))
      )

      const results = await Promise.allSettled(promises)

      // Separate successful and failed results
      const successfulResults = []
      const failedStaff = []

      results.forEach((result, index) => {
        if (result.status === 'fulfilled' && !result.value.error) {
          successfulResults.push(result.value)
        } else {
          const staffInfo = staffList.find(s => s.bank_id_1 === selectedStaff[index])
          failedStaff.push({
            bankId: selectedStaff[index],
            name: staffInfo?.staff_name || 'Unknown',
            reason: result.value?.message || result.reason?.message || 'Unknown error'
          })
        }
      })

      // Show warning if some staff data failed to load
      if (failedStaff.length > 0) {
        message.warning({
          content: (
            <div>
              <div>Could not load data for {failedStaff.length} staff member(s):</div>
              <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                {failedStaff.map(s => (
                  <li key={s.bankId}>{s.name} - {s.reason}</li>
                ))}
              </ul>
            </div>
          ),
          duration: 8,
        })
      }

      // Proceed with successful results only
      if (successfulResults.length === 0) {
        message.error('No data available for any selected staff member')
        setTeamData([])
        setTimeSeriesData([])
        setLoading(false)
        return
      }

      // Store raw timeseries data for comparison charts
      const tsData = successfulResults.map(result => ({
        name: result.staff.name,
        commits: result.timeseries.commits,
        prs: result.timeseries.prs
      }))
      setTimeSeriesData(tsData)

      // Transform data for visualizations
      const transformedData = successfulResults.map(result => {
        const totalCommits = result.timeseries.commits.reduce((sum, r) => sum + r.commits, 0)
        const totalLinesAdded = result.timeseries.commits.reduce((sum, r) => sum + r.lines_added, 0)
        const totalLinesDeleted = result.timeseries.commits.reduce((sum, r) => sum + r.lines_deleted, 0)
        const totalPRs = result.timeseries.prs.reduce((sum, r) => sum + r.prs_opened, 0)
        const totalFilesChanged = result.timeseries.commits.reduce((sum, r) => sum + r.files_changed, 0)
        const uniqueRepos = result.repository_breakdown.length
        const periods = result.timeseries.commits.length || 1

        return {
          bankId: result.staff.bank_id,
          name: result.staff.name,
          rank: result.staff.rank,
          location: result.staff.location,
          totalCommits,
          totalLinesAdded,
          totalLinesDeleted,
          totalPRs,
          totalFilesChanged,
          uniqueRepos,
          avgCommitsPerPeriod: totalCommits / periods,
          avgLinesPerPeriod: (totalLinesAdded + totalLinesDeleted) / periods,
          avgFilesPerPeriod: totalFilesChanged / periods,
          avgPRsPerPeriod: totalPRs / periods,
          codeChurnRatio: totalLinesDeleted / (totalLinesAdded || 1),

          // Quality metrics
          mergeRate: totalPRs > 0 ? (totalPRs / periods) : 0,
          commitFrequencyScore: Math.min(100, (totalCommits / periods / 10) * 100),
          codeVolumeScore: Math.min(100, ((totalLinesAdded + totalLinesDeleted) / periods / 500) * 100),
          collaborationScore: Math.min(100, (uniqueRepos / 10) * 100),

          // For quadrant calculation
          quantity: totalCommits + (totalPRs * 2), // PRs weighted 2x
          quality: (totalPRs > 0 ? (totalPRs / periods) : 0) * 10 + (uniqueRepos * 5), // Quality = merge rate + collaboration
        }
      })

      setTeamData(transformedData)
    } catch (err) {
      setError(err.message)
      message.error(`Failed to fetch team data: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleClearFilters = () => {
    setSelectedStaff([])
    setDateRange([null, null])
    setGranularity('quarterly')
    setFilterLocation(null)
    setFilterRank(null)
    setFilterStaffType(null)
    setFilterManager(null)
    setFilterSubPlatform(null)
    setFilterStaffGrouping(null)
    setTeamData([])
  }

  // Get filtered staff list
  const filteredStaffList = staffList.filter(staff => {
    if (filterLocation && staff.work_location !== filterLocation) return false
    if (filterRank && staff.rank !== filterRank) return false
    if (filterStaffType && staff.staff_type !== filterStaffType) return false
    if (filterManager && staff.reporting_manager_name !== filterManager) return false
    if (filterSubPlatform && staff.sub_platform !== filterSubPlatform) return false
    if (filterStaffGrouping && staff.staff_grouping !== filterStaffGrouping) return false
    return true
  })

  // Prepare Productivity Quadrant Scatter data - only if teamData is available
  const quadrantData = teamData.length > 0 ? teamData.map(staff => ({
    name: staff.name,
    quantity: typeof staff.quantity === 'number' ? staff.quantity : 0,
    quality: typeof staff.quality === 'number' ? staff.quality : 0,
    repos: staff.uniqueRepos || 1,
    rank: staff.rank || 'N/A',
  })).filter(item =>
    typeof item.quantity === 'number' &&
    typeof item.quality === 'number' &&
    !isNaN(item.quantity) &&
    !isNaN(item.quality) &&
    isFinite(item.quantity) &&
    isFinite(item.quality)
  ) : []

  // Calculate quadrant stats
  const avgQuantity = teamData.length > 0 ? teamData.reduce((sum, s) => sum + (s.quantity || 0), 0) / teamData.length : 0
  const avgQuality = teamData.length > 0 ? teamData.reduce((sum, s) => sum + (s.quality || 0), 0) / teamData.length : 0

  // Categorize staff by quadrant
  const stars = teamData.filter(s => s.quantity >= avgQuantity && s.quality >= avgQuality)
  const specialists = teamData.filter(s => s.quantity < avgQuantity && s.quality >= avgQuality)
  const grinders = teamData.filter(s => s.quantity >= avgQuantity && s.quality < avgQuality)
  const emerging = teamData.filter(s => s.quantity < avgQuantity && s.quality < avgQuality)

  // Prepare Comparative Radar data - compare top 5
  const top5 = [...teamData].sort((a, b) => b.quantity - a.quantity).slice(0, 5)
  const radarData = top5.flatMap(staff => [
    { name: staff.name, metric: 'Commits', value: staff.commitFrequencyScore },
    { name: staff.name, metric: 'Code Volume', value: staff.codeVolumeScore },
    { name: staff.name, metric: 'PR Activity', value: Math.min(100, staff.avgPRsPerPeriod * 20) },
    { name: staff.name, metric: 'Repo Breadth', value: staff.collaborationScore },
    { name: staff.name, metric: 'File Scope', value: Math.min(100, staff.avgFilesPerPeriod * 5) },
    { name: staff.name, metric: 'Code Churn', value: Math.min(100, staff.codeChurnRatio * 100) },
  ])

  // Prepare time-series comparison data
  const commitsComparisonData = timeSeriesData.flatMap(staff =>
    staff.commits.map(c => ({
      period: c.period,
      name: staff.name,
      commits: c.commits
    }))
  )

  const linesChangedComparisonData = timeSeriesData.flatMap(staff =>
    staff.commits.flatMap(c => [
      { period: c.period, name: staff.name, type: 'Added', value: c.lines_added },
      { period: c.period, name: staff.name, type: 'Deleted', value: c.lines_deleted }
    ])
  )

  const filesChangedComparisonData = timeSeriesData.flatMap(staff =>
    staff.commits.map(c => ({
      period: c.period,
      name: staff.name,
      files: c.files_changed
    }))
  )

  // Prepare combined metrics data - restructured for proper grouping
  const combinedMetricsData = timeSeriesData.flatMap(staff =>
    staff.commits.flatMap(c => [
      { period: c.period, staffName: staff.name, metric: 'Commits', value: c.commits, groupKey: `${c.period}-Commits` },
      { period: c.period, staffName: staff.name, metric: 'Lines Changed', value: c.lines_added + c.lines_deleted, groupKey: `${c.period}-Lines Changed` },
      { period: c.period, staffName: staff.name, metric: 'Files Changed', value: c.files_changed, groupKey: `${c.period}-Files Changed` }
    ])
  )

  const reposTouchedComparisonData = timeSeriesData.flatMap(staff =>
    staff.commits.map(c => ({
      period: c.period,
      name: staff.name,
      repos: c.repos_touched
    }))
  )

  const prActivityComparisonData = timeSeriesData.flatMap(staff =>
    staff.prs.map(p => ({
      period: p.period,
      name: staff.name,
      prs: p.prs_opened
    }))
  )

  // Table columns
  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      fixed: 'left',
      width: 200,
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong>{text}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{record.rank || 'N/A'}</Text>
        </Space>
      ),
    },
    {
      title: 'Commits',
      dataIndex: 'totalCommits',
      key: 'totalCommits',
      sorter: (a, b) => a.totalCommits - b.totalCommits,
      render: (val) => <Text>{val.toLocaleString()}</Text>,
    },
    {
      title: 'Lines Changed',
      key: 'lines',
      sorter: (a, b) => (a.totalLinesAdded + a.totalLinesDeleted) - (b.totalLinesAdded + b.totalLinesDeleted),
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <Text style={{ color: '#52c41a' }}>+{record.totalLinesAdded.toLocaleString()}</Text>
          <Text style={{ color: '#ff4d4f' }}>-{record.totalLinesDeleted.toLocaleString()}</Text>
        </Space>
      ),
    },
    {
      title: 'PRs',
      dataIndex: 'totalPRs',
      key: 'totalPRs',
      sorter: (a, b) => a.totalPRs - b.totalPRs,
    },
    {
      title: 'Repos',
      dataIndex: 'uniqueRepos',
      key: 'uniqueRepos',
      sorter: (a, b) => a.uniqueRepos - b.uniqueRepos,
    },
    {
      title: 'Avg/Period',
      key: 'avg',
      render: (_, record) => (
        <Tooltip title={`${record.avgCommitsPerPeriod.toFixed(1)} commits per ${granularity}`}>
          <Tag color="blue">{record.avgCommitsPerPeriod.toFixed(1)}</Tag>
        </Tooltip>
      ),
    },
    {
      title: 'Archetype',
      key: 'archetype',
      render: (_, record) => {
        if (stars.includes(record)) return <Tag color="gold">⭐ Star</Tag>
        if (specialists.includes(record)) return <Tag color="purple">🔍 Specialist</Tag>
        if (grinders.includes(record)) return <Tag color="blue">⚡ Grinder</Tag>
        if (emerging.includes(record)) return <Tag color="green">🌱 Emerging</Tag>
        return <Tag>-</Tag>
      },
    },
  ]

  const hasActiveFilters = filterLocation || filterRank || filterStaffType || filterManager ||
    filterSubPlatform || filterStaffGrouping || selectedStaff.length > 0 || dateRange[0] || dateRange[1] || granularity !== 'quarterly'

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TeamOutlined style={{ color: '#52c41a' }} /> Team Productivity Comparison
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Multi-dimensional productivity analytics across team members
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

          <Col xs={24} md={8}>
            <Text strong>Staff Grouping:</Text>
            <Select
              allowClear
              showSearch
              placeholder="Filter by staff grouping..."
              style={{ width: '100%', marginTop: 8 }}
              value={filterStaffGrouping}
              onChange={setFilterStaffGrouping}
              options={staffGroupingOptions}
            />
          </Col>

          <Col xs={24}>
            <Text strong>Team Members (Select multiple): <Text type="danger">*</Text></Text>
            <Select
              mode="multiple"
              showSearch
              placeholder="Select team members..."
              style={{ width: '100%', marginTop: 8 }}
              value={selectedStaff}
              onChange={setSelectedStaff}
              filterOption={(input, option) =>
                (option?.label?.toLowerCase() || '').includes(input.toLowerCase())
              }
              options={filteredStaffList.map(s => ({
                value: s.bank_id_1,
                label: `${s.staff_name} (${s.email_address}) - ${s.rank || 'N/A'}`,
              }))}
              maxTagCount="responsive"
            />
          </Col>

          <Col xs={24} md={8}>
            <Text strong>Time Granularity:</Text>
            <Segmented
              options={[
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

          <Col xs={24} md={16}>
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
              <Button onClick={fetchTeamData} icon={<ReloadOutlined />} type="primary" loading={loading}>
                Fetch Data
              </Button>
              <Button onClick={handleClearFilters}>Clear Filters</Button>
            </Space>
          </Col>
        </Row>
        </Collapse.Panel>
      </Collapse>

      {/* Data Explanation Header */}
      {!loading && teamData.length > 0 && (
        <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
          <Row align="middle" gutter={16}>
            <Col flex="auto">
              <Space direction="vertical" size={4}>
                <Text strong style={{ color: '#fff', fontSize: 16 }}>
                  🏆 Team Performance Comparison Dashboard
                </Text>
                <Text style={{ color: '#f0f0f0', fontSize: 13 }}>
                  {selectedStaff.length > 0 && `Comparing ${selectedStaff.length} team member${selectedStaff.length > 1 ? 's' : ''}`}
                  {filterRank && ` with rank: ${filterRank}`}
                  {filterLocation && ` in ${filterLocation}`}
                  {filterStaffType && ` (${filterStaffType})`}
                  {filterManager && ` reporting to ${filterManager}`}
                  {filterSubPlatform && ` working on ${filterSubPlatform}`}
                  {selectedStaff.length === 0 && 'Select staff members or apply filters to compare team productivity metrics and identify top performers'}
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
                <Tag color="green" style={{ fontSize: 12 }}>
                  {teamData.length} Members
                </Tag>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {error && <Alert message="Error" description={error} type="error" showIcon style={{ marginBottom: 24 }} />}

      {teamData.length > 0 && (
        <>
          {/* Team Overview Stats */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Team Members"
                  value={teamData.length}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Stars"
                  value={stars.length}
                  prefix={<TrophyOutlined />}
                  valueStyle={{ color: '#faad14' }}
                  suffix={<Text type="secondary">/ {teamData.length}</Text>}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Total Commits"
                  value={teamData.reduce((sum, s) => sum + s.totalCommits, 0).toLocaleString()}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Lines Added"
                  value={teamData.reduce((sum, s) => sum + s.totalLinesAdded, 0).toLocaleString()}
                  valueStyle={{ color: '#52c41a' }}
                  prefix="+"
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Lines Deleted"
                  value={teamData.reduce((sum, s) => sum + s.totalLinesDeleted, 0).toLocaleString()}
                  valueStyle={{ color: '#ff4d4f' }}
                  prefix="-"
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Total PRs"
                  value={teamData.reduce((sum, s) => sum + s.totalPRs, 0).toLocaleString()}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Repos Touched"
                  value={[...new Set(teamData.flatMap(s => s.uniqueRepos))].length}
                  valueStyle={{ color: '#13c2c2' }}
                />
              </Card>
            </Col>
            <Col xs={12} sm={8} md={6} lg={4}>
              <Card>
                <Statistic
                  title="Avg Commits"
                  value={(teamData.reduce((sum, s) => sum + s.avgCommitsPerPeriod, 0) / (teamData.length || 1)).toFixed(1)}
                  valueStyle={{ color: '#1890ff' }}
                  suffix={`/ ${granularity.replace('ly', '')}`}
                />
              </Card>
            </Col>
          </Row>

          {/* Productivity Quadrant Scatter - Hidden */}
          {false && (
          <Card title="📊 Productivity Quadrant - Quality vs Quantity" style={{ marginBottom: 24 }}>
            {teamData.length > 0 && quadrantData.length > 0 ? (
              <Scatter
                data={quadrantData}
                xField="quantity"
                yField="quality"
                colorField="rank"
                sizeField="repos"
                size={[10, 40]}
                shape="circle"
                pointStyle={{
                  fillOpacity: 0.7,
                  stroke: '#fff',
                  lineWidth: 2,
                }}
                xAxis={{
                  title: {
                    text: 'Productivity Quantity (Total Commits + Pull Requests)',
                    style: { fontSize: 14, fontWeight: 'bold' }
                  },
                  nice: true,
                  label: { style: { fontSize: 12 } },
                  grid: {
                    line: {
                      style: {
                        stroke: '#eee',
                        lineWidth: 1,
                        lineDash: [4, 5],
                      },
                    },
                  },
                }}
                yAxis={{
                  title: {
                    text: 'Work Quality (Merge Success + Team Collaboration)',
                    style: { fontSize: 14, fontWeight: 'bold' }
                  },
                  nice: true,
                  label: { style: { fontSize: 12 } },
                  grid: {
                    line: {
                      style: {
                        stroke: '#eee',
                        lineWidth: 1,
                        lineDash: [4, 5],
                      },
                    },
                  },
                }}
                tooltip={{
                  customContent: (title, data) => {
                    if (!data || data.length === 0) return null
                    const item = data[0].data

                    // Determine quadrant
                    let quadrant = ''
                    let quadrantColor = ''
                    let quadrantDesc = ''
                    if (item.quantity >= avgQuantity && item.quality >= avgQuality) {
                      quadrant = '⭐ Stars'
                      quadrantColor = '#faad14'
                      quadrantDesc = 'High quality + high quantity - top performers'
                    } else if (item.quantity < avgQuantity && item.quality >= avgQuality) {
                      quadrant = '🔍 Specialists'
                      quadrantColor = '#722ed1'
                      quadrantDesc = 'High-quality focused contributors'
                    } else if (item.quantity >= avgQuantity && item.quality < avgQuality) {
                      quadrant = '⚡ Grinders'
                      quadrantColor = '#1890ff'
                      quadrantDesc = 'High output, quality improving'
                    } else {
                      quadrant = '🌱 Emerging'
                      quadrantColor = '#52c41a'
                      quadrantDesc = 'Building both metrics'
                    }

                    return `
                      <div style="padding: 14px; min-width: 280px; background: white; border: 1px solid #ddd; border-radius: 6px; box-shadow: 0 3px 12px rgba(0,0,0,0.15);">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 12px; color: #1890ff;">👤 ${item.name}</div>
                        <div style="background: ${quadrantColor}22; padding: 10px; border-radius: 6px; margin-bottom: 12px; border-left: 3px solid ${quadrantColor};">
                          <div style="color: ${quadrantColor}; font-weight: bold; font-size: 14px;">${quadrant}</div>
                          <div style="color: #666; font-size: 12px; margin-top: 4px;">${quadrantDesc}</div>
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: #f9f9f9; border-radius: 4px;">
                          <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span><strong>Productivity Quantity:</strong></span>
                            <span style="font-weight: bold; color: #1890ff;">${Math.round(item.quantity)}</span>
                          </div>
                          <div style="color: #666; font-size: 11px; margin-top: 2px;">Total commits + (PRs × 2)</div>
                        </div>
                        <div style="margin: 10px 0; padding: 8px; background: #f9f9f9; border-radius: 4px;">
                          <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span><strong>Work Quality:</strong></span>
                            <span style="font-weight: bold; color: #52c41a;">${item.quality.toFixed(1)}</span>
                          </div>
                          <div style="color: #666; font-size: 11px; margin-top: 2px;">Merge success rate + team collaboration score</div>
                        </div>
                        <div style="margin: 10px 0; display: flex; justify-content: space-between;">
                          <span><strong>Repositories Touched:</strong></span>
                          <span style="font-weight: bold;">${item.repos}</span>
                        </div>
                        <div style="margin: 10px 0; display: flex; justify-content: space-between;">
                          <span><strong>Rank/Position:</strong></span>
                          <span style="font-weight: bold;">${item.rank}</span>
                        </div>
                        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #e8e8e8; color: #999; font-size: 11px; text-align: center;">
                          💡 Bubble size shows breadth of repository contributions
                        </div>
                      </div>
                    `
                  }
                }}
                legend={{
                  position: 'top-right',
                }}
                annotations={[
                  {
                    type: 'line',
                    start: [avgQuantity, 'min'],
                    end: [avgQuantity, 'max'],
                    style: {
                      stroke: '#ff4d4f',
                      lineWidth: 2,
                      lineDash: [4, 4],
                    },
                  },
                  {
                    type: 'line',
                    start: ['min', avgQuality],
                    end: ['max', avgQuality],
                    style: {
                      stroke: '#ff4d4f',
                      lineWidth: 2,
                      lineDash: [4, 4],
                    },
                  },
                  {
                    type: 'text',
                    position: ['95%', '95%'],
                    content: '⭐ Stars',
                    style: { fontSize: 14, fill: '#faad14', fontWeight: 'bold' },
                  },
                  {
                    type: 'text',
                    position: ['5%', '95%'],
                    content: '🔍 Specialists',
                    style: { fontSize: 14, fill: '#722ed1', fontWeight: 'bold' },
                  },
                  {
                    type: 'text',
                    position: ['95%', '5%'],
                    content: '⚡ Grinders',
                    style: { fontSize: 14, fill: '#1890ff', fontWeight: 'bold' },
                  },
                  {
                    type: 'text',
                    position: ['5%', '5%'],
                    content: '🌱 Emerging',
                    style: { fontSize: 14, fill: '#52c41a', fontWeight: 'bold' },
                  },
                ]}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Text type="secondary">No data to display. Please select team members and fetch data.</Text>
              </div>
            )}
            <Alert
              message="Quadrant Interpretation"
              description={
                <div>
                  <div>⭐ <strong>Stars</strong> ({stars.length}): High quality + high quantity - top performers</div>
                  <div>🔍 <strong>Specialists</strong> ({specialists.length}): High quality, lower volume - quality-focused contributors</div>
                  <div>⚡ <strong>Grinders</strong> ({grinders.length}): High volume, quality concerns - need quality improvement</div>
                  <div>🌱 <strong>Emerging</strong> ({emerging.length}): Building both metrics - growth opportunities</div>
                </div>
              }
              type="info"
              showIcon
              style={{ marginTop: 16 }}
            />
          </Card>
          )}

          {/* Comparative Radar - Top 5 */}
          {top5.length > 0 && (
            <Card
              title="🧬 Top 5 Developer DNA Comparison"
              style={{ marginBottom: 24 }}
              extra={
                <Text type="secondary" style={{ fontSize: 13 }}>
                  Multi-dimensional skill profile comparing top performers across 6 key metrics
                </Text>
              }
            >
              <Radar
                data={radarData}
                xField="metric"
                yField="value"
                seriesField="name"
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
                  size: 3,
                }}
                area={{}}
                legend={{
                  position: 'bottom',
                }}
                tooltip={{
                  showTitle: true,
                  customContent: (title, data) => {
                    if (!data || data.length === 0) return null
                    const metricExplanations = {
                      'Commits': {
                        icon: '📝',
                        desc: 'Frequency of code commits - measures consistent contributions to the codebase'
                      },
                      'Code Volume': {
                        icon: '📊',
                        desc: 'Total lines of code changed - measures the volume of code output'
                      },
                      'PR Activity': {
                        icon: '🔄',
                        desc: 'Pull requests created - shows collaboration and code review engagement'
                      },
                      'Repo Breadth': {
                        icon: '🗂️',
                        desc: 'Cross-repository contributions - indicates versatility and team support'
                      },
                      'File Scope': {
                        icon: '📁',
                        desc: 'Breadth of files modified - shows wide-ranging codebase knowledge'
                      },
                      'Code Churn': {
                        icon: '♻️',
                        desc: 'Code deletion to addition ratio - high values indicate refactoring work'
                      }
                    }
                    const metric = metricExplanations[title] || { icon: '📈', desc: '' }
                    const avgScore = data.reduce((sum, item) => sum + item.value, 0) / data.length

                    return `
                      <div style="padding: 14px; max-width: 320px; background: white; border: 1px solid #ddd; border-radius: 6px; box-shadow: 0 3px 12px rgba(0,0,0,0.15);">
                        <div style="font-weight: bold; font-size: 15px; margin-bottom: 8px; color: #1890ff;">
                          ${metric.icon} ${title}
                        </div>
                        <div style="color: #666; font-size: 12px; margin-bottom: 12px; padding: 8px; background: #f9f9f9; border-radius: 4px; border-left: 3px solid #1890ff;">
                          ${metric.desc}
                        </div>
                        <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                          <strong>Team Average:</strong> <span style="color: #1890ff; font-weight: bold;">${avgScore.toFixed(1)}/100</span>
                        </div>
                        ${data.map(item => {
                          const percentage = (item.value / 100) * 100
                          const color = item.value >= 70 ? '#52c41a' : item.value >= 40 ? '#faad14' : '#ff4d4f'
                          return `
                            <div style="margin: 8px 0;">
                              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <div>
                                  <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                  <strong>${item.name}</strong>
                                </div>
                                <span style="font-weight: bold; color: ${color};">${item.value.toFixed(1)}/100</span>
                              </div>
                              <div style="background: #f0f0f0; height: 6px; border-radius: 3px; overflow: hidden;">
                                <div style="background: ${color}; height: 100%; width: ${percentage}%; transition: width 0.3s;"></div>
                              </div>
                            </div>
                          `
                        }).join('')}
                      </div>
                    `
                  }
                }}
              />
            </Card>
          )}

          {/* Time-Series Comparison Charts */}
          <Card title="📈 Team Performance Comparison Over Time" style={{ marginBottom: 24 }}>
            <Tabs
              defaultActiveKey="1"
              items={[
                {
                  key: '1',
                  label: 'Combined Metrics View',
                  children: (
                    <>
                    <Column
                      data={combinedMetricsData}
                      isGroup
                      xField="groupKey"
                      yField="value"
                      seriesField="staffName"
                      dodgePadding={4}
                      intervalPadding={20}
                      columnStyle={{
                        radius: [8, 8, 0, 0],
                      }}
                      legend={{
                        position: 'top-right',
                        layout: 'horizontal',
                      }}
                      label={{
                        position: 'top',
                        style: {
                          fill: '#000',
                          opacity: 0.8,
                          fontSize: 11,
                        },
                        formatter: (datum) => {
                          return datum.value.toLocaleString()
                        }
                      }}
                      xAxis={{
                        title: { text: 'Metrics by Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: {
                          autoRotate: true,
                          autoHide: true,
                          style: { fontSize: 11 },
                          formatter: (text) => {
                            // Extract period and metric from groupKey
                            const parts = text.split('-')
                            if (parts.length >= 2) {
                              const period = parts[0]
                              const metric = parts.slice(1).join('-')
                              const metricIcons = {
                                'Commits': '📝',
                                'Lines Changed': '📊',
                                'Files Changed': '📁'
                              }
                              return `${period}\n${metricIcons[metric] || metric}`
                            }
                            return text
                          }
                        }
                      }}
                      yAxis={{
                        title: { text: 'Metric Value', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: {
                          style: { fontSize: 12 },
                          formatter: (v) => v.toLocaleString()
                        }
                      }}
                      tooltip={{
                        shared: true,
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null

                          // Extract period and metric from groupKey
                          const parts = title.split('-')
                          const period = parts[0]
                          const metric = parts.slice(1).join('-')

                          const metricColors = {
                            'Commits': '#1890ff',
                            'Lines Changed': '#52c41a',
                            'Files Changed': '#faad14'
                          }

                          const metricIcons = {
                            'Commits': '📝',
                            'Lines Changed': '📊',
                            'Files Changed': '📁'
                          }

                          const color = metricColors[metric] || '#1890ff'
                          const icon = metricIcons[metric] || '📈'
                          const total = data.reduce((sum, item) => sum + item.value, 0)

                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 350px;">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: ${color};">
                                ${icon} ${metric} - ${period}
                              </div>
                              <div style="font-size: 11px; color: #666; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                                Total: <strong style="color: ${color};">${total.toLocaleString()}</strong>
                              </div>
                              ${data.map(item => `
                                <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
                                  <div>
                                    <span style="display: inline-block; width: 8px; height: 8px; background: ${item.color}; border-radius: 50%; margin-right: 6px;"></span>
                                    <span style="font-size: 12px; font-weight: 500;">${item.data.staffName}</span>
                                  </div>
                                  <span style="font-weight: bold; color: ${item.color}; margin-left: 12px;">${item.value.toLocaleString()}</span>
                                </div>
                              `).join('')}
                            </div>
                          `
                        }
                      }}
                    />
                    <Alert
                      message="Chart Legend"
                      description={
                        <Space size="large">
                          <Text><span style={{ display: 'inline-block', width: 12, height: 12, background: '#1890ff', borderRadius: 2, marginRight: 8 }}></span>📝 <strong>Commits</strong> - Total number of code commits</Text>
                          <Text><span style={{ display: 'inline-block', width: 12, height: 12, background: '#52c41a', borderRadius: 2, marginRight: 8 }}></span>📊 <strong>Lines Changed</strong> - Total lines added + deleted</Text>
                          <Text><span style={{ display: 'inline-block', width: 12, height: 12, background: '#faad14', borderRadius: 2, marginRight: 8 }}></span>📁 <strong>Files Changed</strong> - Number of files modified</Text>
                        </Space>
                      }
                      type="info"
                      showIcon
                      style={{ marginTop: 16 }}
                    />
                    </>
                  ),
                },
                {
                  key: '2',
                  label: 'Commits Over Time',
                  children: (
                    <Line
                      data={commitsComparisonData}
                      xField="period"
                      yField="commits"
                      seriesField="name"
                      smooth
                      point={{ size: 4 }}
                      legend={{ position: 'top-right' }}
                      xAxis={{
                        title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                      }}
                      yAxis={{
                        title: { text: 'Number of Commits', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { style: { fontSize: 12 } }
                      }}
                      tooltip={{
                        shared: true,
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const total = data.reduce((sum, item) => sum + item.value, 0)
                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1890ff;">📅 ${title}</div>
                              <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                                <strong>Total Commits:</strong> ${total}
                              </div>
                              ${data.map(item => `
                                <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
                                  <div>
                                    <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                    <span style="font-weight: 500;">${item.name}</span>
                                  </div>
                                  <span style="margin-left: 16px; font-weight: bold; color: ${item.color};">${item.value} commits</span>
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
                  key: '3',
                  label: 'Lines Changed',
                  children: (
                    <Column
                      data={linesChangedComparisonData}
                      isGroup
                      xField="period"
                      yField="value"
                      seriesField="name"
                      groupField="type"
                      color={['#52c41a', '#ff4d4f']}
                      legend={{ position: 'top-right' }}
                      xAxis={{
                        title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                      }}
                      yAxis={{
                        title: { text: 'Number of Lines', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: {
                          style: { fontSize: 12 },
                          formatter: (v) => v.toLocaleString()
                        }
                      }}
                      tooltip={{
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const grouped = {}
                          data.forEach(item => {
                            const type = item.data.type
                            if (!grouped[type]) grouped[type] = []
                            grouped[type].push(item)
                          })
                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1890ff;">📅 ${title}</div>
                              ${Object.entries(grouped).map(([type, items]) => `
                                <div style="margin-top: 8px;">
                                  <div style="font-weight: bold; margin-bottom: 4px; color: ${type === 'Added' ? '#52c41a' : '#ff4d4f'};">
                                    ${type === 'Added' ? '➕ Lines Added' : '➖ Lines Deleted'}
                                  </div>
                                  ${items.map(item => `
                                    <div style="margin: 4px 0 4px 16px; display: flex; align-items: center; justify-content: space-between;">
                                      <div>
                                        <span style="display: inline-block; width: 8px; height: 8px; background: ${item.color}; border-radius: 50%; margin-right: 6px;"></span>
                                        <span style="font-weight: 500;">${item.name}</span>
                                      </div>
                                      <span style="margin-left: 16px; font-weight: bold; color: ${item.color};">${item.value.toLocaleString()} lines</span>
                                    </div>
                                  `).join('')}
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
                  key: '4',
                  label: 'Files Changed',
                  children: (
                    <Line
                      data={filesChangedComparisonData}
                      xField="period"
                      yField="files"
                      seriesField="name"
                      smooth
                      point={{ size: 4 }}
                      legend={{ position: 'top-right' }}
                      xAxis={{
                        title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                      }}
                      yAxis={{
                        title: { text: 'Number of Files Modified', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { style: { fontSize: 12 } }
                      }}
                      tooltip={{
                        shared: true,
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const total = data.reduce((sum, item) => sum + item.value, 0)
                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1890ff;">📅 ${title}</div>
                              <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                                <strong>Total Files Changed:</strong> ${total}
                              </div>
                              ${data.map(item => `
                                <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
                                  <div>
                                    <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                    <span style="font-weight: 500;">${item.name}</span>
                                  </div>
                                  <span style="margin-left: 16px; font-weight: bold; color: ${item.color};">${item.value} files</span>
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
                  key: '5',
                  label: 'Repos Touched',
                  children: (
                    <Column
                      data={reposTouchedComparisonData}
                      isGroup
                      xField="period"
                      yField="repos"
                      seriesField="name"
                      legend={{ position: 'top-right' }}
                      xAxis={{
                        title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                      }}
                      yAxis={{
                        title: { text: 'Number of Repositories', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { style: { fontSize: 12 } }
                      }}
                      tooltip={{
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const total = data.reduce((sum, item) => sum + item.value, 0)
                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1890ff;">📅 ${title}</div>
                              <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                                <strong>Total Repos Touched:</strong> ${total}
                                <div style="font-size: 11px; color: #666; margin-top: 2px;">Shows breadth of contribution across different repositories</div>
                              </div>
                              ${data.map(item => `
                                <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
                                  <div>
                                    <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                    <span style="font-weight: 500;">${item.name}</span>
                                  </div>
                                  <span style="margin-left: 16px; font-weight: bold; color: ${item.color};">${item.value} repos</span>
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
                  key: '5',
                  label: 'PR Activity',
                  children: (
                    <Line
                      data={prActivityComparisonData}
                      xField="period"
                      yField="prs"
                      seriesField="name"
                      smooth
                      point={{ size: 5, shape: 'diamond' }}
                      legend={{ position: 'top-right' }}
                      xAxis={{
                        title: { text: 'Time Period', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { autoRotate: true, autoHide: true, style: { fontSize: 12 } }
                      }}
                      yAxis={{
                        title: { text: 'Number of Pull Requests', style: { fontSize: 14, fontWeight: 'bold' } },
                        label: { style: { fontSize: 12 } }
                      }}
                      tooltip={{
                        shared: true,
                        showTitle: true,
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          const total = data.reduce((sum, item) => sum + item.value, 0)
                          return `
                            <div style="padding: 12px; background: white; border: 1px solid #ddd; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                              <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #1890ff;">📅 ${title}</div>
                              <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f0f0f0;">
                                <strong>Total PRs Opened:</strong> ${total}
                                <div style="font-size: 11px; color: #666; margin-top: 2px;">Pull Requests indicate code review and collaboration activity</div>
                              </div>
                              ${data.map(item => `
                                <div style="margin: 6px 0; display: flex; align-items: center; justify-content: space-between;">
                                  <div>
                                    <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                    <span style="font-weight: 500;">${item.name}</span>
                                  </div>
                                  <span style="margin-left: 16px; font-weight: bold; color: ${item.color};">${item.value} PRs</span>
                                </div>
                              `).join('')}
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

          {/* Detailed Table */}
          <Card title="📋 Detailed Team Metrics" style={{ marginBottom: 24 }}>
            <Table
              columns={columns}
              dataSource={teamData}
              rowKey="bankId"
              scroll={{ x: 1000 }}
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </>
      )}

      {teamData.length === 0 && !loading && (
        <Alert
          message="No Data"
          description="Please select team members and click 'Fetch Data' to view team comparison analytics."
          type="info"
          showIcon
        />
      )}

      {loading && (
        <div style={{ padding: '50px', textAlign: 'center' }}>
          <Spin size="large" tip="Fetching team productivity data...">
            <div style={{ minHeight: '200px' }} />
          </Spin>
        </div>
      )}
    </div>
  )
}

export default TeamComparison
