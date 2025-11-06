import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const TopCommits = () => {
  return (
    <div>
      <Title level={2}>🏆 Top Commits</Title>
      <Card>Top commits by lines changed</Card>
    </div>
  )
}

export default TopCommits
