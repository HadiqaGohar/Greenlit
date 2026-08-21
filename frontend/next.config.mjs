/** @type {import('next').NextConfig} */
const nextConfig = {
  // Reduce timeout for Google Fonts to fail faster
  experimental: {
    optimizePackageImports: ['next-themes'],
  },
  // Handle network issues more gracefully
  headers: async () => {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
