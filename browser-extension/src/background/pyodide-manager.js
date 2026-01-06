/**
 * Pyodide Manager
 * Phase 9.1.2: Pyodide Integration
 *
 * Manages Python runtime via Pyodide (WebAssembly)
 */

const PYODIDE_VERSION = '0.25.0';
const PYODIDE_CDN = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

export class PyodideManager {
  constructor() {
    this.pyodide = null;
    this.isLoaded = false;
    this.loadingPromise = null;
    this.installedPackages = new Set();
  }

  /**
   * Initialize Pyodide
   */
  async initialize() {
    if (this.loadingPromise) {
      return this.loadingPromise;
    }

    this.loadingPromise = this._loadPyodide();
    return this.loadingPromise;
  }

  /**
   * Load Pyodide from CDN
   */
  async _loadPyodide() {
    try {
      console.log('Loading Pyodide from CDN...');

      // Import Pyodide loader
      const pyodideScript = document.createElement('script');
      pyodideScript.src = `${PYODIDE_CDN}pyodide.js`;

      await new Promise((resolve, reject) => {
        pyodideScript.onload = resolve;
        pyodideScript.onerror = reject;
        document.head.appendChild(pyodideScript);
      });

      // Load Pyodide
      this.pyodide = await loadPyodide({
        indexURL: PYODIDE_CDN
      });

      console.log('✅ Pyodide loaded');

      // Install core packages
      await this.installCorePackages();

      this.isLoaded = true;
      return this.pyodide;

    } catch (error) {
      console.error('Failed to load Pyodide:', error);
      throw error;
    }
  }

  /**
   * Install core Python packages
   */
  async installCorePackages() {
    const corePackages = [
      'micropip',
      'regex',
      'pyyaml'
    ];

    console.log('Installing core packages:', corePackages);

    try {
      await this.pyodide.loadPackage('micropip');

      const micropip = this.pyodide.pyimport('micropip');

      for (const pkg of corePackages) {
        if (pkg !== 'micropip') {
          try {
            await micropip.install(pkg);
            this.installedPackages.add(pkg);
            console.log(`  ✅ Installed ${pkg}`);
          } catch (error) {
            console.warn(`  ⚠️  Failed to install ${pkg}:`, error.message);
          }
        }
      }

      console.log('✅ Core packages installed');

    } catch (error) {
      console.error('Failed to install core packages:', error);
      throw error;
    }
  }

  /**
   * Install optional packages
   */
  async installPackage(packageName) {
    if (this.installedPackages.has(packageName)) {
      return; // Already installed
    }

    try {
      const micropip = this.pyodide.pyimport('micropip');
      await micropip.install(packageName);
      this.installedPackages.add(packageName);
      console.log(`✅ Installed ${packageName}`);
    } catch (error) {
      console.error(`Failed to install ${packageName}:`, error);
      throw error;
    }
  }

  /**
   * Run Python code
   */
  async runPython(code) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    try {
      const result = await this.pyodide.runPythonAsync(code);
      return result;
    } catch (error) {
      console.error('Python execution error:', error);
      throw error;
    }
  }

  /**
   * Run Python function
   */
  async runPythonFunction(funcName, args = []) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    try {
      // Convert args to Python
      const pyArgs = args.map(arg => this.pyodide.toPy(arg));

      // Get function from globals
      const func = this.pyodide.globals.get(funcName);

      if (!func) {
        throw new Error(`Function ${funcName} not found`);
      }

      // Call function
      const result = await func(...pyArgs);

      // Convert result to JS
      return result.toJs ? result.toJs() : result;

    } catch (error) {
      console.error(`Failed to run ${funcName}:`, error);
      throw error;
    }
  }

  /**
   * Load Python module from string
   */
  async loadModule(moduleName, moduleCode) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    try {
      // Create module in Pyodide filesystem
      this.pyodide.FS.writeFile(`${moduleName}.py`, moduleCode);

      // Import module
      await this.pyodide.runPythonAsync(`import ${moduleName}`);

      console.log(`✅ Loaded module: ${moduleName}`);

    } catch (error) {
      console.error(`Failed to load module ${moduleName}:`, error);
      throw error;
    }
  }

  /**
   * Evaluate Python expression
   */
  async eval(expression) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    try {
      const result = await this.pyodide.runPythonAsync(expression);
      return result.toJs ? result.toJs() : result;
    } catch (error) {
      console.error('Eval error:', error);
      throw error;
    }
  }

  /**
   * Get Python variable
   */
  getVariable(name) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    const value = this.pyodide.globals.get(name);
    return value ? (value.toJs ? value.toJs() : value) : undefined;
  }

  /**
   * Set Python variable
   */
  setVariable(name, value) {
    if (!this.isLoaded) {
      throw new Error('Pyodide not loaded');
    }

    this.pyodide.globals.set(name, this.pyodide.toPy(value));
  }

  /**
   * Check if package is installed
   */
  isPackageInstalled(packageName) {
    return this.installedPackages.has(packageName);
  }

  /**
   * Get Pyodide version
   */
  getVersion() {
    return PYODIDE_VERSION;
  }

  /**
   * Get memory usage
   */
  getMemoryUsage() {
    if (!this.isLoaded) {
      return null;
    }

    try {
      // Pyodide memory stats
      return {
        heapSize: this.pyodide._module.HEAP8.length,
        heapUsed: this.pyodide._module.HEAP8.byteLength
      };
    } catch (error) {
      return null;
    }
  }

  /**
   * Clear Python globals (garbage collection)
   */
  clearGlobals() {
    if (!this.isLoaded) {
      return;
    }

    try {
      this.pyodide.runPython(`
import gc
# Clear user-defined variables
user_vars = [v for v in dir() if not v.startswith('_')]
for v in user_vars:
    try:
        del globals()[v]
    except:
        pass
gc.collect()
`);
      console.log('✅ Python globals cleared');
    } catch (error) {
      console.error('Failed to clear globals:', error);
    }
  }

  /**
   * Destroy Pyodide instance
   */
  destroy() {
    if (this.pyodide) {
      // Clean up
      this.clearGlobals();
      this.pyodide = null;
      this.isLoaded = false;
      this.installedPackages.clear();
      console.log('✅ Pyodide destroyed');
    }
  }
}

export default PyodideManager;
