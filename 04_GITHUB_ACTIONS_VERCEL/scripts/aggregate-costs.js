#!/usr/bin/env node

/**
 * Aggregate Costs
 * Aggregates costs from all batch results
 */

const fs = require('fs').promises;
const path = require('path');

async function aggregateCosts(batchesDir) {
  let totalCost = 0;

  try {
    const entries = await fs.readdir(batchesDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory() && entry.name.startsWith('processed-batch-')) {
        const metadataPath = path.join(batchesDir, entry.name, 'metadata.json');

        try {
          const content = await fs.readFile(metadataPath, 'utf-8');
          const metadata = JSON.parse(content);
          totalCost += metadata.totalCost || 0;
        } catch (error) {
          console.error(`Error reading ${metadataPath}:`, error.message);
        }
      }
    }

    console.log(totalCost.toFixed(4));
    return totalCost;

  } catch (error) {
    console.error('Error aggregating costs:', error);
    return 0;
  }
}

// Main
if (require.main === module) {
  const batchesDir = process.argv[2] || './all-batches';
  aggregateCosts(batchesDir);
}

module.exports = { aggregateCosts };
