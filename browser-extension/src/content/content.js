/**
 * Content Script
 * Phase 9.1.5: Browser Context Menus & Actions
 *
 * Runs on all pages, extracts content and communicates with background
 */

console.log('Data20 content script loaded');

/**
 * Extract page content
 */
function extractPageContent() {
  const content = {
    title: document.title,
    url: window.location.href,
    text: extractText(),
    metadata: extractMetadata(),
    timestamp: new Date().toISOString()
  };

  return content;
}

/**
 * Extract text from page
 */
function extractText() {
  // Remove script and style elements
  const clone = document.body.cloneNode(true);
  const scripts = clone.querySelectorAll('script, style, noscript');
  scripts.forEach(el => el.remove());

  // Get text content
  let text = clone.textContent || clone.innerText || '';

  // Clean up whitespace
  text = text
    .replace(/\s+/g, ' ')
    .trim();

  return text;
}

/**
 * Extract metadata from page
 */
function extractMetadata() {
  const metadata = {
    description: '',
    keywords: [],
    author: '',
    published: '',
    image: ''
  };

  // Description
  const descMeta = document.querySelector('meta[name="description"], meta[property="og:description"]');
  if (descMeta) {
    metadata.description = descMeta.content;
  }

  // Keywords
  const keywordsMeta = document.querySelector('meta[name="keywords"]');
  if (keywordsMeta) {
    metadata.keywords = keywordsMeta.content.split(',').map(k => k.trim());
  }

  // Author
  const authorMeta = document.querySelector('meta[name="author"]');
  if (authorMeta) {
    metadata.author = authorMeta.content;
  }

  // Published date
  const publishedMeta = document.querySelector('meta[property="article:published_time"]');
  if (publishedMeta) {
    metadata.published = publishedMeta.content;
  }

  // Image
  const imageMeta = document.querySelector('meta[property="og:image"]');
  if (imageMeta) {
    metadata.image = imageMeta.content;
  }

  return metadata;
}

/**
 * Highlight selected text
 */
function highlightSelection(color = 'yellow') {
  const selection = window.getSelection();

  if (selection.rangeCount > 0) {
    const range = selection.getRangeAt(0);
    const span = document.createElement('span');
    span.style.backgroundColor = color;
    span.style.padding = '2px';

    try {
      range.surroundContents(span);
    } catch (error) {
      console.warn('Failed to highlight selection:', error);
    }
  }
}

/**
 * Create floating button
 */
function createFloatingButton() {
  const button = document.createElement('div');
  button.id = 'data20-floating-btn';
  button.innerHTML = '📊';
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-size: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 10000;
    transition: transform 0.2s;
  `;

  button.addEventListener('click', () => {
    // Send message to background to analyze page
    const content = extractPageContent();

    chrome.runtime.sendMessage({
      type: 'PAGE_CONTENT_EXTRACTED',
      content: content
    }, (response) => {
      if (response && response.success) {
        showAnalysisResults(response.result);
      }
    });
  });

  button.addEventListener('mouseenter', () => {
    button.style.transform = 'scale(1.1)';
  });

  button.addEventListener('mouseleave', () => {
    button.style.transform = 'scale(1)';
  });

  document.body.appendChild(button);
}

/**
 * Show analysis results
 */
function showAnalysisResults(results) {
  const overlay = document.createElement('div');
  overlay.id = 'data20-results-overlay';
  overlay.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    z-index: 10001;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  `;

  const modal = document.createElement('div');
  modal.style.cssText = `
    background: white;
    border-radius: 12px;
    padding: 30px;
    max-width: 600px;
    max-height: 80vh;
    overflow-y: auto;
    color: #333;
  `;

  modal.innerHTML = `
    <h2 style="margin-top: 0; color: #667eea;">Page Analysis Results</h2>

    <div style="margin: 20px 0;">
      <h3>Reading Time</h3>
      <p>${results.readingTime.reading_time_minutes} minutes (${results.readingTime.word_count} words)</p>
    </div>

    <div style="margin: 20px 0;">
      <h3>Language</h3>
      <p>${results.language.language} (${Math.round(results.language.confidence * 100)}% confidence)</p>
    </div>

    <div style="margin: 20px 0;">
      <h3>Keywords</h3>
      <p>${results.keywords.keywords.join(', ')}</p>
    </div>

    <div style="margin: 20px 0;">
      <h3>Word Statistics</h3>
      <p>Total words: ${results.wordCount.total_words}</p>
      <p>Unique words: ${results.wordCount.unique_words}</p>
    </div>

    <button id="close-results" style="
      padding: 10px 20px;
      background: #667eea;
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 16px;
    ">Close</button>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  // Close button
  document.getElementById('close-results').addEventListener('click', () => {
    overlay.remove();
  });

  // Close on overlay click
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      overlay.remove();
    }
  });
}

/**
 * Listen for messages from background
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('Content script received message:', message.type);

  switch (message.type) {
    case 'EXTRACT_PAGE_CONTENT':
      const content = extractPageContent();
      sendResponse(content);
      break;

    case 'HIGHLIGHT_SELECTION':
      highlightSelection(message.color);
      sendResponse({ success: true });
      break;

    default:
      sendResponse({ success: false, error: 'Unknown message type' });
  }

  return true; // Async response
});

// Add floating button on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createFloatingButton);
} else {
  createFloatingButton();
}

console.log('✅ Data20 content script ready');
