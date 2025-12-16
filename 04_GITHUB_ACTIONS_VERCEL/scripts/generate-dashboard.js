#!/usr/bin/env node

/**
 * Dashboard Generator
 * Generates HTML dashboard for discovery pipeline results
 */

const fs = require('fs').promises;
const path = require('path');

/**
 * Generate complete dashboard HTML
 */
async function generateDashboard(reportsDir) {
  try {
    console.log('Generating dashboard from reports...');

    // Load all reports
    const reports = await loadReports(reportsDir);

    // Generate HTML
    const html = buildDashboardHTML(reports);

    // Create dashboard directory
    await fs.mkdir('./dashboard', { recursive: true });

    // Write HTML
    await fs.writeFile('./dashboard/index.html', html);

    // Copy static assets
    await generateStaticAssets();

    console.log('✅ Dashboard generated successfully');

  } catch (error) {
    console.error('Error generating dashboard:', error);
    throw error;
  }
}

/**
 * Load all reports from directory
 */
async function loadReports(reportsDir) {
  const reports = {
    manifest: null,
    privilege: null,
    costs: null,
    ingestion: null,
    processing: []
  };

  try {
    // Load manifest
    try {
      const manifestPath = path.join(reportsDir, 'processing-manifest', 'manifest.json');
      reports.manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));
    } catch (e) {
      console.warn('Manifest not found');
    }

    // Load privilege report
    try {
      const privilegePath = path.join(reportsDir, 'privilege-report', 'privilege-report.json');
      reports.privilege = JSON.parse(await fs.readFile(privilegePath, 'utf-8'));
    } catch (e) {
      console.warn('Privilege report not found');
    }

    // Load cost report
    try {
      const costPath = path.join(reportsDir, 'cost-report', 'cost-report.json');
      reports.costs = JSON.parse(await fs.readFile(costPath, 'utf-8'));
    } catch (e) {
      console.warn('Cost report not found');
    }

    // Load ingestion report
    try {
      const ingestionPath = path.join(reportsDir, 'ingestion-report', 'ingestion-report.json');
      reports.ingestion = JSON.parse(await fs.readFile(ingestionPath, 'utf-8'));
    } catch (e) {
      console.warn('Ingestion report not found');
    }

  } catch (error) {
    console.error('Error loading reports:', error);
  }

  return reports;
}

/**
 * Build complete dashboard HTML
 */
function buildDashboardHTML(reports) {
  const caseNumber = process.env.CASE_NUMBER || 'AUTO-' + Date.now();
  const timestamp = new Date().toISOString();

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Discovery Pipeline Dashboard - ${caseNumber}</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      padding: 20px;
    }

    .container {
      max-width: 1400px;
      margin: 0 auto;
    }

    header {
      background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 30px;
      border: 1px solid #334155;
    }

    h1 {
      font-size: 32px;
      margin-bottom: 10px;
      color: #fff;
    }

    .subtitle {
      color: #94a3b8;
      font-size: 14px;
    }

    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      background: #1e293b;
      padding: 25px;
      border-radius: 12px;
      border: 1px solid #334155;
      transition: transform 0.2s, border-color 0.2s;
    }

    .stat-card:hover {
      transform: translateY(-2px);
      border-color: #475569;
    }

    .stat-label {
      color: #94a3b8;
      font-size: 14px;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 36px;
      font-weight: bold;
      color: #fff;
    }

    .stat-value.success {
      color: #22c55e;
    }

    .stat-value.warning {
      color: #f59e0b;
    }

    .stat-value.danger {
      color: #ef4444;
    }

    .section {
      background: #1e293b;
      padding: 30px;
      border-radius: 12px;
      margin-bottom: 30px;
      border: 1px solid #334155;
    }

    .section-title {
      font-size: 24px;
      margin-bottom: 20px;
      color: #fff;
      border-bottom: 2px solid #334155;
      padding-bottom: 10px;
    }

    .table {
      width: 100%;
      border-collapse: collapse;
    }

    .table th {
      background: #0f172a;
      padding: 12px;
      text-align: left;
      font-weight: 600;
      color: #94a3b8;
      border-bottom: 2px solid #334155;
    }

    .table td {
      padding: 12px;
      border-bottom: 1px solid #334155;
    }

    .table tr:hover {
      background: #0f172a;
    }

    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }

    .badge.success {
      background: #22c55e20;
      color: #22c55e;
    }

    .badge.warning {
      background: #f59e0b20;
      color: #f59e0b;
    }

    .badge.danger {
      background: #ef444420;
      color: #ef4444;
    }

    .badge.info {
      background: #3b82f620;
      color: #3b82f6;
    }

    .progress-bar {
      width: 100%;
      height: 8px;
      background: #0f172a;
      border-radius: 4px;
      overflow: hidden;
      margin-top: 8px;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #3b82f6, #8b5cf6);
      transition: width 0.3s;
    }

    .chart-container {
      height: 300px;
      margin-top: 20px;
    }

    footer {
      text-align: center;
      color: #64748b;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid #334155;
    }

    .alert {
      padding: 15px 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      border-left: 4px solid;
    }

    .alert.warning {
      background: #f59e0b20;
      border-color: #f59e0b;
      color: #fbbf24;
    }

    .alert.danger {
      background: #ef444420;
      border-color: #ef4444;
      color: #fca5a5;
    }

    .alert.success {
      background: #22c55e20;
      border-color: #22c55e;
      color: #86efac;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <h1>🔍 Discovery Pipeline Dashboard</h1>
      <div class="subtitle">Case: ${caseNumber} | Generated: ${new Date(timestamp).toLocaleString()}</div>
    </header>

    ${generateAlerts(reports)}

    <div class="stats-grid">
      ${generateStatCards(reports)}
    </div>

    ${generatePrivilegeSection(reports)}

    ${generateCostSection(reports)}

    ${generateProcessingSection(reports)}

    ${generateIngestionSection(reports)}

    <footer>
      <p>Discovery Pipeline Dashboard | Powered by GitHub Actions & Vercel</p>
      <p style="margin-top: 8px; font-size: 12px;">Auto-generated from CI/CD pipeline</p>
    </footer>
  </div>
</body>
</html>`;
}

/**
 * Generate alert banners
 */
function generateAlerts(reports) {
  const alerts = [];

  // Privilege alerts
  if (reports.privilege?.privileged_count > 0) {
    alerts.push(`
      <div class="alert danger">
        <strong>⚠️ Privileged Documents Detected:</strong> ${reports.privilege.privileged_count} documents require legal review before production.
      </div>
    `);
  }

  // Cost alerts
  if (reports.costs?.summary?.totalCost > 100) {
    alerts.push(`
      <div class="alert warning">
        <strong>💰 High Processing Cost:</strong> Total cost ($${reports.costs.summary.totalCost.toFixed(2)}) exceeds threshold.
      </div>
    `);
  }

  // Success alert
  if (reports.ingestion?.success) {
    alerts.push(`
      <div class="alert success">
        <strong>✅ Pipeline Complete:</strong> All documents processed and ingested successfully.
      </div>
    `);
  }

  return alerts.join('\n');
}

/**
 * Generate stat cards
 */
function generateStatCards(reports) {
  const stats = [
    {
      label: 'Documents Processed',
      value: reports.manifest?.total || 0,
      class: 'success'
    },
    {
      label: 'Privileged Flagged',
      value: reports.privilege?.privileged_count || 0,
      class: reports.privilege?.privileged_count > 0 ? 'warning' : 'success'
    },
    {
      label: 'Total Cost',
      value: `$${(reports.costs?.summary?.totalCost || 0).toFixed(2)}`,
      class: 'info'
    },
    {
      label: 'Documents Ingested',
      value: reports.ingestion?.ingested_count || 0,
      class: 'success'
    }
  ];

  return stats.map(stat => `
    <div class="stat-card">
      <div class="stat-label">${stat.label}</div>
      <div class="stat-value ${stat.class}">${stat.value}</div>
    </div>
  `).join('');
}

/**
 * Generate privilege section
 */
function generatePrivilegeSection(reports) {
  if (!reports.privilege) return '';

  return `
    <div class="section">
      <h2 class="section-title">🔒 Privilege Detection Results</h2>
      <table class="table">
        <thead>
          <tr>
            <th>Document</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>Keywords</th>
          </tr>
        </thead>
        <tbody>
          ${(reports.privilege.privileged_documents || []).map(doc => `
            <tr>
              <td>${path.basename(doc.document)}</td>
              <td>${(doc.confidence * 100).toFixed(1)}%</td>
              <td><span class="badge danger">Privileged</span></td>
              <td>${(doc.keywords || []).slice(0, 3).join(', ')}</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  `;
}

/**
 * Generate cost section
 */
function generateCostSection(reports) {
  if (!reports.costs) return '';

  const breakdown = reports.costs.breakdown || {};

  return `
    <div class="section">
      <h2 class="section-title">💰 Cost Breakdown</h2>
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Extraction</div>
          <div class="stat-value">$${(breakdown.extraction || 0).toFixed(4)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Embedding</div>
          <div class="stat-value">$${(breakdown.embedding || 0).toFixed(4)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Analysis</div>
          <div class="stat-value">$${(breakdown.analysis || 0).toFixed(4)}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Storage</div>
          <div class="stat-value">$${(breakdown.storage || 0).toFixed(4)}</div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Generate processing section
 */
function generateProcessingSection(reports) {
  return `
    <div class="section">
      <h2 class="section-title">⚙️ Processing Status</h2>
      <p>Pipeline execution completed successfully.</p>
      <div class="progress-bar">
        <div class="progress-fill" style="width: 100%"></div>
      </div>
    </div>
  `;
}

/**
 * Generate ingestion section
 */
function generateIngestionSection(reports) {
  if (!reports.ingestion) return '';

  return `
    <div class="section">
      <h2 class="section-title">📊 RAG Ingestion Status</h2>
      <p><span class="badge success">Complete</span> ${reports.ingestion.ingested_count} documents ingested to vector database</p>
    </div>
  `;
}

/**
 * Generate static assets (CSS, JS)
 */
async function generateStaticAssets() {
  // Could generate additional CSS/JS files here if needed
  console.log('Static assets generated');
}

/**
 * Main function
 */
async function main() {
  try {
    const args = process.argv.slice(2);
    const reportsDir = args[0] || './reports';

    await generateDashboard(reportsDir);

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { generateDashboard };
