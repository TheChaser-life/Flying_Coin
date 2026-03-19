import { auth } from "@/auth"
import { redirect } from "next/navigation"
import { SignOut } from "@/components/user-auth"
import { Button } from "@/components/ui/button"
import Link from "next/link"
import { Providers } from "@/components/providers"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  
  // If no session or token refresh failed, redirect to login
  if (!session || (session as any).error === "RefreshAccessTokenError") {
    redirect("/")
  }

  const navItems = [
    { label: "Dashboard", href: "/dashboard" },
    { label: "Analysis", href: "/analysis" },
    { label: "Forecast", href: "/forecast" },
    { label: "Sentiment", href: "/sentiment" },
    { label: "Portfolio", href: "/portfolio" },
    { label: "Backtesting", href: "/backtesting" },
  ]

  return (
    <Providers session={session}>
      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container flex h-14 items-center justify-between">
            <div className="flex items-center gap-6 md:gap-10">
              <Link className="flex items-center space-x-2" href="/">
                <span className="inline-block font-bold">Flying Coin</span>
              </Link>
              <nav className="hidden gap-6 md:flex">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    className="text-sm font-medium hover:text-primary transition-colors"
                    href={item.href}
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground hidden sm:inline-block">
                {session.user?.email}
              </span>
              <SignOut size="sm" variant="outline" />
            </div>
          </div>
        </header>
        <main className="flex-1 container py-6">{children}</main>
      </div>
    </Providers>
  )
}
