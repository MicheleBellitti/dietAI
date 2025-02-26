module.exports = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:5000/api/:path*',  // Proxy API requests to Flask backend
      },
    ];
  },
};
