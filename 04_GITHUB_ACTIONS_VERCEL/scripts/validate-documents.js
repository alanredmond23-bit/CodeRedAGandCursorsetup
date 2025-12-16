#!/usr/bin/env node

/**
 * Document Validator
 * Validates discovery documents before processing
 */

const fs = require('fs').promises;
const path = require('path');

const VALIDATION_RULES = {
  maxFileSize: 100 * 1024 * 1024, // 100MB
  minFileSize: 1, // 1 byte
  allowedExtensions: ['.pdf', '.docx', '.doc', '.txt'],
  forbiddenPatterns: [
    /password/i,
    /credit.?card/i,
    /ssn/i,
    /social.?security/i
  ]
};

/**
 * Validate a single file
 */
async function validateFile(filePath) {
  const errors = [];
  const warnings = [];

  try {
    // Check file exists
    const stats = await fs.stat(filePath);

    // Check file size
    if (stats.size > VALIDATION_RULES.maxFileSize) {
      errors.push(`File exceeds maximum size (${VALIDATION_RULES.maxFileSize} bytes)`);
    }

    if (stats.size < VALIDATION_RULES.minFileSize) {
      errors.push('File is empty');
    }

    // Check extension
    const ext = path.extname(filePath).toLowerCase();
    if (!VALIDATION_RULES.allowedExtensions.includes(ext)) {
      errors.push(`Unsupported file extension: ${ext}`);
    }

    // Check filename for sensitive patterns
    const basename = path.basename(filePath);
    VALIDATION_RULES.forbiddenPatterns.forEach(pattern => {
      if (pattern.test(basename)) {
        warnings.push(`Filename matches sensitive pattern: ${pattern}`);
      }
    });

    return {
      file: filePath,
      valid: errors.length === 0,
      errors,
      warnings
    };

  } catch (error) {
    return {
      file: filePath,
      valid: false,
      errors: [error.message],
      warnings: []
    };
  }
}

/**
 * Validate all documents
 */
async function validateDocuments() {
  const results = {
    total: 0,
    valid: 0,
    invalid: 0,
    files: []
  };

  const dirs = ['discovery-docs', 'case-files'];

  for (const dir of dirs) {
    try {
      const files = await scanDirectory(dir);

      for (const file of files) {
        const result = await validateFile(file);
        results.files.push(result);
        results.total++;

        if (result.valid) {
          results.valid++;
        } else {
          results.invalid++;
          console.error(`❌ ${file}: ${result.errors.join(', ')}`);
        }

        if (result.warnings.length > 0) {
          console.warn(`⚠️  ${file}: ${result.warnings.join(', ')}`);
        }
      }
    } catch (error) {
      if (error.code !== 'ENOENT') {
        console.error(`Error scanning ${dir}:`, error.message);
      }
    }
  }

  console.log(`\n📊 Validation Summary:`);
  console.log(`Total: ${results.total}`);
  console.log(`Valid: ${results.valid}`);
  console.log(`Invalid: ${results.invalid}`);

  if (results.invalid > 0) {
    process.exit(1);
  }

  return results;
}

/**
 * Scan directory recursively
 */
async function scanDirectory(dir) {
  const files = [];

  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        const subFiles = await scanDirectory(fullPath);
        files.push(...subFiles);
      } else if (entry.isFile()) {
        files.push(fullPath);
      }
    }
  } catch (error) {
    // Ignore directory not found errors
  }

  return files;
}

// Main
if (require.main === module) {
  validateDocuments();
}

module.exports = { validateFile, validateDocuments };
