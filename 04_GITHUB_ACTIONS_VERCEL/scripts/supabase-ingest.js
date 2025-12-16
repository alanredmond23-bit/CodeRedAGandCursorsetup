#!/usr/bin/env node

/**
 * Supabase Ingestion Script
 * Ingests processed documents into Supabase vector database
 */

const fs = require('fs').promises;
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const { OpenAI } = require('openai');

// Initialize clients
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY
});

const CONFIG = {
  embeddingModel: 'text-embedding-3-large',
  batchSize: 100,
  tableName: 'discovery_documents'
};

/**
 * Generate embeddings for text chunks
 */
async function generateEmbedding(text) {
  try {
    const response = await openai.embeddings.create({
      model: CONFIG.embeddingModel,
      input: text
    });

    return response.data[0].embedding;
  } catch (error) {
    console.error('Error generating embedding:', error.message);
    throw error;
  }
}

/**
 * Ingest a single document
 */
async function ingestDocument(document, caseId) {
  try {
    // Generate embedding
    const embedding = await generateEmbedding(document.text);

    // Prepare document data
    const documentData = {
      case_id: caseId,
      file_name: document.metadata?.fileName || path.basename(document.filePath),
      file_path: document.filePath,
      content: document.text,
      embedding: embedding,
      metadata: {
        ...document.metadata,
        analysis: document.analysis,
        processedAt: document.processedAt
      },
      word_count: document.metadata?.wordCount || 0,
      created_at: new Date().toISOString()
    };

    // Insert into Supabase
    const { data, error } = await supabase
      .from(CONFIG.tableName)
      .insert(documentData)
      .select();

    if (error) throw error;

    console.log(`✓ Ingested: ${documentData.file_name}`);
    return data[0];

  } catch (error) {
    console.error(`Error ingesting ${document.filePath}:`, error.message);
    throw error;
  }
}

/**
 * Batch ingest documents
 */
async function batchIngest(documents, caseId) {
  const results = {
    ingested: [],
    failed: []
  };

  for (let i = 0; i < documents.length; i += CONFIG.batchSize) {
    const batch = documents.slice(i, i + CONFIG.batchSize);
    console.log(`Processing batch ${Math.floor(i / CONFIG.batchSize) + 1}/${Math.ceil(documents.length / CONFIG.batchSize)}`);

    for (const doc of batch) {
      try {
        const result = await ingestDocument(doc, caseId);
        results.ingested.push(result);
      } catch (error) {
        results.failed.push({
          document: doc.filePath,
          error: error.message
        });
      }
    }

    // Rate limiting pause
    if (i + CONFIG.batchSize < documents.length) {
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  return results;
}

/**
 * Load documents from processed output
 */
async function loadProcessedDocuments(processedDir) {
  const documents = [];

  try {
    const entries = await fs.readdir(processedDir, { withFileTypes: true });

    for (const entry of entries) {
      if (entry.isDirectory() && entry.name.startsWith('batch-')) {
        const batchPath = path.join(processedDir, entry.name);
        const files = await fs.readdir(batchPath);

        for (const file of files) {
          if (file.endsWith('.json') && file !== 'metadata.json') {
            const filePath = path.join(batchPath, file);
            const content = await fs.readFile(filePath, 'utf-8');
            const document = JSON.parse(content);

            if (document.success) {
              documents.push(document);
            }
          }
        }
      }
    }

    return documents;
  } catch (error) {
    console.error('Error loading documents:', error);
    throw error;
  }
}

/**
 * Verify ingestion
 */
async function verifyIngestion(caseId, expectedCount) {
  try {
    const { count, error } = await supabase
      .from(CONFIG.tableName)
      .select('*', { count: 'exact', head: true })
      .eq('case_id', caseId);

    if (error) throw error;

    console.log(`\n📊 Verification Results:`);
    console.log(`Expected: ${expectedCount}`);
    console.log(`Ingested: ${count}`);
    console.log(`Status: ${count === expectedCount ? '✅ Success' : '⚠️  Mismatch'}`);

    return count === expectedCount;
  } catch (error) {
    console.error('Error verifying ingestion:', error);
    return false;
  }
}

/**
 * Main function
 */
async function main() {
  try {
    const args = process.argv.slice(2);
    const processedDir = args[0] || './processed-docs';
    const caseId = process.env.CASE_ID || `CASE-${Date.now()}`;

    console.log(`🚀 Starting ingestion for case: ${caseId}`);
    console.log(`Source directory: ${processedDir}`);

    // Load processed documents
    const documents = await loadProcessedDocuments(processedDir);
    console.log(`📄 Found ${documents.length} documents to ingest`);

    if (documents.length === 0) {
      console.log('No documents to ingest');
      return;
    }

    // Ingest documents
    const results = await batchIngest(documents, caseId);

    // Save results
    const report = {
      caseId,
      timestamp: new Date().toISOString(),
      totalDocuments: documents.length,
      ingestedCount: results.ingested.length,
      failedCount: results.failed.length,
      ingested: results.ingested.map(d => d.file_name),
      failed: results.failed
    };

    await fs.writeFile(
      'ingestion-result.json',
      JSON.stringify(report, null, 2)
    );

    // Verify
    await verifyIngestion(caseId, results.ingested.length);

    console.log('\n✅ Ingestion complete!');
    console.log(`Ingested: ${results.ingested.length}`);
    console.log(`Failed: ${results.failed.length}`);

    if (results.failed.length > 0) {
      console.log('\n❌ Failed documents:');
      results.failed.forEach(f => console.log(`  - ${f.document}: ${f.error}`));
    }

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { ingestDocument, batchIngest, generateEmbedding };
