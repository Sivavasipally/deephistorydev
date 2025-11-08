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
} from 'antd'
import {
  ReloadOutlined,
  TeamOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
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
  const [granularity, setGranularity] = useState('monthly')
  const [dateRange, setDateRange] = useState([null, null])
  const [filterLocation, setFilterLocation] = useState(null)
  const [filterRank, setFilterRank] = useState(null)
  const [filterStaffType, setFilterStaffType] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Data
  const [teamData, setTeamData] = useState([])
  const [timeSeriesData, setTimeSeriesData] = useState([])

  // Filter options (derived from staffList)
  const locationOptions = [...new Set(staffList.map(s => s.work_location).filter(Boolean))].map(loc => ({ label: loc, value: loc }))
  const rankOptions = [...new Set(staffList.map(s => s.rank).filter(Boolean))].map(rank => ({ label: rank, value: rank }))
  const staffTypeOptions = [...new Set(staffList.map(s => s.staff_type).filter(Boolean))].map(type => ({ label: type, value: type }))

  // Fetch staff list on mount
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
        authorsAPI.getProductivity(bankId, params)
      )

      const results = await Promise.all(promises)

      // Store raw timeseries data for comparison charts
      const tsData = results.map(result => ({
        name: result.staff.name,
        commits: result.timeseries.commits,
        prs: result.timeseries.prs
      }))
      setTimeSeriesData(tsData)

      // Transform data for visualizations
      const transformedData = results.map(result => {
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
    setGranularity('monthly')
    setFilterLocation(null)
    setFilterRank(null)
    setFilterStaffType(null)
    setTeamData([])
  }

  // Get filtered staff list
  const filteredStaffList = staffList.filter(staff => {
    if (filterLocation && staff.work_location !== filterLocation) return false
    if (filterRank && staff.rank !== filterRank) return false
    if (filterStaffType && staff.staff_type !== filterStaffType) return false
    return true
  })

  // Prepare Productivity Quadrant Scatter data
  const quadrantData = teamData.map(staff => ({
    name: staff.name,
    quantity: staff.quantity,
    quality: staff.quality,
    repos: staff.uniqueRepos,
    rank: staff.rank || 'N/A',
  }))

  // Calculate quadrant stats
  const avgQuantity = teamData.reduce((sum, s) => sum + s.quantity, 0) / (teamData.length || 1)
  const avgQuality = teamData.reduce((sum, s) => sum + s.quality, 0) / (teamData.length || 1)

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

      {/* Filters */}
      <Card title="🔍 Filters & Configuration" style={{ marginBottom: 24 }}>
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
      </Card>

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

          {/* Productivity Quadrant Scatter */}
          <Card title="📊 Productivity Quadrant - Quality vs Quantity" style={{ marginBottom: 24 }}>
            {quadrantData.length > 0 ? (
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
                  title: { text: 'Quantity (Commits + PRs)' },
                  nice: true,
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
                  title: { text: 'Quality (Merge Rate + Collaboration)' },
                  nice: true,
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
                      <div style="padding: 12px; min-width: 250px;">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 12px;">${item.name}</div>
                        <div style="background: ${quadrantColor}22; padding: 8px; border-radius: 4px; margin-bottom: 12px;">
                          <div style="color: ${quadrantColor}; font-weight: bold;">${quadrant}</div>
                          <div style="color: #666; font-size: 12px; margin-top: 4px;">${quadrantDesc}</div>
                        </div>
                        <div style="margin: 8px 0;">
                          <strong>Quantity:</strong> ${Math.round(item.quantity)}<br/>
                          <span style="color: #666; font-size: 12px;">Commits + (PRs × 2)</span>
                        </div>
                        <div style="margin: 8px 0;">
                          <strong>Quality:</strong> ${item.quality.toFixed(1)}<br/>
                          <span style="color: #666; font-size: 12px;">Merge Rate + Collaboration</span>
                        </div>
                        <div style="margin: 8px 0;">
                          <strong>Repositories:</strong> ${item.repos}
                        </div>
                        <div style="margin: 8px 0;">
                          <strong>Rank:</strong> ${item.rank}
                        </div>
                        <div style="margin-top: 12px; padding-top: 8px; border-top: 1px solid #f0f0f0; color: #666; font-size: 11px;">
                          Bubble size represents repository breadth
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

          {/* Comparative Radar - Top 5 */}
          {top5.length > 0 && (
            <Card title="🧬 Top 5 Developer DNA Comparison" style={{ marginBottom: 24 }}>
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
                  customContent: (title, data) => {
                    if (!data || data.length === 0) return null
                    const metricExplanations = {
                      'Commits': 'Frequency of code commits. Higher scores indicate consistent contributions.',
                      'Code Volume': 'Total lines of code changed. Measures output volume.',
                      'PR Activity': 'Number of pull requests created. Shows collaboration engagement.',
                      'Repo Breadth': 'Cross-repository involvement. Indicates versatility and team support.',
                      'File Scope': 'Breadth of files modified. Shows wide-ranging codebase knowledge.',
                      'Code Churn': 'Deletion to addition ratio. High values indicate refactoring work.'
                    }
                    const explanation = metricExplanations[title] || ''
                    return `
                      <div style="padding: 12px; max-width: 300px;">
                        <div style="font-weight: bold; font-size: 14px; margin-bottom: 8px;">${title}</div>
                        <div style="color: #666; font-size: 12px; margin-bottom: 12px;">${explanation}</div>
                        ${data.map(item => `
                          <div style="margin: 6px 0;">
                            <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                            <strong>${item.name}:</strong> ${item.value.toFixed(1)}/100
                          </div>
                        `).join('')}
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
                        label: { autoRotate: true, autoHide: true }
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
                            </div>
                          `
                        }
                      }}
                    />
                  ),
                },
                {
                  key: '2',
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
                        label: { autoRotate: true, autoHide: true }
                      }}
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              ${data.map(item => `
                                <div style="margin: 4px 0;">
                                  <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                  <strong>${item.name} (${item.data.type}):</strong> ${item.value.toLocaleString()} lines
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
                        label: { autoRotate: true, autoHide: true }
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
                                  <strong>${item.name}:</strong> ${item.value} files
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
                        label: { autoRotate: true, autoHide: true }
                      }}
                      tooltip={{
                        customContent: (title, data) => {
                          if (!data || data.length === 0) return null
                          return `
                            <div style="padding: 12px;">
                              <div style="font-weight: bold; margin-bottom: 8px;">${title}</div>
                              ${data.map(item => `
                                <div style="margin: 4px 0;">
                                  <span style="display: inline-block; width: 10px; height: 10px; background: ${item.color}; border-radius: 50%; margin-right: 8px;"></span>
                                  <strong>${item.name}:</strong> ${item.value} repositories
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
                        label: { autoRotate: true, autoHide: true }
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
                                  <strong>${item.name}:</strong> ${item.value} PRs
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
