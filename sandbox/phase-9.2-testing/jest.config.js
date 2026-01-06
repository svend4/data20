/**
 * Jest Configuration - Phase 9.2 Testing
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.test.js',
    '**/__tests__/**/*.spec.js'
  ],

  // Coverage configuration
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],

  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/scripts/',
    '/__tests__/',
    '/public/'
  ],

  // Coverage thresholds (Phase 9.2 goal: 78% overall)
  coverageThresholds: {
    global: {
      branches: 70,
      functions: 75,
      lines: 78,
      statements: 78
    }
  },

  // Module paths
  moduleDirectories: ['node_modules', 'src'],

  // Transform files
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/__tests__/setup.js'],

  // Module name mapper for webpack aliases
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1'
  },

  // Globals for Chrome extension API mocking
  globals: {
    chrome: {}
  },

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,
  resetMocks: true,
  restoreMocks: true
};
