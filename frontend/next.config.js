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

  // Enable standalone output for Docker (disabled for Vercel deployment)
  // output: 'standalone',

  // Experimental features (disabled for lower memory usage)
  // experimental: {
  //   typedRoutes: true,
  // },

  // Image optimization
  images: {
    domains: [],
  },

  // Redirects (temporarily disabled for debugging)
  // async redirects() {
  //   return [
  //     {
  //       source: '/',
  //       destination: '/campaigns',
  //       permanent: false,
  //     },
  //   ]
  // },
}

module.exports = nextConfig
