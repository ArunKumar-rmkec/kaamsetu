const origin = process.env.API_ORIGIN || "http://127.0.0.1:8421";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${origin}/api/:path*` }];
  },
};

module.exports = nextConfig;
