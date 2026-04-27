/** @type {import('next').NextConfig} */
const nextConfig = {
  // Use standalone output for Docker; Netlify sets NETLIFY=true automatically
  output: process.env.NETLIFY ? undefined : 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
