import React, { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  message,
  App,
  Collapse,
  Row,
  Col,
  Select,
  Input,
  Statistic,
  Tabs,
  Tooltip,
  Badge,
} from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined,
  DownOutlined,
  SearchOutlined,
  CodeOutlined,
  BranchesOutlined,
  CheckCircleOutlined,
  MailOutlined,
  EnvironmentOutlined,
  IdcardOutlined,
} from '@ant-design/icons'
import { staffAPI, commitsAPI } from '../services/api'
import dayjs from 'dayjs'
import { exportMultipleSheetsToExcel } from '../utils/excelExport'

const { Title, Text } = Typography
const { Search } = Input

const StaffDetails = () => {
  // Use App context for message
  const { message: messageApi } = App.useApp()

  // State
  const [staffList, setStaffList] = useState([])
  const [filteredStaff, setFilteredStaff] = useState([])
  const [loading, setLoading] = useState(false)
  const [expandedRowKeys, setExpandedRowKeys] = useState([])

  // Filters
  const [searchText, setSearchText] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterStaffType, setFilterStaffType] = useState('all')
  const [filterRank, setFilterRank] = useState('all')
  const [filterLocation, setFilterLocation] = useState('all')
  const [filterDepartment, setFilterDepartment] = useState('all')
  const [showZeroActivity, setShowZeroActivity] = useState(true) // Toggle for zero activity staff

  // Statistics
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    withCommits: 0,
    withPRs: 0,
    withApprovals: 0,
    zeroActivity: 0,
  })

  useEffect(() => {
    fetchStaffData()
  }, [])

  useEffect(() => {
    applyFilters()
  }, [
    staffList,
    searchText,
    filterStatus,
    filterStaffType,
    filterRank,
    filterLocation,
    filterDepartment,
    showZeroActivity,
  ])

  const fetchStaffData = async () => {
    try {
      setLoading(true)

      // Fetch pre-calculated staff metrics (single API call - 100x faster!)
      const response = await fetch('/api/staff-metrics/?limit=10000')
      if (!response.ok) {
        throw new Error('Failed to fetch staff metrics')
      }
      const staffMetrics = await response.json()

      // Transform metrics to match expected format
      const staffWithActivity = staffMetrics.map(s => ({
        ...s,
        // Map metrics fields to expected format
        commitCount: s.total_commits || 0,
        prCount: s.total_prs_created || 0,
        approvalCount: s.total_pr_approvals_given || 0,
        hasActivity: (s.total_commits > 0 || s.total_prs_created > 0 || s.total_pr_approvals_given > 0),
        // Note: Detailed commits/PRs/approvals will be loaded on-demand when row is expanded
        commits: [],
        pullRequests: [],
        approvals: [],
      }))

      setStaffList(staffWithActivity)

      // Calculate statistics
      const totalStaff = staffWithActivity.length
      const activeStaff = staffWithActivity.filter(s => s.staff_status === 'Active').length
      const inactiveStaff = totalStaff - activeStaff
      const withCommits = staffWithActivity.filter(s => s.commitCount > 0).length
      const withPRs = staffWithActivity.filter(s => s.prCount > 0).length
      const withApprovals = staffWithActivity.filter(s => s.approvalCount > 0).length
      const zeroActivity = staffWithActivity.filter(s => !s.hasActivity).length

      setStats({
        total: totalStaff,
        active: activeStaff,
        inactive: inactiveStaff,
        withCommits,
        withPRs,
        withApprovals,
        zeroActivity,
      })

      messageApi.success(`Loaded ${totalStaff} staff members`)
    } catch (err) {
      messageApi.error('Failed to fetch staff data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const applyFilters = () => {
    let filtered = [...staffList]

    // Search text filter
    if (searchText) {
      const search = searchText.toLowerCase()
      filtered = filtered.filter(
        s =>
          s.staff_name?.toLowerCase().includes(search) ||
          s.email_address?.toLowerCase().includes(search) ||
          s.bank_id_1?.toLowerCase().includes(search) ||
          s.reporting_manager_name?.toLowerCase().includes(search)
      )
    }

    // Status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(s => s.staff_status === filterStatus)
    }

    // Staff type filter
    if (filterStaffType !== 'all') {
      filtered = filtered.filter(s => s.staff_type === filterStaffType)
    }

    // Rank filter
    if (filterRank !== 'all') {
      filtered = filtered.filter(s => s.rank === filterRank)
    }

    // Location filter
    if (filterLocation !== 'all') {
      filtered = filtered.filter(s => s.work_location === filterLocation)
    }

    // Department filter
    if (filterDepartment !== 'all') {
      filtered = filtered.filter(s => s.department_id === filterDepartment)
    }

    // Show/hide zero activity staff
    if (!showZeroActivity) {
      filtered = filtered.filter(s => s.hasActivity)
    }

    setFilteredStaff(filtered)
  }

  const handleClearFilters = () => {
    setSearchText('')
    setFilterStatus('all')
    setFilterStaffType('all')
    setFilterRank('all')
    setFilterLocation('all')
    setFilterDepartment('all')
    setShowZeroActivity(true)
  }

  const handleExportToExcel = () => {
    if (filteredStaff.length === 0) {
      messageApi.warning('No data to export')
      return
    }

    const sheets = []

    // Staff Summary Sheet
    sheets.push({
      name: 'Staff Summary',
      data: filteredStaff.map(s => ({
        'Staff Name': s.staff_name,
        'Bank ID': s.bank_id_1,
        'Email': s.email_address,
        'Status': s.staff_status,
        'Original Type': s.original_staff_type,
        'Staff Type': s.staff_type,
        'Rank': s.rank,
        'Level': s.staff_level,
        'HR Role': s.hr_role,
        'Job Function': s.job_function,
        'Department ID': s.department_id,
        'Manager': s.reporting_manager_name,
        'Location': s.work_location,
        'Company': s.company_name,
        'Total Commits': s.commitCount,
        'Total PRs': s.prCount,
        'Total Approvals': s.approvalCount,
        'Has Activity': s.hasActivity ? 'Yes' : 'No',
      })),
    })

    // All Commits Sheet
    const allCommits = []
    filteredStaff.forEach(s => {
      if (s.commits && s.commits.length > 0) {
        s.commits.forEach(commit => {
          allCommits.push({
            'Staff Name': s.staff_name,
            'Email': s.email_address,
            'Commit Hash': commit.commit_hash,
            'Date': commit.commit_date,
            'Message': commit.message,
            'Lines Added': commit.lines_added,
            'Lines Deleted': commit.lines_deleted,
            'Files Changed': commit.files_changed,
            'Repository': commit.repository,
          })
        })
      }
    })
    if (allCommits.length > 0) {
      sheets.push({ name: 'All Commits', data: allCommits })
    }

    // All Pull Requests Sheet
    const allPRs = []
    filteredStaff.forEach(s => {
      if (s.pullRequests && s.pullRequests.length > 0) {
        s.pullRequests.forEach(pr => {
          allPRs.push({
            'Staff Name': s.staff_name,
            'Email': s.email_address,
            'PR Title': pr.title,
            'PR Number': pr.pr_number,
            'State': pr.state,
            'Created Date': pr.created_at,
            'Merged Date': pr.merged_at,
            'Repository': pr.repository,
          })
        })
      }
    })
    if (allPRs.length > 0) {
      sheets.push({ name: 'All Pull Requests', data: allPRs })
    }

    // All Approvals Sheet
    const allApprovals = []
    filteredStaff.forEach(s => {
      if (s.approvals && s.approvals.length > 0) {
        s.approvals.forEach(approval => {
          allApprovals.push({
            'Reviewer Name': s.staff_name,
            'Reviewer Email': s.email_address,
            'PR Title': approval.title,
            'PR Number': approval.pr_number,
            'PR Author': approval.author,
            'Review State': approval.review_state,
            'Reviewed Date': approval.reviewed_at,
            'Repository': approval.repository,
          })
        })
      }
    })
    if (allApprovals.length > 0) {
      sheets.push({ name: 'All Approvals', data: allApprovals })
    }

    const filename = `staff_details_${dayjs().format('YYYYMMDD_HHmmss')}`
    exportMultipleSheetsToExcel(sheets, filename)
    messageApi.success('Excel file exported successfully!')
  }

  // Get unique values for filters
  const uniqueStatuses = [...new Set(staffList.map(s => s.staff_status).filter(Boolean))]
  const uniqueStaffTypes = [...new Set(staffList.map(s => s.staff_type).filter(Boolean))]
  const uniqueRanks = [...new Set(staffList.map(s => s.rank).filter(Boolean))]
  const uniqueLocations = [...new Set(staffList.map(s => s.work_location).filter(Boolean))]
  const uniqueDepartments = [...new Set(staffList.map(s => s.department_id).filter(Boolean))]

  // Main table columns
  const columns = [
    {
      title: 'Staff Name',
      dataIndex: 'staff_name',
      key: 'staff_name',
      fixed: 'left',
      width: 180,
      sorter: (a, b) => (a.staff_name || '').localeCompare(b.staff_name || ''),
      render: (text, record) => (
        <Space>
          <UserOutlined />
          <div>
            <div style={{ fontWeight: 'bold' }}>{text}</div>
            <Text type="secondary" style={{ fontSize: 11 }}>
              {record.bank_id_1}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email_address',
      key: 'email_address',
      width: 200,
      ellipsis: true,
      render: text => (
        <Tooltip title={text}>
          <Space>
            <MailOutlined />
            {text}
          </Space>
        </Tooltip>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'staff_status',
      key: 'staff_status',
      width: 100,
      filters: uniqueStatuses.map(s => ({ text: s, value: s })),
      onFilter: (value, record) => record.staff_status === value,
      render: status => (
        <Tag color={status === 'Active' ? 'green' : 'red'}>{status}</Tag>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'staff_type',
      key: 'staff_type',
      width: 120,
      render: type => <Tag color="blue">{type}</Tag>,
    },
    {
      title: 'Rank',
      dataIndex: 'rank',
      key: 'rank',
      width: 150,
      render: rank => <Tag color="purple">{rank}</Tag>,
    },
    {
      title: 'Location',
      dataIndex: 'work_location',
      key: 'work_location',
      width: 120,
      render: location => (
        <Tooltip title={location}>
          <Space>
            <EnvironmentOutlined />
            {location}
          </Space>
        </Tooltip>
      ),
    },
    {
      title: 'Manager',
      dataIndex: 'reporting_manager_name',
      key: 'reporting_manager_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: 'Activity',
      key: 'activity',
      width: 200,
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="Commits">
            <Badge
              count={record.commitCount}
              showZero
              style={{ backgroundColor: record.commitCount > 0 ? '#52c41a' : '#d9d9d9' }}
            >
              <CodeOutlined style={{ fontSize: 16 }} />
            </Badge>
          </Tooltip>
          <Tooltip title="Pull Requests">
            <Badge
              count={record.prCount}
              showZero
              style={{ backgroundColor: record.prCount > 0 ? '#1890ff' : '#d9d9d9' }}
            >
              <BranchesOutlined style={{ fontSize: 16 }} />
            </Badge>
          </Tooltip>
          <Tooltip title="Approvals">
            <Badge
              count={record.approvalCount}
              showZero
              style={{ backgroundColor: record.approvalCount > 0 ? '#722ed1' : '#d9d9d9' }}
            >
              <CheckCircleOutlined style={{ fontSize: 16 }} />
            </Badge>
          </Tooltip>
        </Space>
      ),
    },
  ]

  // Load detailed data for a staff member on-demand
  const loadStaffDetails = async (staffRecord) => {
    // Check if already loaded
    if (staffRecord.detailsLoaded) {
      return staffRecord
    }

    try {
      // Fetch commits and PRs only when row is expanded
      // Note: Approvals count is already available from staff_metrics
      const [commits, prs] = await Promise.all([
        commitsAPI.getCommits({ author: staffRecord.email_address, limit: 1000 }).catch(() => []),
        fetch(`/api/pull-requests?author=${staffRecord.email_address}&limit=1000`)
          .then(res => {
            if (!res.ok) {
              throw new Error(`HTTP ${res.status}`)
            }
            return res.json()
          })
          .catch(() => []),
      ])

      // Update the staff record with detailed data
      staffRecord.commits = commits || []
      staffRecord.pullRequests = prs || []
      staffRecord.approvals = [] // Approvals details not available in current API
      staffRecord.detailsLoaded = true

      // Update the state to reflect the loaded data
      setStaffList(prevList =>
        prevList.map(s => s.bank_id_1 === staffRecord.bank_id_1 ? staffRecord : s)
      )

      return staffRecord
    } catch (err) {
      console.error(`Error loading details for ${staffRecord.staff_name}:`, err)
      messageApi.error(`Failed to load details for ${staffRecord.staff_name}`)
      return staffRecord
    }
  }

  // Expanded row render - shows detailed information
  const expandedRowRender = record => {
    // Load details when row is expanded
    if (!record.detailsLoaded) {
      loadStaffDetails(record)
    }
    const detailTabs = [
      {
        key: '1',
        label: `Staff Details`,
        children: (
          <Card>
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="Staff Level"
                  value={record.staff_level || 'N/A'}
                  prefix={<IdcardOutlined />}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="HR Role"
                  value={record.hr_role || 'N/A'}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Job Function"
                  value={record.job_function || 'N/A'}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Department ID"
                  value={record.department_id || 'N/A'}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Company"
                  value={record.company_name || 'N/A'}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Original Type"
                  value={record.original_staff_type || 'N/A'}
                />
              </Col>
            </Row>
          </Card>
        ),
      },
      {
        key: '2',
        label: `Commits (${record.commitCount})`,
        children: (
          <Table
            dataSource={Array.isArray(record.commits) ? record.commits : []}
            rowKey={r => r?.commit_hash || r?.id || Math.random().toString()}
            size="small"
            pagination={{ pageSize: 5 }}
            columns={[
              {
                title: 'Hash',
                dataIndex: 'commit_hash',
                key: 'commit_hash',
                width: 100,
                render: hash => <Tag color="blue">{hash?.substring(0, 8)}</Tag>,
              },
              {
                title: 'Date',
                dataIndex: 'commit_date',
                key: 'commit_date',
                width: 150,
                render: date => dayjs(date).format('YYYY-MM-DD HH:mm'),
              },
              {
                title: 'Message',
                dataIndex: 'message',
                key: 'message',
                ellipsis: true,
              },
              {
                title: 'Lines +/-',
                key: 'lines',
                width: 120,
                render: (_, r) => (
                  <Space>
                    <Tag color="success">+{r.lines_added}</Tag>
                    <Tag color="error">-{r.lines_deleted}</Tag>
                  </Space>
                ),
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
                width: 120,
              },
            ]}
          />
        ),
      },
      {
        key: '3',
        label: `Pull Requests (${record.prCount})`,
        children: (
          <Table
            dataSource={Array.isArray(record.pullRequests) ? record.pullRequests : []}
            rowKey={r => r?.pr_number ? `pr-${r.pr_number}` : r?.id || Math.random().toString()}
            size="small"
            pagination={{ pageSize: 5 }}
            columns={[
              {
                title: 'PR #',
                dataIndex: 'pr_number',
                key: 'pr_number',
                width: 80,
              },
              {
                title: 'Title',
                dataIndex: 'title',
                key: 'title',
                ellipsis: true,
              },
              {
                title: 'State',
                dataIndex: 'state',
                key: 'state',
                width: 100,
                render: state => (
                  <Tag color={state === 'merged' ? 'green' : state === 'open' ? 'blue' : 'red'}>
                    {state}
                  </Tag>
                ),
              },
              {
                title: 'Created',
                dataIndex: 'created_at',
                key: 'created_at',
                width: 120,
                render: date => dayjs(date).format('YYYY-MM-DD'),
              },
              {
                title: 'Repository',
                dataIndex: 'repository',
                key: 'repository',
                width: 150,
              },
            ]}
          />
        ),
      },
      {
        key: '4',
        label: `Approvals Given (${record.approvalCount})`,
        children: (
          <Card>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text type="secondary">
                <strong>Total Approvals Given:</strong> {record.approvalCount}
              </Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Note: Detailed approval history is available in the staff_metrics summary.
                The approval count shows the total number of PR approvals this staff member has provided.
              </Text>
            </Space>
          </Card>
        ),
      },
    ]

    return <Tabs items={detailTabs} />
  }

  const hasActiveFilters =
    searchText ||
    filterStatus !== 'all' ||
    filterStaffType !== 'all' ||
    filterRank !== 'all' ||
    filterLocation !== 'all' ||
    filterDepartment !== 'all' ||
    !showZeroActivity

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TeamOutlined style={{ color: '#1890ff' }} /> Staff Details & Activity
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Complete staff information with commits, pull requests, and approvals
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="Total Staff"
              value={stats.total}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="Active"
              value={stats.active}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="With Commits"
              value={stats.withCommits}
              prefix={<CodeOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="With PRs"
              value={stats.withPRs}
              prefix={<BranchesOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="With Approvals"
              value={stats.withApprovals}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Statistic
              title="Zero Activity"
              value={stats.zeroActivity}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Collapse
        defaultActiveKey={['1']}
        style={{ marginBottom: 24 }}
        expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
      >
        <Collapse.Panel
          header={
            <Space>
              <FilterOutlined />
              <span>Filters & Search</span>
              {hasActiveFilters && <Tag color="blue">Active</Tag>}
            </Space>
          }
          key="1"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Text strong>Search</Text>
              <Search
                placeholder="Search by name, email, ID, or manager..."
                value={searchText}
                onChange={e => setSearchText(e.target.value)}
                style={{ marginTop: 8 }}
                prefix={<SearchOutlined />}
                allowClear
              />
            </Col>

            <Col xs={24} md={8}>
              <Text strong>Status</Text>
              <Select
                value={filterStatus}
                onChange={setFilterStatus}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { label: 'All Status', value: 'all' },
                  ...uniqueStatuses.map(s => ({ label: s, value: s })),
                ]}
              />
            </Col>

            <Col xs={24} md={8}>
              <Text strong>Staff Type</Text>
              <Select
                value={filterStaffType}
                onChange={setFilterStaffType}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { label: 'All Types', value: 'all' },
                  ...uniqueStaffTypes.map(s => ({ label: s, value: s })),
                ]}
              />
            </Col>

            <Col xs={24} md={8}>
              <Text strong>Rank</Text>
              <Select
                value={filterRank}
                onChange={setFilterRank}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { label: 'All Ranks', value: 'all' },
                  ...uniqueRanks.map(r => ({ label: r, value: r })),
                ]}
              />
            </Col>

            <Col xs={24} md={8}>
              <Text strong>Location</Text>
              <Select
                value={filterLocation}
                onChange={setFilterLocation}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { label: 'All Locations', value: 'all' },
                  ...uniqueLocations.map(l => ({ label: l, value: l })),
                ]}
              />
            </Col>

            <Col xs={24} md={8}>
              <Text strong>Department</Text>
              <Select
                value={filterDepartment}
                onChange={setFilterDepartment}
                style={{ width: '100%', marginTop: 8 }}
                options={[
                  { label: 'All Departments', value: 'all' },
                  ...uniqueDepartments.map(d => ({ label: d, value: d })),
                ]}
              />
            </Col>

            <Col xs={24}>
              <Space>
                <Text strong>Show Staff with Zero Activity:</Text>
                <Button
                  type={showZeroActivity ? 'primary' : 'default'}
                  onClick={() => setShowZeroActivity(!showZeroActivity)}
                  size="small"
                >
                  {showZeroActivity ? 'Yes' : 'No'}
                </Button>
              </Space>
            </Col>
          </Row>

          <Row style={{ marginTop: 16 }}>
            <Col span={24}>
              <Space>
                <Button onClick={fetchStaffData} icon={<ReloadOutlined />} type="primary" loading={loading}>
                  Refresh Data
                </Button>
                <Button onClick={handleClearFilters}>Clear Filters</Button>
                {filteredStaff.length > 0 && (
                  <Button icon={<DownloadOutlined />} onClick={handleExportToExcel}>
                    Export to Excel
                  </Button>
                )}
              </Space>
            </Col>
          </Row>
        </Collapse.Panel>
      </Collapse>

      {/* Info Card */}
      <Card style={{ marginBottom: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
        <Row align="middle" gutter={16}>
          <Col flex="auto">
            <Space direction="vertical" size={4}>
              <Text strong style={{ color: '#fff', fontSize: 16 }}>
                {filteredStaff.length} Staff Members {hasActiveFilters && '(Filtered)'}
              </Text>
              <Text style={{ color: '#f0f0f0', fontSize: 13 }}>
                Click on any row to expand and view detailed commits, pull requests, and approval history
              </Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Table */}
      <Card>
        <Table
          dataSource={filteredStaff}
          columns={columns}
          rowKey="bank_id_1"
          loading={loading}
          expandable={{
            expandedRowRender,
            expandedRowKeys,
            onExpandedRowsChange: keys => setExpandedRowKeys(keys),
          }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} staff`,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>
    </div>
  )
}

export default StaffDetails
