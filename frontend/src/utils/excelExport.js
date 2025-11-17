/**
 * Excel Export Utility
 * Provides functions to export data to Excel format using xlsx library
 */

import * as XLSX from 'xlsx'

/**
 * Export data to Excel file
 * @param {Array} data - Array of objects to export
 * @param {string} filename - Name of the file (without extension)
 * @param {string} sheetName - Name of the sheet (default: 'Sheet1')
 */
export const exportToExcel = (data, filename, sheetName = 'Sheet1') => {
  if (!data || data.length === 0) {
    console.warn('No data to export')
    return
  }

  // Create a new workbook
  const workbook = XLSX.utils.book_new()

  // Convert data to worksheet
  const worksheet = XLSX.utils.json_to_sheet(data)

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

  // Generate Excel file and trigger download
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

/**
 * Export multiple sheets to a single Excel file
 * @param {Array} sheets - Array of {name, data} objects
 * @param {string} filename - Name of the file (without extension)
 */
export const exportMultipleSheetsToExcel = (sheets, filename) => {
  if (!sheets || sheets.length === 0) {
    console.warn('No sheets to export')
    return
  }

  // Create a new workbook
  const workbook = XLSX.utils.book_new()

  // Add each sheet
  sheets.forEach(({ name, data }) => {
    if (data && data.length > 0) {
      const worksheet = XLSX.utils.json_to_sheet(data)
      XLSX.utils.book_append_sheet(workbook, worksheet, name)
    }
  })

  // Generate Excel file and trigger download
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

/**
 * Export data with custom column widths
 * @param {Array} data - Array of objects to export
 * @param {string} filename - Name of the file (without extension)
 * @param {Object} options - Additional options
 */
export const exportToExcelWithFormatting = (data, filename, options = {}) => {
  if (!data || data.length === 0) {
    console.warn('No data to export')
    return
  }

  const {
    sheetName = 'Sheet1',
    columnWidths = null, // Array of widths or null for auto
    headerStyle = true
  } = options

  // Create a new workbook
  const workbook = XLSX.utils.book_new()

  // Convert data to worksheet
  const worksheet = XLSX.utils.json_to_sheet(data)

  // Set column widths if provided
  if (columnWidths) {
    worksheet['!cols'] = columnWidths.map(width => ({ wch: width }))
  } else {
    // Auto-calculate column widths
    const cols = Object.keys(data[0]).map(key => {
      const maxLength = Math.max(
        key.length,
        ...data.map(row => String(row[key] || '').length)
      )
      return { wch: Math.min(maxLength + 2, 50) } // Max width of 50
    })
    worksheet['!cols'] = cols
  }

  // Add worksheet to workbook
  XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

  // Generate Excel file and trigger download
  XLSX.writeFile(workbook, `${filename}.xlsx`)
}

/**
 * Prepare staff productivity data for export
 */
export const prepareStaffProductivityExport = (productivityData, fileTypeStats, characterMetrics) => {
  const sheets = []

  // Summary sheet
  if (productivityData) {
    const summary = {
      'Staff Name': productivityData.staff.name,
      'Bank ID': productivityData.staff.bank_id,
      'Rank': productivityData.staff.rank,
      'Location': productivityData.staff.location,
      'Total Commits': productivityData.timeseries.commits.reduce((sum, r) => sum + r.commits, 0),
      'Total Lines Added': productivityData.timeseries.commits.reduce((sum, r) => sum + r.lines_added, 0),
      'Total Lines Deleted': productivityData.timeseries.commits.reduce((sum, r) => sum + r.lines_deleted, 0),
      'Total PRs': productivityData.timeseries.prs.reduce((sum, r) => sum + r.prs_opened, 0),
      'Unique Repos': productivityData.repository_breakdown.length
    }

    if (characterMetrics) {
      summary['Characters Added'] = characterMetrics.total_chars_added
      summary['Characters Deleted'] = characterMetrics.total_chars_deleted
      summary['Code Churn'] = characterMetrics.total_churn
      summary['Avg Chars/Commit'] = characterMetrics.avg_chars_per_commit
    }

    sheets.push({ name: 'Summary', data: [summary] })
  }

  // Commits timeseries
  if (productivityData?.timeseries?.commits) {
    sheets.push({
      name: 'Commits Timeseries',
      data: productivityData.timeseries.commits
    })
  }

  // File type statistics
  if (fileTypeStats && fileTypeStats.length > 0) {
    sheets.push({
      name: 'File Types',
      data: fileTypeStats.map(ft => ({
        'File Type': ft.file_type,
        'Commits': ft.commits,
        'Chars Added': ft.chars_added,
        'Chars Deleted': ft.chars_deleted,
        'Total Churn': ft.total_churn,
        'Lines Added': ft.lines_added,
        'Lines Deleted': ft.lines_deleted
      }))
    })
  }

  // Repository breakdown
  if (productivityData?.repository_breakdown) {
    sheets.push({
      name: 'Repositories',
      data: productivityData.repository_breakdown
    })
  }

  return sheets
}

/**
 * Prepare team comparison data for export
 */
export const prepareTeamComparisonExport = (teamData, teamCharacterMetrics) => {
  const sheets = []

  // Team metrics
  if (teamData && teamData.length > 0) {
    sheets.push({
      name: 'Team Metrics',
      data: teamData.map(member => ({
        'Name': member.name,
        'Rank': member.rank,
        'Location': member.location,
        'Total Commits': member.totalCommits,
        'Lines Added': member.totalLinesAdded,
        'Lines Deleted': member.totalLinesDeleted,
        'Total PRs': member.totalPRs,
        'Files Changed': member.totalFilesChanged,
        'Repos Touched': member.uniqueRepos,
        'Avg Commits/Period': member.avgCommitsPerPeriod.toFixed(2),
        'Code Churn Ratio': member.codeChurnRatio.toFixed(2)
      }))
    })
  }

  // Character metrics
  if (teamCharacterMetrics && teamCharacterMetrics.length > 0) {
    sheets.push({
      name: 'Character Metrics',
      data: teamCharacterMetrics.map(member => ({
        'Developer': member.name,
        'Chars Added': member.charMetrics.total_chars_added,
        'Chars Deleted': member.charMetrics.total_chars_deleted,
        'Total Churn': member.charMetrics.total_churn,
        'Avg Chars/Commit': member.charMetrics.avg_chars_per_commit.toFixed(0),
        'Top File Type': member.fileTypes?.[0]?.file_type || 'N/A'
      }))
    })
  }

  // File type distribution
  if (teamCharacterMetrics && teamCharacterMetrics.length > 0) {
    const distributionData = []
    teamCharacterMetrics.forEach(member => {
      if (member.distribution) {
        member.distribution.forEach(dist => {
          distributionData.push({
            'Developer': member.name,
            'Category': dist.category,
            'Commits': dist.commits,
            'Percentage': dist.percentage,
            'Chars Added': dist.chars_added,
            'Chars Deleted': dist.chars_deleted
          })
        })
      }
    })

    if (distributionData.length > 0) {
      sheets.push({ name: 'File Type Distribution', data: distributionData })
    }
  }

  return sheets
}

/**
 * Prepare commits view data for export
 */
export const prepareCommitsExport = (commits) => {
  if (!commits || commits.length === 0) {
    return []
  }

  return commits.map(commit => ({
    'Hash': commit.commit_hash,
    'Author': commit.author_name,
    'Date': commit.commit_date,
    'Message': commit.message,
    'Lines Added': commit.lines_added,
    'Lines Deleted': commit.lines_deleted,
    'Chars Added': commit.chars_added || 0,
    'Chars Deleted': commit.chars_deleted || 0,
    'Files Changed': commit.files_changed,
    'File Types': commit.file_types || '',
    'Repository': commit.repository
  }))
}

/**
 * Prepare Dashboard360 data for export
 */
export const prepareDashboard360Export = (orgData, characterMetrics, fileTypeDistribution) => {
  const sheets = []

  // Organization summary
  if (orgData?.summary) {
    const summary = {
      'Total Commits': orgData.summary.total_commits,
      'Total PRs': orgData.summary.total_prs,
      'Total Contributors': orgData.summary.total_contributors,
      'Total Repositories': orgData.summary.total_repositories,
      'Median Cycle Time (hrs)': orgData.summary.median_cycle_time_hours,
      'P90 Cycle Time (hrs)': orgData.summary.p90_cycle_time_hours,
      'Overall Merge Rate (%)': orgData.summary.overall_merge_rate
    }

    if (characterMetrics) {
      summary['Characters Added'] = characterMetrics.total_chars_added
      summary['Characters Deleted'] = characterMetrics.total_chars_deleted
      summary['Code Churn'] = characterMetrics.total_churn
      summary['Avg Chars/Commit'] = characterMetrics.avg_chars_per_commit
    }

    sheets.push({ name: 'Organization Summary', data: [summary] })
  }

  // Contributors
  if (orgData?.contributors) {
    sheets.push({
      name: 'Contributors',
      data: orgData.contributors
    })
  }

  // File type distribution
  if (fileTypeDistribution && fileTypeDistribution.length > 0) {
    sheets.push({
      name: 'File Type Distribution',
      data: fileTypeDistribution.map(dist => ({
        'Category': dist.category,
        'Commits': dist.commits,
        'Percentage': dist.percentage,
        'Chars Added': dist.chars_added,
        'Chars Deleted': dist.chars_deleted
      }))
    })
  }

  return sheets
}
