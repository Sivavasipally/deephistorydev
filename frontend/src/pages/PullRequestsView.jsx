import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const PullRequestsView = () => {
  return (
    <div>
      <Title level={2}>🔀 Pull Requests View</Title>
      <Card>Pull requests content - similar to CommitsView</Card>
    </div>
  )
}

export default PullRequestsView
