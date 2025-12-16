#!/usr/bin/env node

/**
 * Manifest Generator
 * Creates a processing manifest for discovery documents
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

const DISCOVERY_DIRS = ['discovery-docs', 'case-files'];
const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.doc', '.txt'];

/**
 * Calculate file hash
 */
async function calculateHash(filePath) {
  const content = await fs.readFile(filePath);
  return crypto.createHash('sha256').update(content).digest('hex');
}

/**
 * Scan directory for documents
 */
async function scanDirectory(dirPath) {
  const documents = [];

  try {
    const entries = await fs.readdir(dirPath, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory()) {
        // Recursively scan subdirectories
        const subDocs = await scanDirectory(fullPath);
        documents.push(...subDocs);
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name).toLowerCase();

        if (SUPPORTED_EXTENSIONS.includes(ext)) {
          const stats = await fs.stat(fullPath);
          const hash = await calculateHash(fullPath);

          documents.push({
            path: fullPath,
            name: entry.name,
            extension: ext,
            size: stats.size,
            hash: hash,
            created: stats.birthtime.toISOString(),
            modified: stats.mtime.toISOString()
          });
        }
      }
    }
  } catch (error) {
    if (error.code !== 'ENOENT') {
      console.error(`Error scanning ${dirPath}:`, error.message);
    }
  }

  return documents;
}

/**
 * Generate processing manifest
 */
async function generateManifest() {
  const manifest = {
    version: '1.0.0',
    generated: new Date().toISOString(),
    documents: [],
    summary: {
      total: 0,
      byExtension: {},
      totalSize: 0
    }
  };

  // Scan all discovery directories
  for (const dir of DISCOVERY_DIRS) {
    const documents = await scanDirectory(dir);
    manifest.documents.push(...documents);
  }

  // Calculate summary statistics
  manifest.summary.total = manifest.documents.length;
  manifest.summary.totalSize = manifest.documents.reduce((sum, doc) => sum + doc.size, 0);

  // Count by extension
  manifest.documents.forEach(doc => {
    const ext = doc.extension;
    manifest.summary.byExtension[ext] = (manifest.summary.byExtension[ext] || 0) + 1;
  });

  return manifest;
}

/**
 * Main function
 */
async function main() {
  try {
    const manifest = await generateManifest();

    // Output manifest as JSON
    console.log(JSON.stringify(manifest, null, 2));

    // Log summary
    console.error('\n📋 Manifest Summary:');
    console.error(`Total Documents: ${manifest.summary.total}`);
    console.error(`Total Size: ${(manifest.summary.totalSize / 1024 / 1024).toFixed(2)} MB`);
    console.error('\nBy Extension:');
    Object.entries(manifest.summary.byExtension).forEach(([ext, count]) => {
      console.error(`  ${ext}: ${count}`);
    });

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { generateManifest, scanDirectory };
