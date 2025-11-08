import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Typography,
  Tabs,
  Select,
  Input,
  Row,
  Col,
  Statistic,
  Modal,
  Progress,
  Tag,
  Divider,
  List,
  Checkbox,
  Tooltip,
  Alert,
  Badge,
} from 'antd'
import {
  LinkOutlined,
  SaveOutlined,
  DeleteOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  UserOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  BulbOutlined,
  SelectOutlined,
  ClearOutlined,
} from '@ant-design/icons'
import { mappingsAPI, staffAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { TextArea } = Input

const AuthorMapping = () => {
  const [unmappedAuthors, setUnmappedAuthors] = useState([])
  const [staffList, setStaffList] = useState([])
  const [mappings, setMappings] = useState([])
  const [loading, setLoading] = useState(false)
  const [selectedAuthor, setSelectedAuthor] = useState(null)
  const [selectedStaff, setSelectedStaff] = useState(null)
  const [searchStaff, setSearchStaff] = useState('')
  const [notes, setNotes] = useState('')
  const [autoMatchLoading, setAutoMatchLoading] = useState(false)
  const [autoMatchProgress, setAutoMatchProgress] = useState(0)

  // Multi-select state
  const [selectedAuthors, setSelectedAuthors] = useState([])
  const [bulkStaff, setBulkStaff] = useState(null)
  const [bulkNotes, setBulkNotes] = useState('')
  const [searchAuthor, setSearchAuthor] = useState('')

  // Reverse mapping state (staff to author)
  const [unmappedStaff, setUnmappedStaff] = useState([])
  const [selectedStaffMember, setSelectedStaffMember] = useState(null)
  const [selectedAuthorForStaff, setSelectedAuthorForStaff] = useState(null)
  const [reverseNotes, setReverseNotes] = useState('')
  const [searchUnmappedStaff, setSearchUnmappedStaff] = useState('')

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [authorsData, staffData, mappingsData, unmappedStaffData] = await Promise.all([
        mappingsAPI.getUnmappedAuthors(),
        staffAPI.getStaffList({ limit: 1000 }),
        mappingsAPI.getMappings(),
        staffAPI.getUnmappedStaff({ limit: 1000 }),
      ])
      setUnmappedAuthors(authorsData)
      setStaffList(staffData)
      setMappings(mappingsData)
      setUnmappedStaff(unmappedStaffData)
    } catch (err) {
      message.error('Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const handleCreateMapping = async () => {
    if (!selectedAuthor || !selectedStaff) {
      message.warning('Please select both author and staff member')
      return
    }

    try {
      await mappingsAPI.createMapping({
        author_name: selectedAuthor.author_name,
        author_email: selectedAuthor.author_email,
        bank_id_1: selectedStaff.bank_id_1,
        staff_id: selectedStaff.staff_id,
        staff_name: selectedStaff.staff_name,
        notes: notes,
      })
      message.success('Mapping created successfully!')
      setSelectedAuthor(null)
      setSelectedStaff(null)
      setNotes('')
      fetchData()
    } catch (err) {
      message.error('Failed to create mapping')
    }
  }

  const handleDeleteMapping = async (authorName) => {
    try {
      await mappingsAPI.deleteMapping(authorName)
      message.success('Mapping deleted successfully!')
      fetchData()
    } catch (err) {
      message.error('Failed to delete mapping')
    }
  }

  // Calculate name similarity (simple Levenshtein distance)
  const calculateSimilarity = (str1, str2) => {
    const s1 = str1.toLowerCase()
    const s2 = str2.toLowerCase()

    if (s1 === s2) return 1.0
    if (s1.includes(s2) || s2.includes(s1)) return 0.8

    // Simple similarity based on word overlap
    const words1 = s1.split(/\s+/)
    const words2 = s2.split(/\s+/)
    const commonWords = words1.filter(w => words2.includes(w))

    if (commonWords.length > 0) {
      return commonWords.length / Math.max(words1.length, words2.length)
    }

    return 0
  }

  // Get suggested staff for an author
  const getSuggestedStaff = (author) => {
    return staffList
      .map(staff => ({
        ...staff,
        similarity: calculateSimilarity(author.author_name, staff.staff_name)
      }))
      .filter(s => s.similarity > 0.3)
      .sort((a, b) => b.similarity - a.similarity)
      .slice(0, 3)
  }

  // Handle bulk mapping
  const handleBulkMapping = async () => {
    if (selectedAuthors.length === 0) {
      message.warning('Please select at least one author')
      return
    }
    if (!bulkStaff) {
      message.warning('Please select a staff member')
      return
    }

    Modal.confirm({
      title: 'Bulk Mapping Confirmation',
      content: `Map ${selectedAuthors.length} author(s) to ${bulkStaff.staff_name}?`,
      onOk: async () => {
        setAutoMatchLoading(true)
        setAutoMatchProgress(0)

        let successCount = 0
        for (let i = 0; i < selectedAuthors.length; i++) {
          try {
            const author = unmappedAuthors.find(a => a.author_name === selectedAuthors[i])
            await mappingsAPI.createMapping({
              author_name: author.author_name,
              author_email: author.author_email,
              bank_id_1: bulkStaff.bank_id_1,
              staff_id: bulkStaff.staff_id,
              staff_name: bulkStaff.staff_name,
              notes: bulkNotes || 'Bulk mapped',
            })
            successCount++
            setAutoMatchProgress(Math.round(((i + 1) / selectedAuthors.length) * 100))
          } catch (err) {
            console.error('Failed to create mapping:', err)
          }
        }

        message.success(`Successfully mapped ${successCount} of ${selectedAuthors.length} authors!`)
        setSelectedAuthors([])
        setBulkStaff(null)
        setBulkNotes('')
        setAutoMatchLoading(false)
        setAutoMatchProgress(0)
        fetchData()
      }
    })
  }

  const handleAutoMatch = async () => {
    Modal.confirm({
      title: 'Auto-Match by Email',
      content: 'This will automatically map authors to staff members when emails match. Continue?',
      onOk: async () => {
        setAutoMatchLoading(true)
        setAutoMatchProgress(0)

        try {
          // Find matches
          const matches = []
          for (const author of unmappedAuthors) {
            const matchingStaff = staffList.find(
              (s) => s.email_address?.toLowerCase() === author.author_email?.toLowerCase()
            )
            if (matchingStaff) {
              matches.push({
                author_name: author.author_name,
                author_email: author.author_email,
                bank_id_1: matchingStaff.bank_id_1,
                staff_id: matchingStaff.staff_id,
                staff_name: matchingStaff.staff_name,
                notes: 'Auto-matched by email',
              })
            }
          }

          if (matches.length === 0) {
            message.info('No email matches found')
            setAutoMatchLoading(false)
            return
          }

          // Create mappings
          let successCount = 0
          for (let i = 0; i < matches.length; i++) {
            try {
              await mappingsAPI.createMapping(matches[i])
              successCount++
              setAutoMatchProgress(Math.round(((i + 1) / matches.length) * 100))
            } catch (err) {
              console.error('Failed to create mapping:', err)
            }
          }

          message.success(`Auto-matched ${successCount} authors!`)
          fetchData()
        } catch (err) {
          message.error('Auto-match failed')
        } finally {
          setAutoMatchLoading(false)
          setAutoMatchProgress(0)
        }
      },
    })
  }

  const handleDownload = () => {
    const headers = ['Author Name', 'Author Email', 'Bank ID', 'Staff ID', 'Staff Name', 'Mapped Date', 'Notes']
    const csv = [
      headers.join(','),
      ...mappings.map((m) =>
        [
          m.author_name,
          m.author_email,
          m.bank_id_1,
          m.staff_id,
          m.staff_name,
          m.mapped_date,
          m.notes || '',
        ].join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `author_staff_mappings_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  const handleReverseMapping = async () => {
    if (!selectedStaffMember || !selectedAuthorForStaff) {
      message.warning('Please select both staff member and author')
      return
    }

    try {
      await mappingsAPI.createMapping({
        author_name: selectedAuthorForStaff.author_name,
        author_email: selectedAuthorForStaff.author_email,
        bank_id_1: selectedStaffMember.bank_id_1,
        staff_id: selectedStaffMember.staff_id,
        staff_name: selectedStaffMember.staff_name,
        notes: reverseNotes || 'Reverse mapped (staff to author)',
      })

      message.success(`Mapped ${selectedStaffMember.staff_name} to ${selectedAuthorForStaff.author_name}!`)
      setSelectedStaffMember(null)
      setSelectedAuthorForStaff(null)
      setReverseNotes('')
      fetchData()
    } catch (err) {
      message.error('Failed to create reverse mapping')
    }
  }

  // Filter staff by search
  const filteredStaff = searchStaff
    ? staffList.filter(
        (s) =>
          s.staff_name?.toLowerCase().includes(searchStaff.toLowerCase()) ||
          s.email_address?.toLowerCase().includes(searchStaff.toLowerCase())
      )
    : staffList

  const mappingsColumns = [
    {
      title: 'Author Name',
      dataIndex: 'author_name',
      key: 'author_name',
      width: 200,
      fixed: 'left',
      render: (name) => (
        <Space>
          <UserOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Author Email',
      dataIndex: 'author_email',
      key: 'author_email',
      width: 250,
    },
    {
      title: 'Bank ID',
      dataIndex: 'bank_id_1',
      key: 'bank_id_1',
      width: 120,
      render: (id) => <Tag color="blue">{id}</Tag>,
    },
    {
      title: 'Staff Name',
      dataIndex: 'staff_name',
      key: 'staff_name',
      width: 200,
    },
    {
      title: 'Mapped Date',
      dataIndex: 'mapped_date',
      key: 'mapped_date',
      width: 180,
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Notes',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="link"
          danger
          icon={<DeleteOutlined />}
          onClick={() => handleDeleteMapping(record.author_name)}
        >
          Delete
        </Button>
      ),
    },
  ]

  const createMappingTab = (
    <div>
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={12}>
          <Card title={<Space><UserOutlined /> Select Author</Space>} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Statistic
                title="Unmapped Authors"
                value={unmappedAuthors.length}
                prefix={<TeamOutlined />}
              />
              <Select
                style={{ width: '100%' }}
                placeholder="Select author to map"
                showSearch
                value={selectedAuthor?.author_name}
                onChange={(value) => {
                  const author = unmappedAuthors.find((a) => a.author_name === value)
                  setSelectedAuthor(author)
                }}
                filterOption={(input, option) =>
                  (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
                }
              >
                {unmappedAuthors.map((author) => (
                  <Select.Option key={author.author_name} value={author.author_name}>
                    {author.author_name} ({author.commit_count} commits)
                  </Select.Option>
                ))}
              </Select>
              {selectedAuthor && (
                <Card size="small" style={{ backgroundColor: '#f0f2f5' }}>
                  <Space direction="vertical" size="small">
                    <Text strong>Email:</Text>
                    <Text>{selectedAuthor.author_email}</Text>
                    <Text strong>Total Commits:</Text>
                    <Text>{selectedAuthor.commit_count}</Text>
                  </Space>
                </Card>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={<Space><TeamOutlined /> Select Staff Member</Space>} bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Input
                placeholder="Search staff by name or email..."
                value={searchStaff}
                onChange={(e) => setSearchStaff(e.target.value)}
                allowClear
              />
              <Select
                style={{ width: '100%' }}
                placeholder="Select staff member"
                showSearch
                value={selectedStaff?.staff_name}
                onChange={(value) => {
                  const staff = staffList.find((s) => s.staff_name === value)
                  setSelectedStaff(staff)
                }}
                filterOption={(input, option) =>
                  (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
                }
              >
                {filteredStaff.map((staff) => (
                  <Select.Option key={staff.bank_id_1} value={staff.staff_name}>
                    {staff.staff_name} ({staff.bank_id_1})
                  </Select.Option>
                ))}
              </Select>
              {selectedStaff && (
                <Card size="small" style={{ backgroundColor: '#f0f2f5' }}>
                  <Space direction="vertical" size="small">
                    <Text strong>Bank ID:</Text>
                    <Text>{selectedStaff.bank_id_1}</Text>
                    <Text strong>Email:</Text>
                    <Text>{selectedStaff.email_address}</Text>
                    <Text strong>Tech Unit:</Text>
                    <Text>{selectedStaff.tech_unit}</Text>
                  </Space>
                </Card>
              )}
            </Space>
          </Card>
        </Col>
      </Row>

      <Divider />

      <Card title="💾 Save Mapping">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <TextArea
            placeholder="Add notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
          />
          <Button
            type="primary"
            size="large"
            icon={<SaveOutlined />}
            onClick={handleCreateMapping}
            disabled={!selectedAuthor || !selectedStaff}
            block
          >
            Create Mapping
          </Button>
        </Space>
      </Card>
    </div>
  )

  const viewMappingsTab = (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Mappings"
              value={mappings.length}
              prefix={<LinkOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Total Authors"
              value={unmappedAuthors.length + mappings.length}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Mapping Coverage"
              value={
                unmappedAuthors.length + mappings.length > 0
                  ? Math.round((mappings.length / (unmappedAuthors.length + mappings.length)) * 100)
                  : 0
              }
              suffix="%"
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Existing Mappings"
        extra={
          <Button icon={<DownloadOutlined />} onClick={handleDownload}>
            Download CSV
          </Button>
        }
      >
        <Table
          columns={mappingsColumns}
          dataSource={mappings}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            pageSize: 20,
            showTotal: (total) => `Total ${total} mappings`,
          }}
        />
      </Card>
    </div>
  )

  // Filter authors by search
  const filteredUnmappedAuthors = searchAuthor
    ? unmappedAuthors.filter(a =>
        a.author_name?.toLowerCase().includes(searchAuthor.toLowerCase()) ||
        a.author_email?.toLowerCase().includes(searchAuthor.toLowerCase())
      )
    : unmappedAuthors

  const bulkOperationsTab = (
    <div>
      {/* Auto-Match by Email */}
      <Card title="⚡ Auto-Match by Email" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Alert
            message="Automatic Email Matching"
            description="This will automatically map authors to active staff members when their email addresses match exactly. Inactive staff members are excluded from matching."
            type="info"
            showIcon
          />
          {autoMatchLoading && (
            <Progress percent={autoMatchProgress} status="active" />
          )}
          <Button
            type="primary"
            size="large"
            icon={<ThunderboltOutlined />}
            onClick={handleAutoMatch}
            loading={autoMatchLoading}
            block
          >
            Run Auto-Match by Email
          </Button>
        </Space>
      </Card>

      {/* Multi-Select Bulk Mapping */}
      <Card
        title="📋 Bulk Mapping (Multi-Select)"
        style={{ marginBottom: 24 }}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>Only active staff members shown</Text>}
      >
        <Row gutter={[24, 24]}>
          {/* Left: Author Selection */}
          <Col xs={24} lg={14}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Space style={{ marginBottom: 12 }}>
                  <Text strong>Select Authors to Map:</Text>
                  <Badge count={selectedAuthors.length} showZero color="blue" />
                </Space>
                <Space style={{ marginBottom: 8, width: '100%' }}>
                  <Input
                    placeholder="Search authors..."
                    value={searchAuthor}
                    onChange={(e) => setSearchAuthor(e.target.value)}
                    allowClear
                    style={{ width: 300 }}
                  />
                  <Button
                    size="small"
                    icon={<SelectOutlined />}
                    onClick={() => setSelectedAuthors(filteredUnmappedAuthors.map(a => a.author_name))}
                  >
                    Select All ({filteredUnmappedAuthors.length})
                  </Button>
                  <Button
                    size="small"
                    icon={<ClearOutlined />}
                    onClick={() => setSelectedAuthors([])}
                    disabled={selectedAuthors.length === 0}
                  >
                    Clear
                  </Button>
                </Space>
              </div>

              <div style={{ maxHeight: 400, overflowY: 'auto', border: '1px solid #f0f0f0', borderRadius: 4, padding: 8 }}>
                <List
                  dataSource={filteredUnmappedAuthors}
                  renderItem={(author) => {
                    const suggestions = getSuggestedStaff(author)
                    const isSelected = selectedAuthors.includes(author.author_name)

                    return (
                      <List.Item
                        style={{
                          backgroundColor: isSelected ? '#e6f7ff' : 'transparent',
                          padding: '12px',
                          borderRadius: 4,
                          marginBottom: 4,
                          cursor: 'pointer'
                        }}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedAuthors(prev => prev.filter(name => name !== author.author_name))
                          } else {
                            setSelectedAuthors(prev => [...prev, author.author_name])
                          }
                        }}
                      >
                        <List.Item.Meta
                          avatar={
                            <Checkbox
                              checked={isSelected}
                              onChange={(e) => {
                                e.stopPropagation()
                                if (e.target.checked) {
                                  setSelectedAuthors(prev => [...prev, author.author_name])
                                } else {
                                  setSelectedAuthors(prev => prev.filter(name => name !== author.author_name))
                                }
                              }}
                            />
                          }
                          title={
                            <Space direction="vertical" size={0}>
                              <Text strong>{author.author_name}</Text>
                              <Text type="secondary" style={{ fontSize: 12 }}>{author.author_email}</Text>
                              <Text type="secondary" style={{ fontSize: 11 }}>{author.commit_count} commits</Text>
                            </Space>
                          }
                          description={
                            suggestions.length > 0 && (
                              <Space size={4} wrap>
                                <Tooltip title="Suggested matches based on name similarity">
                                  <BulbOutlined style={{ color: '#faad14' }} />
                                </Tooltip>
                                {suggestions.map((staff, idx) => (
                                  <Tag
                                    key={idx}
                                    color={staff.similarity > 0.7 ? 'green' : staff.similarity > 0.5 ? 'orange' : 'default'}
                                    style={{ fontSize: 11 }}
                                  >
                                    {staff.staff_name} ({Math.round(staff.similarity * 100)}%)
                                  </Tag>
                                ))}
                              </Space>
                            )
                          }
                        />
                      </List.Item>
                    )
                  }}
                />
              </div>
            </Space>
          </Col>

          {/* Right: Staff Selection */}
          <Col xs={24} lg={10}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Text strong>Map Selected Authors To:</Text>
              <Select
                style={{ width: '100%' }}
                placeholder="Select staff member"
                showSearch
                value={bulkStaff?.staff_name}
                onChange={(value) => {
                  const staff = staffList.find((s) => s.staff_name === value)
                  setBulkStaff(staff)
                }}
                filterOption={(input, option) =>
                  (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
                }
              >
                {staffList.map((staff) => (
                  <Select.Option key={staff.bank_id_1} value={staff.staff_name}>
                    {staff.staff_name} ({staff.bank_id_1})
                  </Select.Option>
                ))}
              </Select>

              {bulkStaff && (
                <Card size="small" style={{ backgroundColor: '#f0f2f5' }}>
                  <Space direction="vertical" size="small">
                    <Text strong>Staff Details:</Text>
                    <Text>Bank ID: {bulkStaff.bank_id_1}</Text>
                    <Text>Email: {bulkStaff.email_address}</Text>
                    <Text>Tech Unit: {bulkStaff.tech_unit}</Text>
                  </Space>
                </Card>
              )}

              <TextArea
                placeholder="Add notes (optional)..."
                value={bulkNotes}
                onChange={(e) => setBulkNotes(e.target.value)}
                rows={3}
              />

              {autoMatchLoading && (
                <Progress percent={autoMatchProgress} status="active" />
              )}

              <Button
                type="primary"
                size="large"
                icon={<SaveOutlined />}
                onClick={handleBulkMapping}
                disabled={selectedAuthors.length === 0 || !bulkStaff || autoMatchLoading}
                block
              >
                Map {selectedAuthors.length} Author(s) to {bulkStaff?.staff_name || 'Staff'}
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Reverse Mapping: Staff to Author */}
      <Card
        title="🔄 Reverse Mapping (Staff → Author)"
        style={{ marginBottom: 24 }}
        extra={<Text type="secondary" style={{ fontSize: 12 }}>Map unmapped staff to authors</Text>}
      >
        <Alert
          message="Reverse Mapping"
          description="Select an unmapped staff member and map them to a Git author. This is useful when you know the staff member but need to find their corresponding Git identity."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Row gutter={[24, 24]}>
          {/* Left: Staff Selection */}
          <Col xs={24} lg={12}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>Step 1: Select Unmapped Staff Member</Text>
                <Input
                  placeholder="Search staff by name or email..."
                  value={searchUnmappedStaff}
                  onChange={(e) => setSearchUnmappedStaff(e.target.value)}
                  allowClear
                  style={{ marginTop: 8, marginBottom: 8 }}
                />
                <Select
                  showSearch
                  placeholder="Select staff member..."
                  style={{ width: '100%' }}
                  value={selectedStaffMember?.bank_id_1}
                  onChange={(value) => {
                    const staff = unmappedStaff.find(s => s.bank_id_1 === value)
                    setSelectedStaffMember(staff)
                    setSelectedAuthorForStaff(null)
                  }}
                  filterOption={(input, option) =>
                    (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
                  }
                  options={unmappedStaff
                    .filter(s =>
                      !searchUnmappedStaff ||
                      s.staff_name?.toLowerCase().includes(searchUnmappedStaff.toLowerCase()) ||
                      s.email_address?.toLowerCase().includes(searchUnmappedStaff.toLowerCase())
                    )
                    .map(s => ({
                      value: s.bank_id_1,
                      label: `${s.staff_name} (${s.email_address})`
                    }))}
                />
              </div>

              {selectedStaffMember && (
                <Card size="small" style={{ backgroundColor: '#f0f9ff' }}>
                  <Space direction="vertical" size="small">
                    <Text strong>Selected Staff:</Text>
                    <Text>Name: {selectedStaffMember.staff_name}</Text>
                    <Text>Email: {selectedStaffMember.email_address}</Text>
                    <Text>Bank ID: {selectedStaffMember.bank_id_1}</Text>
                    <Text>Tech Unit: {selectedStaffMember.tech_unit}</Text>
                  </Space>
                </Card>
              )}
            </Space>
          </Col>

          {/* Right: Author Selection */}
          <Col xs={24} lg={12}>
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>Step 2: Select Author to Map To</Text>
                <Select
                  showSearch
                  placeholder="Select author..."
                  style={{ width: '100%', marginTop: 8 }}
                  value={selectedAuthorForStaff?.author_name}
                  onChange={(value) => {
                    const author = unmappedAuthors.find(a => a.author_name === value)
                    setSelectedAuthorForStaff(author)
                  }}
                  disabled={!selectedStaffMember}
                  filterOption={(input, option) =>
                    (option?.value?.toLowerCase() || '').includes(input.toLowerCase())
                  }
                  options={unmappedAuthors.map(a => ({
                    value: a.author_name,
                    label: `${a.author_name} (${a.author_email}) - ${a.commit_count} commits`
                  }))}
                />
              </div>

              {selectedAuthorForStaff && (
                <Card size="small" style={{ backgroundColor: '#f0f9ff' }}>
                  <Space direction="vertical" size="small">
                    <Text strong>Selected Author:</Text>
                    <Text>Name: {selectedAuthorForStaff.author_name}</Text>
                    <Text>Email: {selectedAuthorForStaff.author_email}</Text>
                    <Text>Commits: {selectedAuthorForStaff.commit_count}</Text>
                  </Space>
                </Card>
              )}

              <TextArea
                placeholder="Add notes (optional)..."
                value={reverseNotes}
                onChange={(e) => setReverseNotes(e.target.value)}
                rows={3}
                disabled={!selectedStaffMember || !selectedAuthorForStaff}
              />

              <Button
                type="primary"
                size="large"
                icon={<LinkOutlined />}
                onClick={handleReverseMapping}
                disabled={!selectedStaffMember || !selectedAuthorForStaff}
                block
              >
                Create Mapping
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Statistics */}
      <Card title="📊 Statistics">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong>Unmapped Authors: </Text>
            <Tag color="orange">{unmappedAuthors.length}</Tag>
          </div>
          <div>
            <Text strong>Unmapped Staff: </Text>
            <Tag color="orange">{unmappedStaff.length}</Tag>
          </div>
          <div>
            <Text strong>Selected for Mapping: </Text>
            <Tag color="blue">{selectedAuthors.length}</Tag>
          </div>
          <div>
            <Text strong>Total Staff Members: </Text>
            <Tag color="cyan">{staffList.length}</Tag>
          </div>
          <div>
            <Text strong>Existing Mappings: </Text>
            <Tag color="green">{mappings.length}</Tag>
          </div>
          <div>
            <Text strong>Mapping Progress: </Text>
            <Tag color="purple">
              {((mappings.length / (mappings.length + unmappedAuthors.length)) * 100).toFixed(1)}%
            </Tag>
          </div>
        </Space>
      </Card>
    </div>
  )

  return (
    <div>
      <Title level={2}>
        <LinkOutlined style={{ color: '#1890ff' }} /> Author-Staff Mapping
      </Title>
      <Text type="secondary" style={{ fontSize: 16, display: 'block', marginBottom: 24 }}>
        Link Git commit authors with official staff records
      </Text>

      <Tabs
        defaultActiveKey="1"
        items={[
          {
            key: '1',
            label: 'Create Mapping',
            children: createMappingTab,
          },
          {
            key: '2',
            label: 'View Mappings',
            children: viewMappingsTab,
          },
          {
            key: '3',
            label: 'Bulk Operations',
            children: bulkOperationsTab,
          },
        ]}
      />
    </div>
  )
}

export default AuthorMapping
