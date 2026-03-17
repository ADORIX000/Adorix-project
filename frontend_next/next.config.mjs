/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/ws',
        destination: 'http://localhost:8002/ws',
      },
      {
        source: '/ads/:path*',
        destination: 'http://localhost:8002/ads/:path*',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8002/api/:path*',
      },
    ];
  },
};

export default nextConfig;
