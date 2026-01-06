/**
 * Pyodide Web Worker
 * Phase 8.1.5: WebAssembly Tools (Pyodide Integration)
 *
 * Web worker for running Python code via Pyodide (Python compiled to WebAssembly).
 * Runs Python code in a separate thread to avoid blocking the UI.
 *
 * This worker:
 * - Loads Pyodide runtime (Python in WebAssembly)
 * - Executes Python code from tools
 * - Handles package installation
 * - Returns results to main thread
 */

// Pyodide CDN URL (version 0.24.1)
const PYODIDE_CDN = 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js';

let pyodideInstance = null;
let isInitialized = false;
let initializationPromise = null;

/**
 * Initialize Pyodide
 * Loads the Pyodide runtime and Python standard library
 */
async function initializePyodide() {
  if (isInitialized && pyodideInstance) {
    return pyodideInstance;
  }

  if (initializationPromise) {
    return initializationPromise;
  }

  initializationPromise = (async () => {
    try {
      console.log('[Pyodide Worker] Loading Pyodide...');

      // Import Pyodide from CDN
      importScripts(PYODIDE_CDN);

      // Load Pyodide
      pyodideInstance = await loadPyodide({
        indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/',
      });

      console.log('[Pyodide Worker] Pyodide loaded successfully');

      // Load commonly used packages
      await pyodideInstance.loadPackage(['micropip', 're', 'json']);

      isInitialized = true;
      console.log('[Pyodide Worker] Pyodide initialized successfully');

      return pyodideInstance;
    } catch (error) {
      console.error('[Pyodide Worker] Failed to initialize Pyodide:', error);
      initializationPromise = null;
      throw error;
    }
  })();

  return initializationPromise;
}

/**
 * Execute Python code
 */
async function executePython(code, context = {}) {
  const pyodide = await initializePyodide();

  try {
    // Set context variables in Python globals
    for (const [key, value] of Object.entries(context)) {
      pyodide.globals.set(key, value);
    }

    // Run Python code
    const result = await pyodide.runPythonAsync(code);

    // Convert result to JavaScript
    let jsResult;
    if (result && result.toJs) {
      jsResult = result.toJs({ dict_converter: Object.fromEntries });
    } else {
      jsResult = result;
    }

    return {
      success: true,
      result: jsResult,
    };
  } catch (error) {
    console.error('[Pyodide Worker] Python execution error:', error);
    return {
      success: false,
      error: error.message || String(error),
      stack: error.stack,
    };
  }
}

/**
 * Install Python packages
 */
async function installPackages(packages) {
  const pyodide = await initializePyodide();

  try {
    console.log(`[Pyodide Worker] Installing packages: ${packages.join(', ')}`);

    for (const pkg of packages) {
      await pyodide.loadPackage(pkg);
    }

    console.log('[Pyodide Worker] Packages installed successfully');

    return {
      success: true,
      installed: packages,
    };
  } catch (error) {
    console.error('[Pyodide Worker] Package installation failed:', error);
    return {
      success: false,
      error: error.message || String(error),
    };
  }
}

/**
 * Execute a tool function
 * Tools are Python functions that process data
 */
async function executeTool(toolCode, functionName, parameters) {
  const pyodide = await initializePyodide();

  try {
    console.log(`[Pyodide Worker] Executing tool: ${functionName}`);

    // Load the tool code
    await pyodide.runPythonAsync(toolCode);

    // Prepare parameters as JSON
    const paramsJson = JSON.stringify(parameters);

    // Execute the tool function
    const pythonCode = `
import json

# Parse parameters
params = json.loads('''${paramsJson}''')

# Execute tool function
result = ${functionName}(**params)

# Convert result to JSON
json.dumps(result, ensure_ascii=False)
`;

    const resultJson = await pyodide.runPythonAsync(pythonCode);
    const result = JSON.parse(resultJson);

    return {
      success: true,
      result,
    };
  } catch (error) {
    console.error(`[Pyodide Worker] Tool execution failed (${functionName}):`, error);
    return {
      success: false,
      error: error.message || String(error),
      stack: error.stack,
    };
  }
}

/**
 * Get Pyodide version and status
 */
async function getStatus() {
  if (!isInitialized) {
    return {
      initialized: false,
      version: null,
    };
  }

  const pyodide = await initializePyodide();

  return {
    initialized: true,
    version: pyodide.version,
    loadedPackages: pyodide.loadedPackages,
  };
}

/**
 * Message handler
 * Handles messages from the main thread
 */
self.onmessage = async function (event) {
  const { id, type, data } = event.data;

  try {
    let result;

    switch (type) {
      case 'INIT':
        await initializePyodide();
        result = { success: true };
        break;

      case 'EXECUTE':
        result = await executePython(data.code, data.context);
        break;

      case 'EXECUTE_TOOL':
        result = await executeTool(data.toolCode, data.functionName, data.parameters);
        break;

      case 'INSTALL_PACKAGES':
        result = await installPackages(data.packages);
        break;

      case 'GET_STATUS':
        result = await getStatus();
        break;

      default:
        result = {
          success: false,
          error: `Unknown message type: ${type}`,
        };
    }

    // Send result back to main thread
    self.postMessage({
      id,
      type: 'RESULT',
      result,
    });
  } catch (error) {
    // Send error back to main thread
    self.postMessage({
      id,
      type: 'ERROR',
      error: {
        message: error.message || String(error),
        stack: error.stack,
      },
    });
  }
};

console.log('[Pyodide Worker] Worker loaded and ready');
