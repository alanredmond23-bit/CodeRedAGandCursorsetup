#!/usr/bin/env node

/**
 * Privilege Detector
 * Detects attorney-client privilege and work product in discovery documents
 */

const fs = require('fs').promises;
const OpenAI = require('openai');
const Anthropic = require('@anthropic-ai/sdk');
const natural = require('natural');

// Privilege indicators
const PRIVILEGE_KEYWORDS = {
  high: [
    'attorney-client privilege',
    'work product',
    'privileged and confidential',
    'attorney work product',
    'legal advice',
    'in anticipation of litigation',
    'prepared for litigation'
  ],
  medium: [
    'confidential communication',
    'attorney',
    'counsel',
    'legal opinion',
    'lawyer',
    'law firm',
    'privileged',
    'attorney communication'
  ],
  low: [
    'confidential',
    'legal',
    'advice',
    'discussion with counsel'
  ]
};

// Common attorney email patterns
const ATTORNEY_PATTERNS = [
  /@.*law\.com$/i,
  /@.*legal\.com$/i,
  /esq\.?$/i,
  /attorney/i,
  /counsel/i
];

// Initialize AI clients
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

/**
 * Detect privilege in a document
 */
async function detectPrivilege(document, options = {}) {
  const {
    sensitivity = 'medium',
    provider = 'anthropic',
    useAI = true
  } = options;

  try {
    // Stage 1: Keyword analysis
    const keywordResult = analyzeKeywords(document.text);

    // Stage 2: Pattern matching
    const patternResult = analyzePatterns(document);

    // Stage 3: AI analysis (if enabled and confidence is uncertain)
    let aiResult = null;
    if (useAI && keywordResult.confidence < 0.9) {
      aiResult = await analyzeWithAI(document.text, provider);
    }

    // Aggregate results
    const finalResult = aggregateResults(
      keywordResult,
      patternResult,
      aiResult,
      sensitivity
    );

    return {
      document: document.filePath,
      isPrivileged: finalResult.isPrivileged,
      confidence: finalResult.confidence,
      reasons: finalResult.reasons,
      keywords: finalResult.keywords,
      metadata: {
        keywordScore: keywordResult.score,
        patternScore: patternResult.score,
        aiScore: aiResult?.score || null,
        sensitivity
      }
    };

  } catch (error) {
    console.error(`Error detecting privilege in ${document.filePath}:`, error.message);
    throw error;
  }
}

/**
 * Analyze document for privilege keywords
 */
function analyzeKeywords(text) {
  const lowerText = text.toLowerCase();
  let score = 0;
  const foundKeywords = [];

  // Check high-priority keywords
  PRIVILEGE_KEYWORDS.high.forEach(keyword => {
    if (lowerText.includes(keyword.toLowerCase())) {
      score += 3;
      foundKeywords.push({ keyword, priority: 'high' });
    }
  });

  // Check medium-priority keywords
  PRIVILEGE_KEYWORDS.medium.forEach(keyword => {
    if (lowerText.includes(keyword.toLowerCase())) {
      score += 2;
      foundKeywords.push({ keyword, priority: 'medium' });
    }
  });

  // Check low-priority keywords
  PRIVILEGE_KEYWORDS.low.forEach(keyword => {
    if (lowerText.includes(keyword.toLowerCase())) {
      score += 1;
      foundKeywords.push({ keyword, priority: 'low' });
    }
  });

  // Calculate confidence
  const confidence = Math.min(score / 10, 1.0);

  return {
    score,
    confidence,
    keywords: foundKeywords
  };
}

/**
 * Analyze document patterns (email addresses, headers, etc.)
 */
function analyzePatterns(document) {
  let score = 0;
  const patterns = [];

  // Check for attorney email addresses
  ATTORNEY_PATTERNS.forEach(pattern => {
    const matches = document.text.match(pattern);
    if (matches) {
      score += 2;
      patterns.push({ type: 'attorney_email', value: matches[0] });
    }
  });

  // Check for privileged headers in emails
  const privilegedHeaders = [
    /^(subject|re):\s*privileged/im,
    /^(subject|re):\s*attorney-client/im,
    /^(subject|re):\s*confidential/im
  ];

  privilegedHeaders.forEach(headerPattern => {
    if (headerPattern.test(document.text)) {
      score += 3;
      patterns.push({ type: 'privileged_header', pattern: headerPattern.source });
    }
  });

  // Check for law firm letterhead indicators
  const letterheadPatterns = [
    /\b\w+\s*,\s*\w+\s*&\s*\w+\s*llp\b/i,
    /\b\w+\s*law\s*firm\b/i,
    /\battorneys?\s*at\s*law\b/i
  ];

  letterheadPatterns.forEach(pattern => {
    if (pattern.test(document.text)) {
      score += 2;
      patterns.push({ type: 'law_firm_letterhead', pattern: pattern.source });
    }
  });

  return {
    score,
    patterns
  };
}

/**
 * Analyze document with AI
 */
async function analyzeWithAI(text, provider = 'anthropic') {
  const prompt = `Analyze this document for attorney-client privilege or work product protection.

Consider:
1. Is this a communication between attorney and client?
2. Was legal advice sought or provided?
3. Is this work product prepared in anticipation of litigation?
4. Are there explicit privilege assertions?
5. Is the communication confidential?

Respond in JSON format:
{
  "isPrivileged": boolean,
  "confidence": number (0-1),
  "reasoning": "explanation",
  "privilegeType": "attorney-client" | "work-product" | "none"
}

Document excerpt (first 2000 chars):
${text.substring(0, 2000)}`;

  try {
    if (provider === 'anthropic') {
      const message = await anthropic.messages.create({
        model: 'claude-3-5-sonnet-20241022',
        max_tokens: 1000,
        messages: [{
          role: 'user',
          content: prompt
        }]
      });

      const response = JSON.parse(message.content[0].text);
      return {
        score: response.isPrivileged ? (response.confidence * 10) : 0,
        confidence: response.confidence,
        reasoning: response.reasoning,
        privilegeType: response.privilegeType
      };

    } else if (provider === 'openai') {
      const completion = await openai.chat.completions.create({
        model: 'gpt-4-turbo-preview',
        messages: [{
          role: 'user',
          content: prompt
        }],
        response_format: { type: 'json_object' }
      });

      const response = JSON.parse(completion.choices[0].message.content);
      return {
        score: response.isPrivileged ? (response.confidence * 10) : 0,
        confidence: response.confidence,
        reasoning: response.reasoning,
        privilegeType: response.privilegeType
      };
    }

  } catch (error) {
    console.error('AI analysis failed:', error.message);
    return null;
  }
}

/**
 * Aggregate all detection results
 */
function aggregateResults(keywordResult, patternResult, aiResult, sensitivity) {
  const weights = {
    low: { keyword: 0.3, pattern: 0.3, ai: 0.4 },
    medium: { keyword: 0.4, pattern: 0.3, ai: 0.3 },
    high: { keyword: 0.5, pattern: 0.3, ai: 0.2 }
  };

  const w = weights[sensitivity];

  // Calculate weighted confidence
  let totalConfidence = (keywordResult.confidence * w.keyword) +
                        (Math.min(patternResult.score / 10, 1.0) * w.pattern);

  if (aiResult) {
    totalConfidence += (aiResult.confidence * w.ai);
  } else {
    // Redistribute AI weight if not available
    totalConfidence = totalConfidence / (1 - w.ai);
  }

  // Determine if privileged based on sensitivity
  const thresholds = {
    low: 0.7,
    medium: 0.5,
    high: 0.3
  };

  const isPrivileged = totalConfidence >= thresholds[sensitivity];

  // Compile reasons
  const reasons = [];
  if (keywordResult.keywords.length > 0) {
    reasons.push(`Found ${keywordResult.keywords.length} privilege-related keywords`);
  }
  if (patternResult.patterns.length > 0) {
    reasons.push(`Matched ${patternResult.patterns.length} privilege patterns`);
  }
  if (aiResult?.reasoning) {
    reasons.push(`AI analysis: ${aiResult.reasoning}`);
  }

  return {
    isPrivileged,
    confidence: totalConfidence,
    reasons,
    keywords: keywordResult.keywords.map(k => k.keyword)
  };
}

/**
 * Main function
 */
async function main() {
  try {
    const args = parseArgs();
    const files = await loadDocumentList(args.files);

    console.log(`Checking ${files.length} documents for privilege...`);

    const results = {
      total: files.length,
      privileged_documents: [],
      non_privileged_documents: [],
      high_risk_documents: []
    };

    for (const file of files) {
      console.log(`Checking: ${file}`);

      // Load document
      const text = await fs.readFile(file, 'utf-8');
      const document = { filePath: file, text };

      // Detect privilege
      const result = await detectPrivilege(document, {
        sensitivity: args.sensitivity,
        provider: args.provider
      });

      if (result.isPrivileged) {
        results.privileged_documents.push(result);

        if (result.confidence > 0.8) {
          results.high_risk_documents.push(result);
        }
      } else {
        results.non_privileged_documents.push(result);
      }
    }

    // Save results
    await fs.writeFile(args.output, JSON.stringify(results, null, 2));

    console.log('✅ Privilege detection complete');
    console.log(`Privileged: ${results.privileged_documents.length}`);
    console.log(`High Risk: ${results.high_risk_documents.length}`);
    console.log(`Non-Privileged: ${results.non_privileged_documents.length}`);

  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

/**
 * Parse command-line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const parsed = {
    provider: 'anthropic',
    sensitivity: 'medium',
    files: 'changed-files.txt',
    output: 'privilege-results.json'
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--provider') parsed.provider = args[++i];
    if (args[i] === '--sensitivity') parsed.sensitivity = args[++i];
    if (args[i] === '--files') parsed.files = args[++i];
    if (args[i] === '--output') parsed.output = args[++i];
  }

  return parsed;
}

/**
 * Load document list from file
 */
async function loadDocumentList(filePath) {
  const content = await fs.readFile(filePath, 'utf-8');
  return content.split('\n').filter(line => line.trim());
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { detectPrivilege, analyzeKeywords, analyzePatterns };
