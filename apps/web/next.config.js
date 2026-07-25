/** @type {import('next').NextConfig} */
const nextConfig = {
  transpilePackages: ["@transparencia/ui", "@transparencia/db"],
  serverExternalPackages: ["pg", "kysely"],
};

module.exports = nextConfig;
