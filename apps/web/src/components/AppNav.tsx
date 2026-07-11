"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Főoldal" },
  { href: "/sources", label: "Források" },
  { href: "/settings", label: "Beállítások" },
  { href: "/search", label: "Keresés" },
  { href: "/ask", label: "Kérdezés" },
  { href: "/graph", label: "Gráf" },
  { href: "/proposals", label: "Javaslatok" },
  { href: "/projects", label: "Projektek" },
] as const;

export function AppNav() {
  const pathname = usePathname();

  return (
    <nav className="app-nav" aria-label="Fő navigáció">
      <div className="app-nav-inner">
        <Link href="/" className="app-nav-brand">
          PKB
        </Link>
        <ul className="app-nav-links">
          {NAV_ITEMS.map((item) => {
            const active =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <li key={item.href}>
                <Link href={item.href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined}>
                  {item.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </div>
    </nav>
  );
}
