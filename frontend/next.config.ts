// frontend/next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  eslint: {
    // 🚀 не зупиняти білд через ESLint помилки
    ignoreDuringBuilds: true,
  },
  typescript: {
    // 🚀 не зупиняти білд через TypeScript помилки
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
