/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,

  // Temporarily disable type checking and linting during build for quick deployment
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },

  // Environment variables exposed to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },

  // Experimental features
  experimental: {
    typedRoutes: true,
  },

  // Image optimization
  images: {
    domains: [],
  },

  // Redirects
  async redirects() {
    return [
      {
        source: '/',
        destination: '/campaigns',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig
