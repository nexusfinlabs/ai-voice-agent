import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: "/nucleo",
  output: "export",      // genera carpeta out/ con HTML/CSS/JS estáticos
  trailingSlash: true,  // /nucleo/ en vez de /nucleo (necesario para Tailscale)
  images: {
    unoptimized: true,  // obligatorio para export estático
  },
};

export default nextConfig;
