import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Spin,
  Alert,
  Typography,
  Select,
  Space,
  Tag,
  Row,
  Col,
  Statistic,
  message,
  Avatar,
} from 'antd'
import {
  UserOutlined,
  CheckCircleOutlined,
  TeamOutlined,
  TrophyOutlined,
  MailOutlined,
  DatabaseOutlined,
} from '@ant-design/icons'
import { Bar } from '@ant-design/charts'
import { pullRequestsAPI } from '../services/api'

const { Title, Text } = Typography

const TopApprovers = () => {
  const [approvers, setApprovers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [limit, setLimit] = useState(10)

  useEffect(() => {
    fetchTopApprovers()
  }, [limit])

  const fetchTopApprovers = async () => {
    try {
      setLoading(true)
      const data = await pullRequestsAPI.getTopApprovers({ limit })
      setApprovers(data)
      setError(null)
    } catch (err) {
      setError(err.message)
      message.error('Failed to fetch top approvers')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: 'Rank',
      key: 'rank',
      width: 80,
      render: (_, __, index) => {
        const colors = ['gold', 'silver', 'bronze', 'blue', 'cyan', 'purple', 'magenta', 'orange', 'lime', 'green']
        return (
          <Tag color={colors[index] || 'blue'} style={{ fontSize: 14, fontWeight: 'bold' }}>
            #{index + 1}
          </Tag>
        )
      },
    },
    {
      title: 'Approver',
      dataIndex: 'approver_name',
      key: 'approver_name',
      width: 200,
      render: (name) => (
        <Space>
          <Avatar
            style={{ backgroundColor: '#1890ff' }}
            icon={<UserOutlined />}
            size="small"
          />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 250,
      render: (email) => (
        <Space>
          <MailOutlined style={{ color: '#1890ff' }} />
          <Text type="secondary">{email}</Text>
        </Space>
      ),
    },
    {
      title: 'Total Approvals',
      dataIndex: 'total_approvals',
      key: 'total_approvals',
      width: 150,
      align: 'center',
      sorter: (a, b) => a.total_approvals - b.total_approvals,
      defaultSortOrder: 'descend',
      render: (count) => (
        <Tag
          color="success"
          icon={<CheckCircleOutlined />}
          style={{ fontSize: 16, fontWeight: 'bold', padding: '4px 12px' }}
        >
          {count}
        </Tag>
      ),
    },
    {
      title: 'Repositories',
      dataIndex: 'repositories',
      key: 'repositories',
      width: 130,
      align: 'center',
      render: (count) => (
        <Tag color="purple" icon={<DatabaseOutlined />}>
          {count} repos
        </Tag>
      ),
    },
    {
      title: 'Avg Approvals/Repo',
      key: 'avg_approvals',
      width: 160,
      align: 'center',
      render: (_, record) => {
        const avg = record.repositories > 0 ? (record.total_approvals / record.repositories).toFixed(1) : 0
        return (
          <Tag color="blue">
            {avg} per repo
          </Tag>
        )
      },
    },
  ]

  // Calculate summary stats
  const totalApprovals = approvers.reduce((sum, a) => sum + a.total_approvals, 0)
  const avgApprovalsPerPerson = approvers.length > 0 ? Math.round(totalApprovals / approvers.length) : 0

  // Prepare chart data
  const chartData = approvers.map((approver) => ({
    approver: approver.approver_name,
    approvals: approver.total_approvals,
  }))

  if (loading && !approvers.length) {
    return (
      <div style={{ padding: '50px', textAlign: 'center' }}>
        <Spin size="large" tip="Loading top approvers...">
          <div style={{ minHeight: '400px' }} />
        </Spin>
      </div>
    )
  }

  if (error && !approvers.length) {
    return <Alert message="Error" description={error} type="error" showIcon />
  }

  return (
    <div>
      <div className="page-header">
        <Title level={2}>
          <TeamOutlined style={{ color: '#52c41a' }} /> Top PR Approvers
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Team members who review and approve the most pull requests
        </Text>
      </div>

      {/* Controls */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>Show Top:</Text>
          <Select value={limit} onChange={setLimit} style={{ width: 120 }}>
            <Select.Option value={5}>Top 5</Select.Option>
            <Select.Option value={10}>Top 10</Select.Option>
            <Select.Option value={20}>Top 20</Select.Option>
            <Select.Option value={50}>Top 50</Select.Option>
            <Select.Option value={100}>Top 100</Select.Option>
          </Select>
        </Space>
      </Card>

      {/* Summary Stats */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Approvers"
              value={approvers.length}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Approvals"
              value={totalApprovals}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Approvals/Person"
              value={avgApprovalsPerPerson}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Most Active Approver"
              value={approvers.length > 0 ? approvers[0].total_approvals : 0}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
              suffix="approvals"
            />
          </Card>
        </Col>
      </Row>

      {/* Chart */}
      <Card title="📊 Approval Leaderboard" style={{ marginBottom: 24 }}>
        <Bar
          data={chartData}
          xField="approvals"
          yField="approver"
          legend={false}
          barStyle={{
            radius: [0, 8, 8, 0],
          }}
          label={{
            position: 'right',
            style: {
              fill: '#000',
              opacity: 0.6,
            },
          }}
          color={({ approver }) => {
            const index = chartData.findIndex(d => d.approver === approver)
            const colors = ['#faad14', '#c0c0c0', '#cd7f32', '#1890ff', '#52c41a', '#722ed1']
            return colors[index] || '#1890ff'
          }}
          meta={{
            approvals: { alias: 'Total Approvals' },
            approver: { alias: 'Approver Name' },
          }}
        />
      </Card>

      {/* Leaderboard Info */}
      {approvers.length > 0 && (
        <Card
          style={{ marginBottom: 24, backgroundColor: '#fff7e6', borderColor: '#ffd666' }}
        >
          <Space direction="vertical" size="small">
            <Space>
              <TrophyOutlined style={{ fontSize: 24, color: '#faad14' }} />
              <Title level={4} style={{ margin: 0 }}>
                Top Reviewer: {approvers[0].approver_name}
              </Title>
            </Space>
            <Text>
              <CheckCircleOutlined style={{ color: '#52c41a' }} /> {approvers[0].total_approvals} total approvals across {approvers[0].repositories} repositories
            </Text>
          </Space>
        </Card>
      )}

      {/* Detailed Table */}
      <Card title="👥 Complete Approver Rankings">
        <Table
          columns={columns}
          dataSource={approvers}
          rowKey="email"
          loading={loading}
          scroll={{ x: 1100 }}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Total ${total} approvers`,
          }}
        />
      </Card>

      {/* Insights */}
      <Card title="💡 Insights" style={{ marginTop: 24 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text strong>Code Review Activity:</Text>
            <br />
            <Text type="secondary">
              The top {Math.min(3, approvers.length)} approvers account for{' '}
              {approvers.length >= 3
                ? Math.round(
                    (approvers.slice(0, 3).reduce((sum, a) => sum + a.total_approvals, 0) /
                      totalApprovals) *
                      100
                  )
                : 100}
              % of all pull request approvals.
            </Text>
          </div>
          <div>
            <Text strong>Team Collaboration:</Text>
            <br />
            <Text type="secondary">
              {approvers.length} team members are actively participating in code reviews, fostering a culture of quality and knowledge sharing.
            </Text>
          </div>
        </Space>
      </Card>
    </div>
  )
}

export default TopApprovers
