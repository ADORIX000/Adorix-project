/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/ws',
        destination: 'http://127.0.0.1:8001/ws',
      },
      {
        source: '/ads/:path*',
        destination: 'http://127.0.0.1:8001/ads/:path*',
      },
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8001/api/:path*',
      },
    ];
  },
};

export default nextConfig;
