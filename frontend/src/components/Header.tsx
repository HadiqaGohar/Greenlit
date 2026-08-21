import Link from "next/link";

export function Header() {
  return (
    <header className="border-b border-charcoal-light/60 bg-charcoal/80 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="group flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded border border-amber/40 bg-charcoal-light text-lg">
            🎬
          </span>
          <div>
            <p className="font-display text-lg font-semibold tracking-wide text-parchment transition-colors group-hover:text-amber">
              GreenLit AI
            </p>
            <p className="text-xs text-parchment/50">
              Production research, before the cameras roll
            </p>
          </div>
        </Link>
      </div>
    </header>
  );
}
