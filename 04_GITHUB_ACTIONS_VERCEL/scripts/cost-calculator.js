#!/usr/bin/env node

/**
 * Cost Calculator
 * Calculates processing costs for discovery documents
 */

const fs = require('fs').promises;
const path = require('path');

// Pricing (as of 2024)
const PRICING = {
  openai: {
    'gpt-4-turbo': {
      input: 0.01 / 1000,  // per token
      output: 0.03 / 1000
    },
    'gpt-4': {
      input: 0.03 / 1000,
      output: 0.06 / 1000
    },
    'gpt-3.5-turbo': {
      input: 0.0005 / 1000,
      output: 0.0015 / 1000
    },
    'text-embedding-3-large': 0.00013 / 1000,
    'text-embedding-3-small': 0.00002 / 1000,
    'text-embedding-ada-002': 0.0001 / 1000
  },
  anthropic: {
    'claude-3-5-sonnet-20241022': {
      input: 3.00 / 1000000,
      output: 15.00 / 1000000
    },
    'claude-3-opus': {
      input: 15.00 / 1000000,
      output: 75.00 / 1000000
    },
    'claude-3-sonnet': {
      input: 3.00 / 1000000,
      output: 15.00 / 1000000
    },
    'claude-3-haiku': {
      input: 0.25 / 1000000,
      output: 1.25 / 1000000
    }
  },
  supabase: {
    storage: 0.021 / 1024 / 1024 / 1024, // per GB/month
    database: 0.00008 / 1000, // per row operation
    bandwidth: 0.09 / 1024 / 1024 / 1024 // per GB
  }
};

/**
 * Calculate cost for a single document
 */
function calculateDocumentCost(document) {
  const costs = {
    extraction: 0,
    embedding: 0,
    analysis: 0,
    storage: 0,
    total: 0
  };

  // Extraction cost (OCR if needed)
  if (document.metadata?.usedOCR) {
    costs.extraction = 0.001; // Estimated OCR cost
  }

  // Embedding cost
  if (document.embedding) {
    const tokens = estimateTokens(document.text);
    costs.embedding = tokens * PRICING.openai['text-embedding-3-large'];
  }

  // Analysis cost
  if (document.analysis) {
    const model = document.analysis.model || 'claude-3-5-sonnet-20241022';
    const inputTokens = document.analysis.inputTokens || estimateTokens(document.text);
    const outputTokens = document.analysis.outputTokens || 500;

    if (model.startsWith('claude')) {
      const pricing = PRICING.anthropic[model];
      costs.analysis = (inputTokens * pricing.input) + (outputTokens * pricing.output);
    } else if (model.startsWith('gpt')) {
      const pricing = PRICING.openai[model];
      costs.analysis = (inputTokens * pricing.input) + (outputTokens * pricing.output);
    }
  }

  // Storage cost (estimated monthly)
  if (document.metadata?.fileSize) {
    costs.storage = document.metadata.fileSize * PRICING.supabase.storage * 30;
  }

  costs.total = Object.values(costs).reduce((sum, cost) => sum + cost, 0);

  return costs;
}

/**
 * Calculate cost for a batch of documents
 */
async function calculateBatchCost(batchDir) {
  try {
    const files = await fs.readdir(batchDir);
    const jsonFiles = files.filter(f => f.endsWith('.json') && f !== 'metadata.json');

    let totalCost = 0;
    const documentCosts = [];

    for (const file of jsonFiles) {
      const filePath = path.join(batchDir, file);
      const content = await fs.readFile(filePath, 'utf-8');
      const document = JSON.parse(content);

      const cost = calculateDocumentCost(document);
      documentCosts.push({
        document: file,
        ...cost
      });

      totalCost += cost.total;
    }

    return {
      batchDir,
      documentCount: jsonFiles.length,
      documentCosts,
      totalCost,
      averageCost: totalCost / jsonFiles.length
    };

  } catch (error) {
    console.error(`Error calculating batch cost:`, error.message);
    throw error;
  }
}

/**
 * Calculate aggregate costs across all batches
 */
async function calculateAggregateCosts(batchesDir) {
  try {
    const batches = await fs.readdir(batchesDir);
    const batchDirs = batches.filter(b => b.startsWith('processed-batch-'));

    const batchCosts = [];
    let grandTotal = 0;
    let totalDocuments = 0;

    for (const batchDir of batchDirs) {
      const fullPath = path.join(batchesDir, batchDir);
      const batchCost = await calculateBatchCost(fullPath);

      batchCosts.push(batchCost);
      grandTotal += batchCost.totalCost;
      totalDocuments += batchCost.documentCount;
    }

    return {
      batches: batchCosts,
      summary: {
        totalBatches: batchCosts.length,
        totalDocuments,
        totalCost: grandTotal,
        averageCostPerDocument: totalDocuments > 0 ? grandTotal / totalDocuments : 0,
        averageCostPerBatch: batchCosts.length > 0 ? grandTotal / batchCosts.length : 0
      },
      breakdown: calculateCostBreakdown(batchCosts)
    };

  } catch (error) {
    console.error(`Error calculating aggregate costs:`, error.message);
    throw error;
  }
}

/**
 * Calculate cost breakdown by category
 */
function calculateCostBreakdown(batchCosts) {
  const breakdown = {
    extraction: 0,
    embedding: 0,
    analysis: 0,
    storage: 0
  };

  batchCosts.forEach(batch => {
    batch.documentCosts.forEach(doc => {
      breakdown.extraction += doc.extraction || 0;
      breakdown.embedding += doc.embedding || 0;
      breakdown.analysis += doc.analysis || 0;
      breakdown.storage += doc.storage || 0;
    });
  });

  return breakdown;
}

/**
 * Estimate token count for text
 */
function estimateTokens(text) {
  if (!text) return 0;
  // Rough estimate: ~4 characters per token
  return Math.ceil(text.length / 4);
}

/**
 * Calculate cost for specific period
 */
async function calculatePeriodCost(period = 'daily') {
  // This would typically query Supabase for actual usage data
  // For now, returning a placeholder structure

  const now = new Date();
  let startDate;

  switch (period) {
    case 'daily':
      startDate = new Date(now);
      startDate.setDate(startDate.getDate() - 1);
      break;
    case 'weekly':
      startDate = new Date(now);
      startDate.setDate(startDate.getDate() - 7);
      break;
    case 'monthly':
      startDate = new Date(now);
      startDate.setMonth(startDate.getMonth() - 1);
      break;
    default:
      throw new Error(`Invalid period: ${period}`);
  }

  // Placeholder - in production, query actual usage from Supabase
  return {
    period,
    startDate: startDate.toISOString(),
    endDate: now.toISOString(),
    cost: 0, // Would be calculated from actual data
    breakdown: {
      openai: 0,
      anthropic: 0,
      supabase: 0
    }
  };
}

/**
 * Generate cost report
 */
function generateCostReport(costs) {
  const report = {
    generatedAt: new Date().toISOString(),
    summary: costs.summary,
    breakdown: costs.breakdown,
    recommendations: generateRecommendations(costs)
  };

  return report;
}

/**
 * Generate cost optimization recommendations
 */
function generateRecommendations(costs) {
  const recommendations = [];
  const avgCost = costs.summary.averageCostPerDocument;

  if (avgCost > 0.10) {
    recommendations.push({
      priority: 'high',
      category: 'model-selection',
      recommendation: 'Consider using Claude 3 Haiku for simple document analysis',
      potentialSavings: avgCost * 0.6 * costs.summary.totalDocuments
    });
  }

  if (costs.breakdown.embedding > costs.breakdown.analysis) {
    recommendations.push({
      priority: 'medium',
      category: 'embedding',
      recommendation: 'Consider using text-embedding-3-small for cost reduction',
      potentialSavings: costs.breakdown.embedding * 0.85
    });
  }

  if (costs.summary.totalDocuments > 1000) {
    recommendations.push({
      priority: 'low',
      category: 'batch-processing',
      recommendation: 'Implement caching to avoid reprocessing unchanged documents',
      potentialSavings: costs.summary.totalCost * 0.2
    });
  }

  return recommendations;
}

/**
 * Main function
 */
async function main() {
  try {
    const args = process.argv.slice(2);
    const targetDir = args[0] || './output';

    console.log(`Calculating costs for: ${targetDir}`);

    // Determine if single batch or aggregate
    const stats = await fs.stat(targetDir);

    let costs;
    if (stats.isDirectory()) {
      const files = await fs.readdir(targetDir);
      if (files.some(f => f.startsWith('processed-batch-'))) {
        // Aggregate calculation
        costs = await calculateAggregateCosts(targetDir);
      } else {
        // Single batch
        costs = await calculateBatchCost(targetDir);
      }
    }

    // Generate report
    const report = generateCostReport(costs);

    // Save report
    await fs.writeFile(
      'cost-report.json',
      JSON.stringify(report, null, 2)
    );

    // Output summary
    console.log('\n📊 Cost Summary');
    console.log('─'.repeat(50));
    console.log(`Total Documents: ${costs.summary?.totalDocuments || 0}`);
    console.log(`Total Cost: $${(costs.summary?.totalCost || costs.totalCost || 0).toFixed(4)}`);
    console.log(`Average/Document: $${(costs.summary?.averageCostPerDocument || costs.averageCost || 0).toFixed(4)}`);
    console.log('─'.repeat(50));

    // Output total cost for GitHub Actions
    console.log((costs.summary?.totalCost || costs.totalCost || 0).toFixed(4));

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = {
  calculateDocumentCost,
  calculateBatchCost,
  calculateAggregateCosts,
  calculatePeriodCost,
  generateCostReport
};
