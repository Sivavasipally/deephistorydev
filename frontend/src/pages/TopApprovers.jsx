import React from 'react'
import { Card, Typography } from 'antd'

const { Title } = Typography

const TopApprovers = () => {
  return (
    <div>
      <Title level={2}>👥 Top PR Approvers</Title>
      <Card>Top PR approvers content</Card>
    </div>
  )
}

export default TopApprovers
