#!/usr/bin/env node

/**
 * Audit Log Generator
 * Generates comprehensive audit trail for legal compliance
 */

const fs = require('fs').promises;
const path = require('path');

async function generateAuditLog(artifactsDir) {
  const audit = {
    version: '1.0.0',
    generated: new Date().toISOString(),
    runId: process.env.GITHUB_RUN_ID || 'local',
    repository: process.env.GITHUB_REPOSITORY || 'unknown',
    actor: process.env.GITHUB_ACTOR || 'system',
    workflow: process.env.GITHUB_WORKFLOW || 'discovery-pipeline',
    events: [],
    summary: {
      documentsProcessed: 0,
      privilegedDetected: 0,
      totalCost: 0,
      duration: null
    }
  };

  try {
    // Scan artifacts directory
    const entries = await fs.readdir(artifactsDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory()) {
        const dirPath = path.join(artifactsDir, entry.name);

        // Process manifest
        if (entry.name === 'processing-manifest') {
          try {
            const manifestPath = path.join(dirPath, 'manifest.json');
            const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));

            audit.events.push({
              timestamp: manifest.generated,
              type: 'manifest_created',
              data: {
                totalDocuments: manifest.summary.total,
                byExtension: manifest.summary.byExtension
              }
            });

            audit.summary.documentsProcessed = manifest.summary.total;
          } catch (e) {}
        }

        // Process privilege report
        if (entry.name === 'privilege-report') {
          try {
            const reportPath = path.join(dirPath, 'privilege-report.json');
            const report = JSON.parse(await fs.readFile(reportPath, 'utf-8'));

            audit.events.push({
              timestamp: new Date().toISOString(),
              type: 'privilege_detection_complete',
              data: {
                privilegedCount: report.privileged_count || 0,
                highRiskCount: report.high_risk_count || 0
              }
            });

            audit.summary.privilegedDetected = report.privileged_count || 0;
          } catch (e) {}
        }

        // Process cost report
        if (entry.name === 'cost-report') {
          try {
            const reportPath = path.join(dirPath, 'cost-report.json');
            const report = JSON.parse(await fs.readFile(reportPath, 'utf-8'));

            audit.events.push({
              timestamp: report.generatedAt || new Date().toISOString(),
              type: 'cost_calculation_complete',
              data: {
                totalCost: report.summary?.totalCost || 0,
                breakdown: report.breakdown || {}
              }
            });

            audit.summary.totalCost = report.summary?.totalCost || 0;
          } catch (e) {}
        }

        // Process ingestion report
        if (entry.name === 'ingestion-report') {
          try {
            const reportPath = path.join(dirPath, 'ingestion-report.json');
            const report = JSON.parse(await fs.readFile(reportPath, 'utf-8'));

            audit.events.push({
              timestamp: report.timestamp || new Date().toISOString(),
              type: 'supabase_ingestion_complete',
              data: {
                ingestedCount: report.ingestedCount || 0,
                failedCount: report.failedCount || 0
              }
            });
          } catch (e) {}
        }
      }
    }

    // Sort events by timestamp
    audit.events.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

    // Calculate duration
    if (audit.events.length > 0) {
      const start = new Date(audit.events[0].timestamp);
      const end = new Date(audit.events[audit.events.length - 1].timestamp);
      audit.summary.duration = Math.round((end - start) / 1000); // seconds
    }

    // Add compliance metadata
    audit.compliance = {
      retention: '7 years',
      standard: 'Fed. R. Civ. P. 26(b)(5)',
      encrypted: false,
      chainOfCustody: audit.events.map(e => ({
        timestamp: e.timestamp,
        type: e.type,
        actor: audit.actor
      }))
    };

    // Output audit log
    console.log(JSON.stringify(audit, null, 2));

  } catch (error) {
    console.error('Error generating audit log:', error);
    process.exit(1);
  }
}

// Main
if (require.main === module) {
  const artifactsDir = process.argv[2] || './audit-artifacts';
  generateAuditLog(artifactsDir);
}

module.exports = { generateAuditLog };
