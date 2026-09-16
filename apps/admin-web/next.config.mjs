/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // react-leaflet's MapContainer doesn't clean up Leaflet's internal DOM marker
  // fast enough for React 18 Strict Mode's dev-only double-invoke of effects,
  // which throws "Map container is already initialized". Strict Mode has no
  // effect on production builds, so this only changes local dev behavior.
  reactStrictMode: false,
  images: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "**",
      },
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
};

export default nextConfig;
