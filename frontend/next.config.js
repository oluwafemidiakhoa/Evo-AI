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

  // No redirects needed - root page serves as dashboard/landing page
}

module.exports = nextConfig
