import React, { useState, useEffect } from 'react'
import {
  Table,
  Card,
  Typography,
  Input,
  Button,
  Space,
  Tag,
  message,
  Select,
  Statistic,
  Row,
  Col,
  Modal,
  Tooltip,
  Divider
} from 'antd'
import {
  SearchOutlined,
  DownloadOutlined,
  ReloadOutlined,
  UserOutlined,
  CodeOutlined,
  BranchesOutlined,
  FileOutlined,
  CalendarOutlined,
  PieChartOutlined,
  BarChartOutlined,
  IdcardOutlined,
  TeamOutlined,
  InfoCircleOutlined
} from '@ant-design/icons'
import axios from 'axios'
import * as XLSX from 'xlsx'

const { Title, Text } = Typography
const { Option } = Select

const CurrentYearStaffMetrics = () => {
  const [staff, setStaff] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [modalVisible, setModalVisible] = useState(false)
  const [currentRecord, setCurrentRecord] = useState(null)

  const currentYear = new Date().getFullYear()

  useEffect(() => {
    fetchStaff()
  }, [statusFilter])

  const fetchStaff = async () => {
    setLoading(true)
    try {
      const params = {}
      if (statusFilter) params.staff_status = statusFilter

      const response = await axios.get('http://localhost:8000/api/staff-metrics/current-year', {
        params
      })
      setStaff(response.data)
      message.success(`Loaded ${response.data.length} current year staff metrics`)
    } catch (error) {
      message.error('Failed to fetch current year staff metrics')
      console.error('Error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (value) => {
    setSearchText(value.toLowerCase())
  }

  const filteredStaff = staff.filter(s =>
    !searchText ||
    s.staff_name?.toLowerCase().includes(searchText) ||
    s.staff_email?.toLowerCase().includes(searchText) ||
    s.bank_id_1?.toLowerCase().includes(searchText)
  )

  const handleRowClick = (record) => {
    setCurrentRecord(record)
    setModalVisible(true)
  }

  const exportToExcel = () => {
    const sheets = []

    // Main sheet with all current year metrics
    sheets.push({
      name: `Current Year ${currentYear}`,
      data: filteredStaff.map(s => ({
        'Bank ID': s.bank_id_1,
        'Staff Name': s.staff_name,
        'Email': s.staff_email,
        'Staff PC Code': s.staff_pc_code || '',
        'Default Role': s.default_role || '',
        'Status': s.staff_status,
        'Year': s.current_year,
        'Total Commits': s.cy_total_commits || 0,
        'Total PRs': s.cy_total_prs || 0,
        'Approvals Given': s.cy_total_approvals_given || 0,
        'Code Reviews Given': s.cy_total_code_reviews_given || 0,
        'Code Reviews Received': s.cy_total_code_reviews_received || 0,
        'Repositories': s.cy_total_repositories || 0,
        'Files Changed': s.cy_total_files_changed || 0,
        'Lines Changed': s.cy_total_lines_changed || 0,
        'Characters Changed': s.cy_total_chars || 0,
        'Code Churn': s.cy_total_code_churn || 0,
        'Different File Types': s.cy_different_file_types || 0,
        'Different Repositories': s.cy_different_repositories || 0,
        'Different Project Keys': s.cy_different_project_keys || 0,
        '% Code Files': (s.cy_pct_code || 0).toFixed(1),
        '% Config Files': (s.cy_pct_config || 0).toFixed(1),
        '% Documentation': (s.cy_pct_documentation || 0).toFixed(1),
        'Avg Commits/Month': (s.cy_avg_commits_monthly || 0).toFixed(2),
        'Avg PRs/Month': (s.cy_avg_prs_monthly || 0).toFixed(2),
        'Avg Approvals/Month': (s.cy_avg_approvals_monthly || 0).toFixed(2),
        'File Types': s.cy_file_types_list || '',
        'Repositories List': s.cy_repositories_list || '',
        'Project Keys': s.cy_project_keys_list || ''
      }))
    })

    const wb = XLSX.utils.book_new()
    sheets.forEach(sheet => {
      const ws = XLSX.utils.json_to_sheet(sheet.data)
      XLSX.utils.book_append_sheet(wb, ws, sheet.name)
    })

    XLSX.writeFile(wb, `current_year_staff_metrics_${currentYear}.xlsx`)
    message.success('Excel file downloaded successfully')
  }

  const columns = [
    {
      title: 'Staff Name',
      dataIndex: 'staff_name',
      key: 'staff_name',
      fixed: 'left',
      width: 200,
      sorter: (a, b) => (a.staff_name || '').localeCompare(b.staff_name || ''),
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Email',
      dataIndex: 'staff_email',
      key: 'staff_email',
      width: 200,
      ellipsis: true
    },
    {
      title: 'Status',
      dataIndex: 'staff_status',
      key: 'staff_status',
      width: 100,
      filters: [
        { text: 'Active', value: 'Active' },
        { text: 'Inactive', value: 'Inactive' }
      ],
      onFilter: (value, record) => record.staff_status === value,
      render: (status) => (
        <Tag color={status === 'Active' ? 'green' : 'red'}>{status}</Tag>
      )
    },
    {
      title: 'Total Commits',
      dataIndex: 'cy_total_commits',
      key: 'cy_total_commits',
      width: 130,
      sorter: (a, b) => (a.cy_total_commits || 0) - (b.cy_total_commits || 0),
      render: (val) => <Text strong>{val || 0}</Text>
    },
    {
      title: 'Total PRs',
      dataIndex: 'cy_total_prs',
      key: 'cy_total_prs',
      width: 110,
      sorter: (a, b) => (a.cy_total_prs || 0) - (b.cy_total_prs || 0),
      render: (val) => val || 0
    },
    {
      title: 'Code Reviews Given',
      dataIndex: 'cy_total_code_reviews_given',
      key: 'cy_total_code_reviews_given',
      width: 160,
      sorter: (a, b) => (a.cy_total_code_reviews_given || 0) - (b.cy_total_code_reviews_given || 0),
      render: (val) => val || 0
    },
    {
      title: 'Code Reviews Received',
      dataIndex: 'cy_total_code_reviews_received',
      key: 'cy_total_code_reviews_received',
      width: 180,
      sorter: (a, b) => (a.cy_total_code_reviews_received || 0) - (b.cy_total_code_reviews_received || 0),
      render: (val) => val || 0
    },
    {
      title: 'Files Changed',
      dataIndex: 'cy_total_files_changed',
      key: 'cy_total_files_changed',
      width: 130,
      sorter: (a, b) => (a.cy_total_files_changed || 0) - (b.cy_total_files_changed || 0),
      render: (val) => val || 0
    },
    {
      title: 'Lines Changed',
      dataIndex: 'cy_total_lines_changed',
      key: 'cy_total_lines_changed',
      width: 130,
      sorter: (a, b) => (a.cy_total_lines_changed || 0) - (b.cy_total_lines_changed || 0),
      render: (val) => val || 0
    },
    {
      title: 'Repositories',
      dataIndex: 'cy_total_repositories',
      key: 'cy_total_repositories',
      width: 120,
      sorter: (a, b) => (a.cy_total_repositories || 0) - (b.cy_total_repositories || 0),
      render: (val) => val || 0
    },
    {
      title: 'File Types',
      dataIndex: 'cy_different_file_types',
      key: 'cy_different_file_types',
      width: 110,
      sorter: (a, b) => (a.cy_different_file_types || 0) - (b.cy_different_file_types || 0),
      render: (val) => val || 0
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>
              <CalendarOutlined /> Current Year Staff Metrics ({currentYear})
            </Title>
            <Text type="secondary">
              View productivity metrics for all staff members for the current year
            </Text>
          </div>

          <Row gutter={16}>
            <Col span={8}>
              <Input
                placeholder="Search by name, email, or bank ID..."
                prefix={<SearchOutlined />}
                onChange={(e) => handleSearch(e.target.value)}
                allowClear
              />
            </Col>
            <Col span={6}>
              <Select
                placeholder="Filter by status"
                style={{ width: '100%' }}
                onChange={setStatusFilter}
                allowClear
              >
                <Option value="">All Staff</Option>
                <Option value="Active">Active</Option>
                <Option value="Inactive">Inactive</Option>
              </Select>
            </Col>
            <Col span={10} style={{ textAlign: 'right' }}>
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={fetchStaff}
                  loading={loading}
                >
                  Refresh
                </Button>
                <Button
                  type="primary"
                  icon={<DownloadOutlined />}
                  onClick={exportToExcel}
                  disabled={filteredStaff.length === 0}
                >
                  Export to Excel
                </Button>
              </Space>
            </Col>
          </Row>

          <Table
            columns={columns}
            dataSource={filteredStaff}
            rowKey="bank_id_1"
            loading={loading}
            scroll={{ x: 1500 }}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} staff members`
            }}
            onRow={(record) => ({
              onClick: () => handleRowClick(record),
              style: { cursor: 'pointer' }
            })}
          />
        </Space>
      </Card>

      {/* Detail Modal */}
      <Modal
        title={<><UserOutlined /> {currentRecord?.staff_name} - Current Year Metrics ({currentYear})</>}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={1200}
      >
        {currentRecord && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            {/* Staff Information */}
            <div>
              <Title level={5}><InfoCircleOutlined /> Staff Information</Title>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Tooltip title="Bank staff identifier">
                    <Statistic
                      title="Bank ID"
                      value={currentRecord.bank_id_1}
                      prefix={<IdcardOutlined />}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Unique staff personal computer code identifier">
                    <Statistic
                      title="Staff PC Code"
                      value={currentRecord.staff_pc_code || 'N/A'}
                      prefix={<IdcardOutlined />}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Default role assigned to this staff member">
                    <Statistic
                      title="Default Role"
                      value={currentRecord.default_role || 'N/A'}
                      prefix={<TeamOutlined />}
                    />
                  </Tooltip>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Activity Totals */}
            <div>
              <Title level={5}><BarChartOutlined /> Activity Totals</Title>
              <Row gutter={[16, 16]}>
                <Col span={6}>
                  <Tooltip title="Total number of commits made in the current year">
                    <Statistic
                      title="Total Commits"
                      value={currentRecord.cy_total_commits || 0}
                      prefix={<CodeOutlined />}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total number of pull requests created in the current year">
                    <Statistic
                      title="Total PRs"
                      value={currentRecord.cy_total_prs || 0}
                      prefix={<BranchesOutlined />}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total number of PR approvals given to other developers">
                    <Statistic
                      title="Approvals Given"
                      value={currentRecord.cy_total_approvals_given || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total number of PRs reviewed (code reviews given to others)">
                    <Statistic
                      title="Code Reviews Given"
                      value={currentRecord.cy_total_code_reviews_given || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total number of code reviews received on own PRs">
                    <Statistic
                      title="Code Reviews Received"
                      value={currentRecord.cy_total_code_reviews_received || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Number of unique repositories worked on">
                    <Statistic
                      title="Repositories"
                      value={currentRecord.cy_total_repositories || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total number of files modified, created, or deleted">
                    <Statistic
                      title="Files Changed"
                      value={currentRecord.cy_total_files_changed || 0}
                      prefix={<FileOutlined />}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total lines of code added plus deleted">
                    <Statistic
                      title="Lines Changed"
                      value={currentRecord.cy_total_lines_changed || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total characters added plus deleted in code">
                    <Statistic
                      title="Characters Changed"
                      value={currentRecord.cy_total_chars || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={6}>
                  <Tooltip title="Total lines of code deleted (code churn indicator)">
                    <Statistic
                      title="Code Churn"
                      value={currentRecord.cy_total_code_churn || 0}
                    />
                  </Tooltip>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Diversity Metrics */}
            <div>
              <Title level={5}><PieChartOutlined /> Diversity Metrics</Title>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Tooltip title="Number of different file types or extensions worked on">
                    <Statistic
                      title="Different File Types"
                      value={currentRecord.cy_different_file_types || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Number of different repositories contributed to">
                    <Statistic
                      title="Different Repositories"
                      value={currentRecord.cy_different_repositories || 0}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Number of different project keys or areas worked on">
                    <Statistic
                      title="Different Project Keys"
                      value={currentRecord.cy_different_project_keys || 0}
                    />
                  </Tooltip>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* File Type Distribution */}
            <div>
              <Title level={5}><FileOutlined /> File Type Distribution</Title>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Tooltip title="Percentage of work on code files (java, js, jsx, tsx, ts, py, sql, etc.)">
                    <Statistic
                      title="% Code Files"
                      value={(currentRecord.cy_pct_code || 0).toFixed(1)}
                      suffix="%"
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Percentage of work on configuration files (xml, json, yml, properties, etc.)">
                    <Statistic
                      title="% Configuration"
                      value={(currentRecord.cy_pct_config || 0).toFixed(1)}
                      suffix="%"
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Percentage of work on documentation files (md, txt, etc.)">
                    <Statistic
                      title="% Documentation"
                      value={(currentRecord.cy_pct_documentation || 0).toFixed(1)}
                      suffix="%"
                    />
                  </Tooltip>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Monthly Averages */}
            <div>
              <Title level={5}><CalendarOutlined /> Monthly Averages</Title>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Tooltip title="Average number of commits per month in the current year">
                    <Statistic
                      title="Avg Commits/Month"
                      value={(currentRecord.cy_avg_commits_monthly || 0).toFixed(2)}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Average number of PRs created per month">
                    <Statistic
                      title="Avg PRs/Month"
                      value={(currentRecord.cy_avg_prs_monthly || 0).toFixed(2)}
                    />
                  </Tooltip>
                </Col>
                <Col span={8}>
                  <Tooltip title="Average number of PR approvals given per month">
                    <Statistic
                      title="Avg Approvals/Month"
                      value={(currentRecord.cy_avg_approvals_monthly || 0).toFixed(2)}
                    />
                  </Tooltip>
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Details Lists */}
            <div>
              <Title level={5}><FileOutlined /> Details</Title>
              <Row gutter={[16, 16]}>
                <Col span={24}>
                  <Text strong>File Types: </Text>
                  <div style={{ marginTop: 8 }}>
                    {currentRecord.cy_file_types_list?.split(',').filter(Boolean).map((type, i) => (
                      <Tag key={i} style={{ marginBottom: 4 }}>{type}</Tag>
                    )) || <Text type="secondary">No file types</Text>}
                  </div>
                </Col>
                <Col span={24}>
                  <Text strong>Repositories: </Text>
                  <div style={{ marginTop: 8 }}>
                    {currentRecord.cy_repositories_list?.split(',').filter(Boolean).map((repo, i) => (
                      <Tag key={i} color="blue" style={{ marginBottom: 4 }}>{repo}</Tag>
                    )) || <Text type="secondary">No repositories</Text>}
                  </div>
                </Col>
                <Col span={24}>
                  <Text strong>Project Keys: </Text>
                  <div style={{ marginTop: 8 }}>
                    {currentRecord.cy_project_keys_list?.split(',').filter(Boolean).map((key, i) => (
                      <Tag key={i} color="green" style={{ marginBottom: 4 }}>{key}</Tag>
                    )) || <Text type="secondary">No project keys</Text>}
                  </div>
                </Col>
              </Row>
            </div>
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default CurrentYearStaffMetrics
