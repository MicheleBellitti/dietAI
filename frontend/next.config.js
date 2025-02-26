// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
    async rewrites() {
      return [
        {
          source: '/api/',
          destination: 'http://localhost:5000/api/', // Adjust to your Flask server URL
        },
      ];
    },
  };
  
  module.exports = nextConfig;