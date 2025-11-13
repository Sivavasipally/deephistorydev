# Enhanced Analytics Implementation Plan
## Character Metrics & File Type Analysis

### Overview
This document outlines the implementation plan for integrating character-level metrics and file type analysis across all dashboard pages.

---

## ✅ Completed

### 1. Utility Module Created
**File**: `frontend/src/utils/fileTypeUtils.js`

**Features**:
- File type categorization (code, config, documentation, test, build, other)
- Language/technology color coding
- Code vs config vs docs ratio calculations
- Language expertise analysis
- Top file types aggregation

**Key Functions**:
```javascript
- getFileTypeInfo(fileType) → Returns category, color, label
- categorizeFileTypes(fileTypesString) → Groups by category
- calculateFileTypeDistribution(commits) → Percentage breakdown
- getTopFileTypes(commits, limit) → Most common file types
- getCodeVsNonCodeRatio(commits) → Code/config/docs split
- getLanguageExpertise(commits) → Developer language proficiency
```

### 2. Backend Analytics API Created
**File**: `backend/routers/analytics.py`

**Endpoints**:
```
GET /api/analytics/file-types/top
  - Returns top N file types by commit count
  - Includes chars_added, chars_deleted, total_churn
  - Filters: date range, repository, staff_id

GET /api/analytics/file-types/distribution
  - Returns code vs config vs docs breakdown
  - Percentage of each category
  - Character metrics per category

GET /api/analytics/characters/metrics
  - Total chars added/deleted
  - Average chars per commit
  - Commits with character data
```

**Registered** in `backend/main.py` at `/api/analytics`

---

## 📋 Implementation Required

### Priority 1: Staff Productivity Page Enhancements

**File**: `frontend/src/pages/StaffProductivity.jsx`

#### Changes Needed:

1. **Add Import**:
```javascript
import {
  getTopFileTypes,
  getCodeVsNonCodeRatio,
  getLanguageExpertise,
  getCategoryColor,
  formatFileTypes
} from '../utils/fileTypeUtils'
```

2. **Add New State Variables**:
```javascript
const [fileTypeStats, setFileTypeStats] = useState(null)
const [characterMetrics, setCharacterMetrics] = useState(null)
const [languageExpertise, setLanguageExpertise] = useState([])
```

3. **Fetch Analytics Data** (in useEffect):
```javascript
// Fetch file type analytics
const fetchFileTypeAnalytics = async () => {
  try {
    const response = await fetch(
      `/api/analytics/file-types/top?staff_id=${selectedStaff}&limit=10`
    )
    const data = await response.json()
    setFileTypeStats(data)
  } catch (error) {
    console.error('Error fetching file type stats:', error)
  }
}

// Fetch character metrics
const fetchCharacterMetrics = async () => {
  try {
    const response = await fetch(
      `/api/analytics/characters/metrics?staff_id=${selectedStaff}`
    )
    const data = await response.json()
    setCharacterMetrics(data)
  } catch (error) {
    console.error('Error fetching character metrics:', error)
  }
}
```

4. **Add Character Metrics to Summary Stats**:
```javascript
<Col xs={24} sm={12} md={8} lg={4}>
  <Card>
    <Statistic
      title="Characters Added"
      value={characterMetrics?.total_chars_added || 0}
      valueStyle={{ color: '#52c41a', fontSize: '18px' }}
      prefix={<CodeOutlined />}
      suffix={
        <Tooltip title="Total characters added across all commits">
          <QuestionCircleOutlined style={{ fontSize: 12 }} />
        </Tooltip>
      }
    />
  </Card>
</Col>

<Col xs={24} sm={12} md={8} lg={4}>
  <Card>
    <Statistic
      title="Avg Chars/Commit"
      value={characterMetrics?.avg_chars_per_commit || 0}
      valueStyle={{ color: '#1890ff', fontSize: '18px' }}
      prefix={<FileTextOutlined />}
      precision={0}
    />
  </Card>
</Col>
```

5. **Add New Tab for File Type Analysis**:
```javascript
<Tabs.TabPane tab="📂 File Types & Languages" key="file-types">
  <Row gutter={[16, 16]}>
    {/* Code vs Config vs Docs */}
    <Col span={24}>
      <Card title="📊 Code vs Configuration vs Documentation">
        <Column
          data={codeVsNonCodeData}
          xField="category"
          yField="percentage"
          label={{
            position: 'top',
            formatter: (datum) => `${datum.percentage}%`
          }}
          color={({ category }) => getCategoryColor(category)}
        />
      </Card>
    </Col>

    {/* Top Programming Languages */}
    <Col span={12}>
      <Card title="💻 Top Programming Languages">
        <Column
          data={languageExpertise}
          xField="label"
          yField="commits"
          seriesField="label"
          color={({ label, color }) => color}
          label={{ position: 'top' }}
        />
      </Card>
    </Col>

    {/* File Type Distribution */}
    <Col span={12}>
      <Card title="📁 File Types Modified">
        <Pie
          data={fileTypeStats?.map(ft => ({
            type: ft.file_type,
            value: ft.commits
          })) || []}
          angleField="value"
          colorField="type"
          radius={0.8}
          label={{
            type: 'outer',
            content: '{name} ({percentage})'
          }}
        />
      </Card>
    </Col>

    {/* Character Churn by File Type */}
    <Col span={24}>
      <Card title="📝 Character Changes by File Type">
        <Column
          data={fileTypeStats || []}
          isGroup
          xField="file_type"
          yField="value"
          seriesField="type"
          data={fileTypeStats?.flatMap(ft => [
            { file_type: ft.file_type, type: 'Added', value: ft.chars_added },
            { file_type: ft.file_type, type: 'Deleted', value: ft.chars_deleted }
          ]) || []}
          color={['#52c41a', '#ff4d4f']}
        />
      </Card>
    </Col>
  </Row>
</Tabs.TabPane>
```

---

### Priority 2: Team Comparison Page Enhancements

**File**: `frontend/src/pages/TeamComparison.jsx`

#### Changes Needed:

1. **Add File Type Distribution Chart**:
```javascript
// After existing charts, add:
<Card title="📂 File Type Distribution by Developer">
  <Column
    data={prepareFileTypeData(timeSeriesData)}
    isStack
    xField="name"
    yField="commits"
    seriesField="category"
    color={({ category }) => getCategoryColor(category)}
    label={{
      position: 'middle',
      layout: [
        { type: 'interval-adjust-position' },
        { type: 'interval-hide-overlap' },
        { type: 'adjust-color' }
      ]
    }}
  />
</Card>
```

2. **Add Character Metrics Comparison**:
```javascript
<Card title="📝 Character Changes Comparison">
  <Column
    data={staffCharacterMetrics}
    isGroup
    xField="name"
    yField="chars"
    seriesField="type"
    color={['#52c41a', '#ff4d4f']}
    dodgePadding={4}
    label={{ position: 'top' }}
  />
</Card>
```

3. **Technology Stack Radar Chart**:
```javascript
<Card title="🎯 Technology Stack Proficiency">
  <Radar
    data={technologyStackData}
    xField="technology"
    yField="score"
    seriesField="developer"
    area={{}}
    point={{ size: 2 }}
  />
</Card>
```

---

### Priority 3: Commits View Enhancements

**File**: `frontend/src/pages/CommitsView.jsx`

#### Changes Needed:

1. **Add File Type Filter**:
```javascript
<Select
  placeholder="Filter by file type"
  allowClear
  style={{ width: 200 }}
  onChange={(value) => setFileTypeFilter(value)}
>
  <Select.Option value="code">Code Files</Select.Option>
  <Select.Option value="config">Configuration</Select.Option>
  <Select.Option value="docs">Documentation</Select.Option>
  <Select.Option value="java">Java</Select.Option>
  <Select.Option value="js">JavaScript</Select.Option>
  <Select.Option value="jsx">React JSX</Select.Option>
  <Select.Option value="tsx">TypeScript TSX</Select.Option>
  <Select.Option value="yml">YAML</Select.Option>
  <Select.Option value="xml">XML</Select.Option>
</Select>
```

2. **Add File Type Column to Table**:
```javascript
{
  title: 'File Types',
  dataIndex: 'file_types',
  key: 'file_types',
  width: 150,
  render: (fileTypes) => (
    <Space wrap>
      {formatFileTypes(fileTypes).slice(0, 3).map((ft, idx) => (
        <Tag key={idx} color={ft.color}>
          {ft.label}
        </Tag>
      ))}
      {formatFileTypes(fileTypes).length > 3 && (
        <Tag>+{formatFileTypes(fileTypes).length - 3}</Tag>
      )}
    </Space>
  )
}
```

3. **Add Character Metrics Column**:
```javascript
{
  title: 'Characters',
  dataIndex: 'chars',
  key: 'chars',
  width: 120,
  render: (_, record) => (
    <Tooltip title={`Added: ${record.chars_added} | Deleted: ${record.chars_deleted}`}>
      <Text type="success">+{record.chars_added || 0}</Text>
      {' / '}
      <Text type="danger">-{record.chars_deleted || 0}</Text>
    </Tooltip>
  ),
  sorter: (a, b) =>
    (a.chars_added + a.chars_deleted) - (b.chars_added + b.chars_deleted)
}
```

---

### Priority 4: Overview/Dashboard360 Enhancements

**File**: `frontend/src/pages/Dashboard360.jsx`

#### Changes Needed:

1. **Add Technology Stack Overview**:
```javascript
<Card title="💻 Technology Stack Usage">
  <Row gutter={16}>
    <Col span={12}>
      <Statistic
        title="Most Used Language"
        value={topLanguage?.label || 'N/A'}
        suffix={`(${topLanguage?.commits || 0} commits)`}
      />
    </Col>
    <Col span={12}>
      <Statistic
        title="Code vs Config Ratio"
        value={codeRatio}
        suffix="%"
        prefix="📊"
      />
    </Col>
  </Row>
</Card>
```

2. **File Type Distribution Pie Chart**:
```javascript
<Card title="📂 Commit Distribution by Category">
  <Pie
    data={categoryDistribution}
    angleField="percentage"
    colorField="category"
    radius={0.9}
    innerRadius={0.6}
    label={{
      type: 'spider',
      labelHeight: 28,
      content: '{name}\n{percentage}%'
    }}
    interactions={[
      { type: 'element-selected' },
      { type: 'element-active' }
    ]}
  />
</Card>
```

3. **Character Metrics Summary**:
```javascript
<Row gutter={16}>
  <Col span={8}>
    <Card>
      <Statistic
        title="Total Characters Added"
        value={totalCharsAdded}
        valueStyle={{ color: '#3f8600' }}
        prefix={<CodeOutlined />}
      />
    </Card>
  </Col>
  <Col span={8}>
    <Card>
      <Statistic
        title="Total Characters Deleted"
        value={totalCharsDeleted}
        valueStyle={{ color: '#cf1322' }}
        prefix={<CodeOutlined />}
      />
    </Card>
  </Col>
  <Col span={8}>
    <Card>
      <Statistic
        title="Total Code Churn"
        value={totalCharsAdded + totalCharsDeleted}
        prefix={<BarChartOutlined />}
      />
    </Card>
  </Col>
</Row>
```

---

## Data Processing Examples

### Calculate Code vs Non-Code Ratio
```javascript
const calculateCodeRatio = (commits) => {
  const { code, config, documentation, other, total } = getCodeVsNonCodeRatio(commits)

  return [
    { category: 'Code', commits: code.count, percentage: parseFloat(code.percentage) },
    { category: 'Configuration', commits: config.count, percentage: parseFloat(config.percentage) },
    { category: 'Documentation', commits: documentation.count, percentage: parseFloat(documentation.percentage) },
    { category: 'Other', commits: other.count, percentage: parseFloat(other.percentage) }
  ]
}
```

### Prepare Technology Stack Data
```javascript
const prepareTechStackData = (commits) => {
  const languages = getLanguageExpertise(commits)

  return languages.map(lang => ({
    label: lang.label,
    color: lang.color,
    commits: lang.commits,
    chars_added: lang.chars_added,
    chars_deleted: lang.chars_deleted,
    total_churn: lang.chars_added + lang.chars_deleted
  }))
}
```

### Group by File Type Category
```javascript
const groupByCategory = (commits) => {
  const categories = {
    code: [],
    config: [],
    documentation: [],
    other: []
  }

  commits.forEach(commit => {
    const cats = categorizeFileTypes(commit.file_types)
    Object.keys(cats).forEach(cat => {
      if (categories[cat]) {
        categories[cat].push(commit)
      }
    })
  })

  return categories
}
```

---

## Chart Configuration Best Practices

### Color Schemes

**File Type Categories**:
- Code: `#52c41a` (green)
- Configuration: `#faad14` (orange)
- Documentation: `#1890ff` (blue)
- Test: `#fa541c` (red-orange)
- Build: `#2f54eb` (indigo)
- Other: `#8c8c8c` (gray)

**Character Metrics**:
- Added: `#52c41a` (green)
- Deleted: `#ff4d4f` (red)
- Churn: `#1890ff` (blue)

### Chart Types Recommendations

1. **File Type Distribution**: Pie or Donut Chart
2. **Code vs Config**: Stacked Column Chart
3. **Language Expertise**: Radar or Column Chart
4. **Character Trends**: Line Chart with dual axis
5. **Developer Comparison**: Grouped Column Chart
6. **Technology Stack**: Tree Map or Bubble Chart

---

## API Integration Pattern

```javascript
const fetchEnhancedAnalytics = async (staffId, filters = {}) => {
  try {
    const [fileTypes, distribution, characterMetrics] = await Promise.all([
      fetch(`/api/analytics/file-types/top?staff_id=${staffId}&${new URLSearchParams(filters)}`),
      fetch(`/api/analytics/file-types/distribution?staff_id=${staffId}&${new URLSearchParams(filters)}`),
      fetch(`/api/analytics/characters/metrics?staff_id=${staffId}&${new URLSearchParams(filters)}`)
    ])

    return {
      fileTypes: await fileTypes.json(),
      distribution: await distribution.json(),
      characterMetrics: await characterMetrics.json()
    }
  } catch (error) {
    console.error('Error fetching analytics:', error)
    return null
  }
}
```

---

## Testing Checklist

- [ ] File type categorization accuracy
- [ ] Character metrics calculations
- [ ] Code vs config vs docs percentages
- [ ] Chart rendering performance
- [ ] Filter interactions
- [ ] Data export functionality
- [ ] Mobile responsiveness
- [ ] Cross-browser compatibility
- [ ] API error handling
- [ ] Loading states

---

## Performance Considerations

1. **Caching**: Cache file type analysis results
2. **Lazy Loading**: Load charts on tab activation
3. **Debouncing**: Debounce filter changes
4. **Pagination**: Paginate large file type lists
5. **Memoization**: Memoize expensive calculations

---

## Next Steps

1. ✅ Create utility module for file type analysis
2. ✅ Create backend analytics API endpoints
3. ⏳ Implement Staff Productivity enhancements
4. ⏳ Update Team Comparison page
5. ⏳ Enhance Commits View with filters
6. ⏳ Update Overview/Dashboard360
7. ⏳ Test all changes
8. ⏳ Update documentation
9. ⏳ Create user guide for new features

---

## Documentation Updates Required

- README.md: Add file type analysis features
- API documentation: Document new endpoints
- User guide: Explain new charts and metrics
- Developer guide: File type categorization logic

---

**Status**: Backend Complete | Frontend In Progress
**Priority**: High
**Estimated Effort**: 8-12 hours for full implementation
