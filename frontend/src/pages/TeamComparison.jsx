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
} from 'antd'
import {
  ReloadOutlined,
  TeamOutlined,
  TrophyOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons'
import { Scatter, Radar, Column } from '@ant-design/charts'
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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Data
  const [teamData, setTeamData] = useState([])

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
    setTeamData([])
  }

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
          <Col xs={24} md={12}>
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
              options={staffList.map(s => ({
                value: s.bank_id_1,
                label: `${s.staff_name} (${s.email_address})`,
              }))}
              maxTagCount="responsive"
            />
          </Col>

          <Col xs={24} md={6}>
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

          <Col xs={24} md={6}>
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
            <Col xs={12} md={6}>
              <Card>
                <Statistic
                  title="Team Members"
                  value={teamData.length}
                  prefix={<TeamOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={12} md={6}>
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
            <Col xs={12} md={6}>
              <Card>
                <Statistic
                  title="Total Commits"
                  value={teamData.reduce((sum, s) => sum + s.totalCommits, 0)}
                  valueStyle={{ color: '#52c41a' }}
                />
              </Card>
            </Col>
            <Col xs={12} md={6}>
              <Card>
                <Statistic
                  title="Total PRs"
                  value={teamData.reduce((sum, s) => sum + s.totalPRs, 0)}
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
          </Row>

          {/* Productivity Quadrant Scatter */}
          <Card title="📊 Productivity Quadrant - Quality vs Quantity" style={{ marginBottom: 24 }}>
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
                fields: ['name', 'quantity', 'quality', 'repos', 'rank'],
                formatter: (datum) => {
                  return {
                    name: datum.name,
                    value: `Quantity: ${datum.quantity.toFixed(0)}, Quality: ${datum.quality.toFixed(1)}, Repos: ${datum.repos}, Rank: ${datum.rank}`,
                  }
                },
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
              />
            </Card>
          )}

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
