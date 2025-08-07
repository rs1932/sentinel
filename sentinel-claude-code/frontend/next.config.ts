import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Optimize for better client-side navigation
  experimental: {
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons'],
  },
  // Enable static optimization where possible
  trailingSlash: false,
  // Improve loading performance
  poweredByHeader: false,
};

export default nextConfig;
