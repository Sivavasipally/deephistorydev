import React, { useState } from 'react'
import {
  Card,
  Input,
  Button,
  Table,
  Alert,
  Typography,
  Space,
  Divider,
  Select,
  message,
  Collapse,
  Tag,
  Row,
  Col,
} from 'antd'
import {
  PlayCircleOutlined,
  RobotOutlined,
  DownloadOutlined,
  CodeOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import { sqlAPI } from '../services/api'
import dayjs from 'dayjs'

const { TextArea } = Input
const { Title, Paragraph, Text } = Typography
const { Panel } = Collapse

const sampleQueries = {
  'Select All Repositories': 'SELECT * FROM repositories LIMIT 10;',
  'Top 10 Authors by Commits': `SELECT author_name, COUNT(*) as commit_count
FROM commits
GROUP BY author_name
ORDER BY commit_count DESC
LIMIT 10;`,
  'PRs with Most Approvals': `SELECT pr.pr_number, pr.title, pr.author_name,
       COUNT(pa.id) as approval_count
FROM pull_requests pr
LEFT JOIN pr_approvals pa ON pr.id = pa.pull_request_id
GROUP BY pr.id
ORDER BY approval_count DESC
LIMIT 10;`,
  'Commits by Month': `SELECT strftime('%Y-%m', commit_date) as month,
       COUNT(*) as commits,
       SUM(lines_added) as total_added,
       SUM(lines_deleted) as total_deleted
FROM commits
GROUP BY month
ORDER BY month DESC;`,
  'Staff by Department': `SELECT tech_unit, COUNT(*) as staff_count
FROM staff_details
GROUP BY tech_unit
ORDER BY staff_count DESC;`,
}

const schemaInfo = `
**repositories**
- id, project_key, slug_name, clone_url, created_at

**commits**
- id, repository_id, commit_hash, author_name, author_email
- committer_name, committer_email, commit_date, message
- lines_added, lines_deleted, files_changed, branch

**pull_requests**
- id, repository_id, pr_number, title, description
- author_name, author_email, created_date, merged_date
- state, source_branch, target_branch
- lines_added, lines_deleted, commits_count

**pr_approvals**
- id, pull_request_id, approver_name, approver_email, approval_date

**staff_details**
- id, bank_id_1, staff_id, staff_name, email_address
- staff_start_date, staff_end_date, tech_unit, platform_name
- staff_type, staff_status, rank, department_id

**author_staff_mapping**
- id, author_name, author_email, bank_id_1
- staff_id, staff_name, mapped_date, notes
`

const SQLExecutor = () => {
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM repositories LIMIT 10;')
  const [aiPrompt, setAiPrompt] = useState('')
  const [generatedSQL, setGeneratedSQL] = useState(null)
  const [queryResult, setQueryResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleExecute = async () => {
    if (!sqlQuery.trim()) {
      message.warning('Please enter a SQL query')
      return
    }

    // Check for destructive queries
    const destructiveKeywords = ['UPDATE', 'DELETE', 'DROP', 'ALTER', 'INSERT']
    const isDestructive = destructiveKeywords.some((keyword) =>
      sqlQuery.trim().toUpperCase().startsWith(keyword)
    )

    if (isDestructive) {
      message.warning('⚠️ Detected potentially destructive query. Use with caution!')
    }

    try {
      setLoading(true)
      setError(null)
      const result = await sqlAPI.execute(sqlQuery)

      if (result.success) {
        setQueryResult(result)
        message.success(`Query executed successfully! ${result.rows} rows returned`)
      } else {
        setError(result.error)
        message.error('Query execution failed')
      }
    } catch (err) {
      setError(err.message)
      message.error('Failed to execute query')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateSQL = async () => {
    if (!aiPrompt.trim()) {
      message.warning('Please enter a description of what data you want')
      return
    }

    try {
      setAiLoading(true)
      const result = await sqlAPI.generateQuery(aiPrompt)
      setGeneratedSQL(result.generated_sql)
      message.success('SQL query generated successfully!')
    } catch (err) {
      message.error(`Failed to generate SQL: ${err.message}`)
    } finally {
      setAiLoading(false)
    }
  }

  const handleUseGenerated = () => {
    if (generatedSQL) {
      setSqlQuery(generatedSQL)
      setGeneratedSQL(null)
      message.success('Generated query loaded into editor')
    }
  }

  const handleDownload = () => {
    if (!queryResult || !queryResult.data.length) {
      message.warning('No data to download')
      return
    }

    const headers = queryResult.columns.join(',')
    const rows = queryResult.data.map((row) =>
      queryResult.columns.map((col) => row[col]).join(',')
    )
    const csv = [headers, ...rows].join('\n')

    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `query_results_${dayjs().format('YYYYMMDD_HHmmss')}.csv`
    a.click()
    message.success('Downloaded successfully!')
  }

  // Prepare table columns from query result
  const tableColumns = queryResult?.columns.map((col) => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    render: (text) => {
      if (text === null || text === undefined) return <Text type="secondary">NULL</Text>
      return text.toString()
    },
  }))

  return (
    <div>
      <div className="page-header">
        <Title level={2}>⚡ SQL Query Executor</Title>
        <Paragraph>
          Execute custom SQL queries or use AI to generate them from natural language
        </Paragraph>
      </div>

      <Alert
        message="Read-only queries recommended"
        description="Use caution with UPDATE, DELETE, or INSERT statements."
        type="warning"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* AI Query Generator */}
      <Card
        title={
          <Space>
            <RobotOutlined style={{ color: '#1890ff' }} />
            <span>AI-Powered Query Generator</span>
          </Space>
        }
        style={{ marginBottom: 24 }}
      >
        <Paragraph type="secondary">
          Describe what data you want in plain English, and AI will generate the SQL query for you
        </Paragraph>

        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <TextArea
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            placeholder="Example: Get all staff who have committed code in the last 6 months"
            rows={3}
            style={{ fontSize: 14 }}
          />

          <Space>
            <Button
              type="primary"
              icon={<RobotOutlined />}
              onClick={handleGenerateSQL}
              loading={aiLoading}
              size="large"
            >
              Generate SQL
            </Button>
          </Space>

          {generatedSQL && (
            <div>
              <Divider />
              <Title level={5}>📝 Generated SQL Query</Title>
              <Card style={{ backgroundColor: '#f5f5f5' }}>
                <pre style={{ margin: 0, overflow: 'auto' }}>{generatedSQL}</pre>
              </Card>
              <Space style={{ marginTop: 16 }}>
                <Button type="primary" icon={<ThunderboltOutlined />} onClick={handleUseGenerated}>
                  Use This Query
                </Button>
                <Button onClick={() => setGeneratedSQL(null)}>Clear</Button>
              </Space>
            </div>
          )}
        </Space>
      </Card>

      {/* SQL Query Editor */}
      <Card title={<Space><CodeOutlined /> SQL Query Editor</Space>} style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Row gutter={16}>
            <Col xs={24} md={16}>
              <Text strong>Enter your SQL query:</Text>
            </Col>
            <Col xs={24} md={8}>
              <Select
                style={{ width: '100%' }}
                placeholder="Load Sample Query"
                onChange={(value) => setSqlQuery(sampleQueries[value])}
              >
                {Object.keys(sampleQueries).map((key) => (
                  <Select.Option key={key} value={key}>
                    {key}
                  </Select.Option>
                ))}
              </Select>
            </Col>
          </Row>

          <TextArea
            value={sqlQuery}
            onChange={(e) => setSqlQuery(e.target.value)}
            rows={10}
            style={{ fontFamily: 'monospace', fontSize: 13 }}
          />

          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleExecute}
              loading={loading}
              size="large"
            >
              Execute Query
            </Button>
            {queryResult && queryResult.data.length > 0 && (
              <Button icon={<DownloadOutlined />} onClick={handleDownload}>
                Download Results
              </Button>
            )}
          </Space>
        </Space>
      </Card>

      {/* Query Results */}
      {error && (
        <Alert
          message="Query Error"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {queryResult && queryResult.success && (
        <Card
          title={
            <Space>
              <span>Query Results</span>
              <Tag color="success">{queryResult.rows} rows</Tag>
              <Tag color="blue">{queryResult.columns.length} columns</Tag>
            </Space>
          }
        >
          <Table
            columns={tableColumns}
            dataSource={queryResult.data}
            rowKey={(record) => record.id || `row-${JSON.stringify(record)}`}
            scroll={{ x: 'max-content' }}
            pagination={{
              pageSize: 50,
              showSizeChanger: true,
              showTotal: (total) => `Total ${total} rows`,
            }}
          />
        </Card>
      )}

      {/* Database Schema */}
      <Collapse style={{ marginTop: 24 }}>
        <Panel header="📊 Database Schema Reference" key="1">
          <pre style={{ whiteSpace: 'pre-wrap' }}>{schemaInfo}</pre>
        </Panel>
      </Collapse>
    </div>
  )
}

export default SQLExecutor
