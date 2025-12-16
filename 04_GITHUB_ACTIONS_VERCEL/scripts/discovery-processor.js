#!/usr/bin/env node

/**
 * Discovery Document Processor
 * Processes legal discovery documents with AI analysis
 */

const fs = require('fs').promises;
const path = require('path');
const pdfParse = require('pdf-parse');
const mammoth = require('mammoth');
const Tesseract = require('tesseract.js');
const OpenAI = require('openai');
const Anthropic = require('@anthropic-ai/sdk');

// Configuration
const CONFIG = {
  maxRetries: parseInt(process.env.MAX_RETRIES || '3'),
  batchNumber: parseInt(process.env.BATCH_NUMBER || '1'),
  chunkSize: 4000,
  outputDir: './output',
  supportedFormats: ['.pdf', '.docx', '.txt', '.doc']
};

// Initialize AI clients
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Process a single document
 */
async function processDocument(filePath, retries = 0) {
  try {
    console.log(`Processing: ${filePath}`);

    // Extract text based on file type
    const text = await extractText(filePath);

    // Analyze with AI
    const analysis = await analyzeDocument(text, filePath);

    // Extract metadata
    const metadata = await extractMetadata(text, filePath);

    // Calculate processing cost
    const cost = calculateCost(text, analysis);

    return {
      filePath,
      text,
      analysis,
      metadata,
      cost,
      processedAt: new Date().toISOString(),
      success: true
    };

  } catch (error) {
    console.error(`Error processing ${filePath}:`, error.message);

    if (retries < CONFIG.maxRetries) {
      console.log(`Retrying... (${retries + 1}/${CONFIG.maxRetries})`);
      await sleep(1000 * (retries + 1)); // Exponential backoff
      return processDocument(filePath, retries + 1);
    }

    return {
      filePath,
      error: error.message,
      success: false,
      processedAt: new Date().toISOString()
    };
  }
}

/**
 * Extract text from document
 */
async function extractText(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const buffer = await fs.readFile(filePath);

  switch (ext) {
    case '.pdf':
      return await extractFromPDF(buffer);

    case '.docx':
    case '.doc':
      return await extractFromDOCX(buffer);

    case '.txt':
      return buffer.toString('utf-8');

    default:
      throw new Error(`Unsupported file format: ${ext}`);
  }
}

/**
 * Extract text from PDF
 */
async function extractFromPDF(buffer) {
  try {
    const data = await pdfParse(buffer);
    return data.text;
  } catch (error) {
    console.log('PDF parse failed, attempting OCR...');
    return await performOCR(buffer);
  }
}

/**
 * Extract text from DOCX
 */
async function extractFromDOCX(buffer) {
  const result = await mammoth.extractRawText({ buffer });
  return result.value;
}

/**
 * Perform OCR on image-based documents
 */
async function performOCR(buffer) {
  const { data: { text } } = await Tesseract.recognize(buffer, 'eng', {
    logger: m => console.log(m)
  });
  return text;
}

/**
 * Analyze document with AI
 */
async function analyzeDocument(text, filePath) {
  const chunks = chunkText(text, CONFIG.chunkSize);

  // Use Claude for comprehensive analysis
  const prompt = `Analyze this legal discovery document and provide:
1. Document type (email, contract, memo, etc.)
2. Key parties mentioned
3. Important dates
4. Main topics/subjects
5. Relevance to case (1-10 score)
6. Key excerpts (up to 5)
7. Potential privilege concerns

Document excerpt:
${chunks[0]}`;

  const message = await anthropic.messages.create({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 2000,
    messages: [{
      role: 'user',
      content: prompt
    }]
  });

  return {
    analysis: message.content[0].text,
    model: 'claude-3-5-sonnet',
    tokens: message.usage.input_tokens + message.usage.output_tokens
  };
}

/**
 * Extract metadata from document
 */
async function extractMetadata(text, filePath) {
  const stats = await fs.stat(filePath);

  return {
    fileName: path.basename(filePath),
    fileSize: stats.size,
    fileType: path.extname(filePath),
    wordCount: text.split(/\s+/).length,
    charCount: text.length,
    createdAt: stats.birthtime,
    modifiedAt: stats.mtime
  };
}

/**
 * Calculate processing cost
 */
function calculateCost(text, analysis) {
  // OpenAI pricing (example)
  const embeddingCost = (text.length / 1000) * 0.0001; // $0.0001 per 1K tokens

  // Claude pricing
  const inputTokens = analysis.tokens || 0;
  const inputCost = (inputTokens / 1000000) * 3.00; // $3 per 1M tokens
  const outputCost = (inputTokens / 1000000) * 15.00; // $15 per 1M tokens

  return {
    embedding: embeddingCost,
    analysis: inputCost + outputCost,
    total: embeddingCost + inputCost + outputCost
  };
}

/**
 * Chunk text into smaller pieces
 */
function chunkText(text, size) {
  const chunks = [];
  for (let i = 0; i < text.length; i += size) {
    chunks.push(text.slice(i, i + size));
  }
  return chunks;
}

/**
 * Sleep utility
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Main processing function
 */
async function main() {
  try {
    // Load manifest
    const manifestPath = './manifest.json';
    const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf-8'));

    // Get documents for this batch
    const batchSize = Math.ceil(manifest.documents.length / 4);
    const startIdx = (CONFIG.batchNumber - 1) * batchSize;
    const endIdx = startIdx + batchSize;
    const batchDocuments = manifest.documents.slice(startIdx, endIdx);

    console.log(`Processing batch ${CONFIG.batchNumber}: ${batchDocuments.length} documents`);

    // Process documents
    const results = [];
    for (const doc of batchDocuments) {
      const result = await processDocument(doc.path);
      results.push(result);
    }

    // Create output directory
    const batchDir = path.join(CONFIG.outputDir, `batch-${CONFIG.batchNumber}`);
    await fs.mkdir(batchDir, { recursive: true });

    // Save results
    for (let i = 0; i < results.length; i++) {
      const outputPath = path.join(batchDir, `document-${i}.json`);
      await fs.writeFile(outputPath, JSON.stringify(results[i], null, 2));
    }

    // Save batch metadata
    const metadata = {
      batchNumber: CONFIG.batchNumber,
      documentCount: results.length,
      successCount: results.filter(r => r.success).length,
      failureCount: results.filter(r => !r.success).length,
      totalCost: results.reduce((sum, r) => sum + (r.cost?.total || 0), 0),
      processedAt: new Date().toISOString()
    };

    await fs.writeFile(
      path.join(batchDir, 'metadata.json'),
      JSON.stringify(metadata, null, 2)
    );

    console.log('✅ Batch processing complete');
    console.log(`Success: ${metadata.successCount}, Failed: ${metadata.failureCount}`);
    console.log(`Total cost: $${metadata.totalCost.toFixed(4)}`);

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { processDocument, extractText, analyzeDocument };
