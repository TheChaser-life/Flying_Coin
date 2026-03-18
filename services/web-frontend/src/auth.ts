import NextAuth from "next-auth"
import Keycloak from "next-auth/providers/keycloak"

async function refreshAccessToken(token: any) {
  try {
    const url = `${process.env.AUTH_KEYCLOAK_ISSUER}/protocol/openid-connect/token`
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: process.env.AUTH_KEYCLOAK_ID!,
        client_secret: process.env.AUTH_KEYCLOAK_SECRET!,
        grant_type: "refresh_token",
        refresh_token: token.refreshToken,
      }),
    })

    const refreshedTokens = await response.json()

    if (!response.ok) {
      throw refreshedTokens
    }

    console.log("[Auth] Token refreshed successfully")
    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      expiresAt: Math.floor(Date.now() / 1000 + refreshedTokens.expires_in),
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken, // Fall back to old refresh token
    }
  } catch (error) {
    console.error("[Auth] Error refreshing access token:", error)
    return {
      ...token,
      error: "RefreshAccessTokenError",
    }
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Keycloak({
      clientId: process.env.AUTH_KEYCLOAK_ID,
      clientSecret: process.env.AUTH_KEYCLOAK_SECRET,
      issuer: process.env.AUTH_KEYCLOAK_ISSUER,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // Initial sign in
      if (account) {
        console.log("[Auth] Initial sign in, storing tokens")
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          expiresAt: account.expires_at ?? Math.floor(Date.now() / 1000 + (account.expires_in ?? 0)),
        }
      }

      // Return previous token if the access token has not expired yet
      // We refresh 30 seconds before it actually expires to be safe
      if (Date.now() < (token.expiresAt as number) * 1000 - 30000) {
        return token
      }

      // Access token has expired, try to update it
      console.log("[Auth] Token expired/expiring, attempting refresh")
      return refreshAccessToken(token)
    },
    async session({ session, token }: any) {
      session.accessToken = token.accessToken
      session.error = token.error
      return session
    },
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user
      const isApiAuthRoute = nextUrl.pathname.startsWith("/api/auth")
      const isPublicRoute = nextUrl.pathname === "/" || nextUrl.pathname.startsWith("/public")

      if (isApiAuthRoute || isPublicRoute) return true
      return isLoggedIn
    },
  },
})
