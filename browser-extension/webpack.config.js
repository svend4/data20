const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  mode: process.env.NODE_ENV || 'development',
  entry: {
    background: './src/background/background.js',
    popup: './src/popup/popup.js',
    content: './src/content/content.js'
  },
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].js',
    clean: true
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: ['@babel/preset-env']
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      }
    ]
  },
  plugins: [
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'public',
          to: 'public'
        }
      ]
    })
  ],
  resolve: {
    extensions: ['.js'],
    fallback: {
      "fs": false,
      "path": false,
      "os": false
    }
  },
  devtool: 'source-map',
  optimization: {
    minimize: process.env.NODE_ENV === 'production'
  }
};
