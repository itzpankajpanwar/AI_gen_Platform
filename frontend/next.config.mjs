/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  // Proxy API calls through the Next server so the browser only needs port 3200;
  // the FastAPI backend stays private on localhost:8200.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8200/api/:path*" },
    ];
  },
};

export default nextConfig;
