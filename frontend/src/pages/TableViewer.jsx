import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Select,
  Button,
  Space,
  message,
  Typography,
  Row,
  Col,
  Statistic,
  Tag,
  Input,
  Spin,
  Alert,
} from 'antd'
import {
  DatabaseOutlined,
  DownloadOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons'
import { tablesAPI } from '../services/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography

const TableViewer = () => {
  const [tableInfo, setTableInfo] = useState({})
  const [selectedTable, setSelectedTable] = useState('repositories')
  const [tableData, setTableData] = useState([])
  const [loading, setLoading] = useState(false)
  const [limit, setLimit] = useState(100)
  const [searchText, setSearchText] = useState('')

  useEffect(() => {
    fetchTableInfo()
  }, [])

  const fetchTableInfo = async () => {
    try {
      const data = await tablesAPI.getTableInfo()
      setTableInfo(data)
    } catch (err) {
      message.error('Failed to fetch table information')
    }
  }

  const fetchTableData = async () => {
    try {
      setLoading(true)
      const data = await tablesAPI.getTableData(selectedTable, { limit })
      setTableData(data)
    } catch (err) {
      message.error('Failed to fetch table data')
    } finally {
      setLoading(false)
    }
  }

  const handleLoadData = () => {
    fetchTableData()
  }

  const handleDownload = () => {
    if (!tableData.length) {
      message.warning('No data to download')
      return
    }

    const headers = Object.keys(tableData[0])
    const csv = [
      headers.join(','),
      ...tableData.map((row) =>
        headers.map((h) => {
          const val = row[h]
          if (val === null || val === undefined) return ''
          return typeof val === 'string' && val.includes(',') ? `"${val}"` : val
        }).join(',')
      ),
    ].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${selectedTable}_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  // Generate dynamic columns from data
  const columns = tableData.length > 0
    ? Object.keys(tableData[0]).map((key) => ({
        title: key.replace(/_/g, ' ').toUpperCase(),
        dataIndex: key,
        key,
        ellipsis: true,
        width: 150,
        render: (val) => {
          if (val === null || val === undefined) return <Text type="secondary">NULL</Text>
          if (typeof val === 'boolean') return val ? 'true' : 'false'
          if (key.includes('date') || key.includes('Date')) {
            try {
              return dayjs(val).format('YYYY-MM-DD HH:mm')
            } catch {
              return val
            }
          }
          return val.toString()
        },
        ...(key === 'id' ? { fixed: 'left', width: 80 } : {}),
      }))
    : []

  // Filter data by search
  const filteredData = searchText
    ? tableData.filter((row) =>
        Object.values(row).some((val) =>
          val?.toString().toLowerCase().includes(searchText.toLowerCase())
        )
      )
    : tableData

  return (
    <div>
      <Title level={2}>
        <DatabaseOutlined style={{ color: '#722ed1' }} /> Database Table Viewer
      </Title>

      {/* Table Info Overview */}
      <Card title="📊 Tables Overview" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {Object.entries(tableInfo).map(([tableName, rowCount]) => (
            <Col xs={24} sm={12} md={8} lg={6} key={tableName}>
              <Card
                hoverable
                onClick={() => setSelectedTable(tableName)}
                style={{
                  backgroundColor: selectedTable === tableName ? '#e6f7ff' : '#fff',
                  borderColor: selectedTable === tableName ? '#1890ff' : '#d9d9d9',
                }}
              >
                <Statistic
                  title={tableName.replace(/_/g, ' ').toUpperCase()}
                  value={rowCount}
                  suffix="rows"
                  valueStyle={{
                    color: selectedTable === tableName ? '#1890ff' : '#000',
                  }}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Controls */}
      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Text strong>Select Table:</Text>
                <Select
                  value={selectedTable}
                  onChange={setSelectedTable}
                  style={{ width: 200 }}
                >
                  {Object.keys(tableInfo).map((table) => (
                    <Select.Option key={table} value={table}>
                      {table} ({tableInfo[table]} rows)
                    </Select.Option>
                  ))}
                </Select>
              </Space>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Space>
                <Text strong>Limit:</Text>
                <Input
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(parseInt(e.target.value) || 100)}
                  style={{ width: 120 }}
                  min={10}
                  max={10000}
                />
              </Space>
            </Col>
            <Col xs={24} sm={12} md={8}>
              <Input
                placeholder="Search in results..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                allowClear
              />
            </Col>
          </Row>
          <Row gutter={[8, 8]}>
            <Col>
              <Button
                type="primary"
                icon={<DatabaseOutlined />}
                onClick={handleLoadData}
                loading={loading}
              >
                Load Data
              </Button>
            </Col>
            <Col>
              <Button icon={<ReloadOutlined />} onClick={fetchTableInfo}>
                Refresh Info
              </Button>
            </Col>
            <Col>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleDownload}
                disabled={!tableData.length}
              >
                Download CSV
              </Button>
            </Col>
          </Row>
        </Space>
      </Card>

      {/* Data Table */}
      {tableData.length > 0 ? (
        <Card
          title={
            <Space>
              <Text strong>Table: {selectedTable}</Text>
              <Tag color="blue">{filteredData.length} rows</Tag>
              {searchText && <Tag color="orange">Filtered</Tag>}
            </Space>
          }
        >
          <Table
            columns={columns}
            dataSource={filteredData}
            rowKey={(record) => record.id || `row-${JSON.stringify(record)}`}
            loading={loading}
            scroll={{ x: 'max-content' }}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} rows`,
            }}
          />
        </Card>
      ) : loading ? (
        <div style={{ padding: '50px', textAlign: 'center' }}>
          <Spin size="large" tip={`Loading ${selectedTable} data...`}>
            <div style={{ minHeight: '400px' }} />
          </Spin>
        </div>
      ) : (
        <Alert
          message="No Data Loaded"
          description="Click 'Load Data' to view table contents"
          type="info"
          showIcon
        />
      )}
    </div>
  )
}

export default TableViewer
