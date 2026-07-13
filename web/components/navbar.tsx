"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Home" },
  { href: "/app", label: "Console" },
  { href: "/evals", label: "Evals" },
];

export function Navbar() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-ink-base/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="font-display text-xl tracking-tight text-white">
          FactoryPulse
        </Link>
        <nav className="flex items-center gap-1 rounded-full border border-white/[0.06] bg-ink-surface p-1">
          {links.map((l) => {
            const active = pathname === l.href;
            return (
              <Link
                key={l.href}
                href={l.href}
                className={`rounded-full px-4 py-1.5 text-sm transition ${
                  active ? "bg-accent text-black" : "text-zinc-400 hover:text-white"
                }`}
              >
                {l.label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
