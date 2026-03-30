// AI processing utilities
// Uses on-device heuristics + optional API calls for deeper analysis

export interface AiAnalysis {
  summary: string;
  sentiment: 'positive' | 'neutral' | 'negative' | 'urgent';
  priority: 'low' | 'medium' | 'high' | 'critical';
  suggestedTags: string[];
  suggestedCategory: string;
}

// Keyword-based local analysis (works offline, zero latency)
const URGENCY_KEYWORDS = [
  'urgent', 'emergency', 'critical', 'danger', 'hazard', 'broken',
  'failing', 'contaminated', 'injured', 'collapsed', 'flood', 'fire',
  'outbreak', 'shortage', 'blocked', 'destroyed', 'severe'
];

const CATEGORY_PATTERNS: Record<string, string[]> = {
  'Infrastructure': ['road', 'bridge', 'building', 'power', 'water', 'pipe', 'electrical', 'structure', 'construction', 'dam'],
  'Health': ['patient', 'symptom', 'disease', 'medical', 'hospital', 'clinic', 'treatment', 'infection', 'vaccine', 'health'],
  'Environment': ['soil', 'water quality', 'air', 'pollution', 'wildlife', 'vegetation', 'climate', 'deforestation', 'erosion', 'species'],
  'Agriculture': ['crop', 'harvest', 'livestock', 'farm', 'irrigation', 'yield', 'seed', 'pest', 'fertilizer', 'drought'],
  'Community': ['meeting', 'survey', 'interview', 'feedback', 'population', 'household', 'school', 'market', 'transport'],
  'Safety': ['incident', 'accident', 'crime', 'theft', 'violence', 'conflict', 'risk', 'warning', 'evacuation'],
};

const SENTIMENT_POSITIVE = ['good', 'improved', 'positive', 'success', 'excellent', 'progress', 'stable', 'resolved', 'recovered', 'thriving'];
const SENTIMENT_NEGATIVE = ['bad', 'worse', 'decline', 'failed', 'poor', 'damaged', 'deteriorated', 'insufficient', 'lacking'];

export function analyzeLocally(title: string, content: string): AiAnalysis {
  const text = `${title} ${content}`.toLowerCase();
  const words = text.split(/\s+/);

  // Detect priority
  const urgencyHits = URGENCY_KEYWORDS.filter(k => text.includes(k));
  let priority: AiAnalysis['priority'] = 'low';
  if (urgencyHits.length >= 3) priority = 'critical';
  else if (urgencyHits.length >= 2) priority = 'high';
  else if (urgencyHits.length >= 1) priority = 'medium';

  // Detect sentiment
  const posHits = SENTIMENT_POSITIVE.filter(k => text.includes(k)).length;
  const negHits = SENTIMENT_NEGATIVE.filter(k => text.includes(k)).length;
  let sentiment: AiAnalysis['sentiment'] = 'neutral';
  if (urgencyHits.length >= 2) sentiment = 'urgent';
  else if (posHits > negHits) sentiment = 'positive';
  else if (negHits > posHits) sentiment = 'negative';

  // Detect category
  let bestCategory = 'General';
  let bestScore = 0;
  for (const [cat, keywords] of Object.entries(CATEGORY_PATTERNS)) {
    const score = keywords.filter(k => text.includes(k)).length;
    if (score > bestScore) {
      bestScore = score;
      bestCategory = cat;
    }
  }

  // Extract tags (significant words that aren't common)
  const stopWords = new Set(['the', 'a', 'an', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'not', 'with', 'this', 'that', 'it', 'be', 'has', 'had', 'have', 'from', 'by', 'as']);
  const tagCandidates = words
    .filter(w => w.length > 3 && !stopWords.has(w))
    .reduce((acc, w) => { acc[w] = (acc[w] || 0) + 1; return acc; }, {} as Record<string, number>);

  const suggestedTags = Object.entries(tagCandidates)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([tag]) => tag);

  // Generate summary
  const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 10);
  const summary = sentences.length > 0
    ? sentences.slice(0, 2).map(s => s.trim()).join('. ') + '.'
    : content.slice(0, 150) + (content.length > 150 ? '...' : '');

  return {
    summary,
    sentiment,
    priority,
    suggestedTags,
    suggestedCategory: bestCategory,
  };
}

// Optional: Cloud AI enhancement (when online)
export async function analyzeWithApi(title: string, content: string, apiKey?: string): Promise<AiAnalysis | null> {
  if (!apiKey) return null;

  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        messages: [
          {
            role: 'system',
            content: 'You are a field research analyst. Analyze the following field observation and return a JSON object with: summary (2 sentences max), sentiment (positive|neutral|negative|urgent), priority (low|medium|high|critical), suggestedTags (array of 3-5 keywords), suggestedCategory (one of: Infrastructure, Health, Environment, Agriculture, Community, Safety, General). Return ONLY valid JSON.'
          },
          {
            role: 'user',
            content: `Title: ${title}\n\nObservation: ${content}`
          }
        ],
        temperature: 0.3,
        max_tokens: 300,
      }),
    });

    if (!response.ok) return null;

    const data = await response.json();
    const result = JSON.parse(data.choices[0].message.content);
    return result as AiAnalysis;
  } catch {
    return null;
  }
}
