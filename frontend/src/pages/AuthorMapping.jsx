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

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      setLoading(true)
      const [authorsData, staffData, mappingsData] = await Promise.all([
        mappingsAPI.getUnmappedAuthors(),
        staffAPI.getStaffList({ limit: 1000 }),
        mappingsAPI.getMappings(),
      ])
      setUnmappedAuthors(authorsData)
      setStaffList(staffData)
      setMappings(mappingsData)
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

  const bulkOperationsTab = (
    <div>
      <Card title="⚡ Auto-Match by Email" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Text>
            Automatically map authors to staff members when their email addresses match.
          </Text>
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
            Run Auto-Match
          </Button>
        </Space>
      </Card>

      <Card title="📊 Statistics">
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong>Unmapped Authors: </Text>
            <Tag color="orange">{unmappedAuthors.length}</Tag>
          </div>
          <div>
            <Text strong>Total Staff Members: </Text>
            <Tag color="blue">{staffList.length}</Tag>
          </div>
          <div>
            <Text strong>Existing Mappings: </Text>
            <Tag color="green">{mappings.length}</Tag>
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
