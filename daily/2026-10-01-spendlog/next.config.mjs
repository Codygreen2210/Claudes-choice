/** @type {import("next").NextConfig} */
export default {
  async rewrites() {
    return [
      { source: '/.well-known/oauth-protected-resource', destination: '/api/oauth/prm' },
      { source: '/.well-known/oauth-protected-resource/:path*', destination: '/api/oauth/prm' },
      { source: '/.well-known/oauth-authorization-server', destination: '/api/oauth/meta' },
      { source: '/.well-known/oauth-authorization-server/:path*', destination: '/api/oauth/meta' },
      { source: '/.well-known/openid-configuration', destination: '/api/oauth/meta' },
    ];
  },
};
