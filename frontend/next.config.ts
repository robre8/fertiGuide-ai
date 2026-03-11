import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // @xenova/transformers ships WASM + workers that Turbopack can't handle.
  // serverExternalPackages keeps it out of the server bundle;
  // webpack config keeps it out of the client bundle (loaded via CDN/dynamic import).
  serverExternalPackages: ["@xenova/transformers", "onnxruntime-node"],
  webpack: (config, { isServer }) => {
    if (!isServer) {
      // Tell webpack not to bundle these — they'll be loaded at runtime
      config.resolve = config.resolve ?? {};
      config.resolve.alias = {
        ...config.resolve.alias,
        sharp$: false,
        "onnxruntime-node$": false,
      };
    }
    return config;
  },
};

export default nextConfig;
