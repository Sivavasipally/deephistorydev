/**
 * File Type Categorization and Analysis Utilities
 * Categorizes file extensions into meaningful groups for analytics
 */

// File type categories
export const FILE_CATEGORIES = {
  CODE: 'code',
  CONFIG: 'config',
  DOCUMENTATION: 'documentation',
  FRONTEND: 'frontend',
  BACKEND: 'backend',
  DATABASE: 'database',
  TEST: 'test',
  BUILD: 'build',
  OTHER: 'other'
};

// File type mappings
export const FILE_TYPE_MAP = {
  // Backend Code
  java: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#b07219', label: 'Java' },
  py: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#3572A5', label: 'Python' },
  go: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#00ADD8', label: 'Go' },
  rb: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#701516', label: 'Ruby' },
  php: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#4F5D95', label: 'PHP' },
  cs: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.BACKEND, color: '#178600', label: 'C#' },

  // Frontend Code
  js: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#f1e05a', label: 'JavaScript' },
  jsx: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#f1e05a', label: 'React JSX' },
  ts: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#2b7489', label: 'TypeScript' },
  tsx: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#2b7489', label: 'React TSX' },
  vue: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#2c3e50', label: 'Vue' },
  html: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#e34c26', label: 'HTML' },
  css: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#563d7c', label: 'CSS' },
  scss: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#c6538c', label: 'SCSS' },
  sass: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#a53b70', label: 'Sass' },
  less: { category: FILE_CATEGORIES.CODE, subcategory: FILE_CATEGORIES.FRONTEND, color: '#1d365d', label: 'Less' },

  // Configuration Files
  yml: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#cb171e', label: 'YAML' },
  yaml: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#cb171e', label: 'YAML' },
  xml: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#0060ac', label: 'XML' },
  json: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#292929', label: 'JSON' },
  properties: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#2e7d32', label: 'Properties' },
  ini: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#d1dbe0', label: 'INI' },
  toml: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#9c4221', label: 'TOML' },
  env: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#ecd53f', label: 'Environment' },
  conf: { category: FILE_CATEGORIES.CONFIG, subcategory: FILE_CATEGORIES.CONFIG, color: '#5e5c6d', label: 'Config' },

  // Documentation
  md: { category: FILE_CATEGORIES.DOCUMENTATION, subcategory: FILE_CATEGORIES.DOCUMENTATION, color: '#083fa1', label: 'Markdown' },
  txt: { category: FILE_CATEGORIES.DOCUMENTATION, subcategory: FILE_CATEGORIES.DOCUMENTATION, color: '#000080', label: 'Text' },
  rst: { category: FILE_CATEGORIES.DOCUMENTATION, subcategory: FILE_CATEGORIES.DOCUMENTATION, color: '#141414', label: 'reStructuredText' },
  adoc: { category: FILE_CATEGORIES.DOCUMENTATION, subcategory: FILE_CATEGORIES.DOCUMENTATION, color: '#73a803', label: 'AsciiDoc' },

  // Database
  sql: { category: FILE_CATEGORIES.DATABASE, subcategory: FILE_CATEGORIES.DATABASE, color: '#e38c00', label: 'SQL' },

  // Test Files
  test: { category: FILE_CATEGORIES.TEST, subcategory: FILE_CATEGORIES.TEST, color: '#e34c26', label: 'Test' },
  spec: { category: FILE_CATEGORIES.TEST, subcategory: FILE_CATEGORIES.TEST, color: '#e34c26', label: 'Spec' },

  // Build/Deploy
  gradle: { category: FILE_CATEGORIES.BUILD, subcategory: FILE_CATEGORIES.BUILD, color: '#02303a', label: 'Gradle' },
  maven: { category: FILE_CATEGORIES.BUILD, subcategory: FILE_CATEGORIES.BUILD, color: '#c71a36', label: 'Maven' },
  dockerfile: { category: FILE_CATEGORIES.BUILD, subcategory: FILE_CATEGORIES.BUILD, color: '#384d54', label: 'Docker' },
  sh: { category: FILE_CATEGORIES.BUILD, subcategory: FILE_CATEGORIES.BUILD, color: '#89e051', label: 'Shell' },
  bat: { category: FILE_CATEGORIES.BUILD, subcategory: FILE_CATEGORIES.BUILD, color: '#c1f12e', label: 'Batch' },

  // Default for unknown types
  'no-ext': { category: FILE_CATEGORIES.OTHER, subcategory: FILE_CATEGORIES.OTHER, color: '#cccccc', label: 'No Extension' }
};

/**
 * Get category info for a file type
 */
export const getFileTypeInfo = (fileType) => {
  const normalized = fileType?.toLowerCase().trim();
  return FILE_TYPE_MAP[normalized] || {
    category: FILE_CATEGORIES.OTHER,
    subcategory: FILE_CATEGORIES.OTHER,
    color: '#95a5a6',
    label: fileType || 'Unknown'
  };
};

/**
 * Categorize file types from a comma-separated string
 */
export const categorizeFileTypes = (fileTypesString) => {
  if (!fileTypesString) return {};

  const types = fileTypesString.split(',').map(t => t.trim()).filter(t => t);
  const categories = {};

  types.forEach(type => {
    const info = getFileTypeInfo(type);
    const category = info.category;

    if (!categories[category]) {
      categories[category] = {
        types: [],
        count: 0
      };
    }

    categories[category].types.push(type);
    categories[category].count++;
  });

  return categories;
};

/**
 * Calculate percentage of code vs config vs docs
 */
export const calculateFileTypeDistribution = (commits) => {
  const distribution = {
    code: 0,
    config: 0,
    documentation: 0,
    test: 0,
    build: 0,
    other: 0,
    total: 0
  };

  commits.forEach(commit => {
    if (!commit.file_types) return;

    const types = commit.file_types.split(',').map(t => t.trim()).filter(t => t);

    types.forEach(type => {
      const info = getFileTypeInfo(type);
      distribution[info.category] = (distribution[info.category] || 0) + 1;
      distribution.total++;
    });
  });

  return distribution;
};

/**
 * Get top file types with counts
 */
export const getTopFileTypes = (commits, limit = 10) => {
  const typeCounts = {};

  commits.forEach(commit => {
    if (!commit.file_types) return;

    const types = commit.file_types.split(',').map(t => t.trim()).filter(t => t);

    types.forEach(type => {
      if (!typeCounts[type]) {
        const info = getFileTypeInfo(type);
        typeCounts[type] = {
          type,
          count: 0,
          commits: 0,
          chars_added: 0,
          chars_deleted: 0,
          ...info
        };
      }

      typeCounts[type].count++;
      typeCounts[type].commits++;
      typeCounts[type].chars_added += commit.chars_added || 0;
      typeCounts[type].chars_deleted += commit.chars_deleted || 0;
    });
  });

  return Object.values(typeCounts)
    .sort((a, b) => b.count - a.count)
    .slice(0, limit);
};

/**
 * Calculate code vs non-code ratio
 */
export const getCodeVsNonCodeRatio = (commits) => {
  let codeCommits = 0;
  let configCommits = 0;
  let docCommits = 0;
  let otherCommits = 0;

  commits.forEach(commit => {
    if (!commit.file_types) {
      otherCommits++;
      return;
    }

    const categories = categorizeFileTypes(commit.file_types);

    if (categories[FILE_CATEGORIES.CODE]) {
      codeCommits++;
    } else if (categories[FILE_CATEGORIES.CONFIG]) {
      configCommits++;
    } else if (categories[FILE_CATEGORIES.DOCUMENTATION]) {
      docCommits++;
    } else {
      otherCommits++;
    }
  });

  const total = codeCommits + configCommits + docCommits + otherCommits;

  return {
    code: { count: codeCommits, percentage: total > 0 ? (codeCommits / total * 100).toFixed(1) : 0 },
    config: { count: configCommits, percentage: total > 0 ? (configCommits / total * 100).toFixed(1) : 0 },
    documentation: { count: docCommits, percentage: total > 0 ? (docCommits / total * 100).toFixed(1) : 0 },
    other: { count: otherCommits, percentage: total > 0 ? (otherCommits / total * 100).toFixed(1) : 0 },
    total
  };
};

/**
 * Get language expertise based on commits
 */
export const getLanguageExpertise = (commits) => {
  const languages = {};

  commits.forEach(commit => {
    if (!commit.file_types) return;

    const types = commit.file_types.split(',').map(t => t.trim()).filter(t => t);

    types.forEach(type => {
      const info = getFileTypeInfo(type);

      if (info.category === FILE_CATEGORIES.CODE) {
        if (!languages[type]) {
          languages[type] = {
            type,
            label: info.label,
            color: info.color,
            subcategory: info.subcategory,
            commits: 0,
            chars_added: 0,
            chars_deleted: 0,
            lines_added: 0,
            lines_deleted: 0
          };
        }

        languages[type].commits++;
        languages[type].chars_added += commit.chars_added || 0;
        languages[type].chars_deleted += commit.chars_deleted || 0;
        languages[type].lines_added += commit.lines_added || 0;
        languages[type].lines_deleted += commit.lines_deleted || 0;
      }
    });
  });

  return Object.values(languages).sort((a, b) => b.commits - a.commits);
};

/**
 * Format file types for display
 */
export const formatFileTypes = (fileTypesString) => {
  if (!fileTypesString) return [];

  return fileTypesString.split(',')
    .map(t => t.trim())
    .filter(t => t)
    .map(type => ({
      type,
      ...getFileTypeInfo(type)
    }));
};

/**
 * Get category color
 */
export const getCategoryColor = (category) => {
  const colors = {
    [FILE_CATEGORIES.CODE]: '#52c41a',
    [FILE_CATEGORIES.CONFIG]: '#faad14',
    [FILE_CATEGORIES.DOCUMENTATION]: '#1890ff',
    [FILE_CATEGORIES.FRONTEND]: '#722ed1',
    [FILE_CATEGORIES.BACKEND]: '#13c2c2',
    [FILE_CATEGORIES.DATABASE]: '#eb2f96',
    [FILE_CATEGORIES.TEST]: '#fa541c',
    [FILE_CATEGORIES.BUILD]: '#2f54eb',
    [FILE_CATEGORIES.OTHER]: '#8c8c8c'
  };

  return colors[category] || '#95a5a6';
};

export default {
  FILE_CATEGORIES,
  FILE_TYPE_MAP,
  getFileTypeInfo,
  categorizeFileTypes,
  calculateFileTypeDistribution,
  getTopFileTypes,
  getCodeVsNonCodeRatio,
  getLanguageExpertise,
  formatFileTypes,
  getCategoryColor
};
