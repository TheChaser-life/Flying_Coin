import { auth } from "@/auth"
import { SignIn, SignOut } from "@/components/user-auth"
import { Button } from "@/components/ui/button"

export default async function Home() {
  const session = await auth()

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gradient-to-br from-background to-accent/20">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          Flying Coin&nbsp;
          <code className="font-bold">v2.1</code>
        </p>
      </div>

      <div className="relative flex flex-col items-center text-center space-y-8 mt-24">
        <h1 className="text-6xl font-extrabold tracking-tighter sm:text-7xl md:text-8xl bg-clip-text text-transparent bg-gradient-to-r from-primary to-primary/50">
          Future of Finance
        </h1>
        <p className="max-w-[700px] text-lg text-muted-foreground sm:text-xl">
          Advanced analytics, real-time market insights, and powerful backtesting tools. Join the elite group of traders.
        </p>

        <div className="flex gap-4 mt-8">
          {session ? (
            <div className="flex flex-col items-center gap-4">
              <p className="text-secondary-foreground">Welcome back, <span className="font-bold text-primary">{session.user?.name || session.user?.email}</span></p>
              <div className="flex gap-4">
                <Button asChild size="lg">
                  <a href="/dashboard">Go to Dashboard</a>
                </Button>
                <SignOut />
              </div>
            </div>
          ) : (
            <>
              <SignIn provider="keycloak" size="lg" className="px-12 py-6 text-lg" />
              <Button variant="outline" size="lg" className="px-12 py-6 text-lg">
                Explore Market
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="mt-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-4 lg:text-left">
        <a
          href="/analysis"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        >
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Analysis{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className={`m-0 max-w-[30ch] text-sm opacity-50`}>
            Real-time candlestick charts and technical indicators.
          </p>
        </a>

        <a
          href="/dashboard"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        >
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Dashboard{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className={`m-0 max-w-[30ch] text-sm opacity-50`}>
            Monitor your portfolio and market summaries.
          </p>
        </a>

        <a
          href="/backtesting"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        >
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Backtesting{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className={`m-0 max-w-[30ch] text-sm opacity-50`}>
            Test your strategies with historical market data.
          </p>
        </a>

        <a
          href="/docs"
          className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-300 hover:bg-gray-100 hover:dark:border-neutral-700 hover:dark:bg-neutral-800/30"
        >
          <h2 className={`mb-3 text-2xl font-semibold`}>
            Docs{" "}
            <span className="inline-block transition-transform group-hover:translate-x-1 motion-reduce:transform-none">
              -&gt;
            </span>
          </h2>
          <p className={`m-0 max-w-[30ch] text-sm opacity-50`}>
            Learn how to use the platform effectively.
          </p>
        </a>
      </div>
    </main>
  )
}
