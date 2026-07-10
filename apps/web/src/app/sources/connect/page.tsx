import Link from "next/link";

const tiles = [
  {
    href: "/sources/connect/local",
    title: "Helyi mappa",
    subtitle: "Fájlok a gépeden",
    icon: "📁",
  },
  {
    href: "/sources/connect/google",
    title: "Google Drive",
    subtitle: "Mappák a Drive-odban",
    icon: "☁️",
  },
  {
    href: "/sources/connect/google?mode=gmail",
    title: "Email",
    subtitle: "Gmail fontos levelek",
    icon: "✉️",
  },
  {
    href: "/sources/connect/google?mode=calendar",
    title: "Naptár",
    subtitle: "Google Naptár események",
    icon: "📅",
  },
];

export default function ConnectSourcePage() {
  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Új forrás</p>
        <h1>Mit szeretnél csatlakoztatni?</h1>
        <p className="lead">Válassz egy forrástípust. A varázsló végigvezet a beállításon.</p>
      </section>

      <section className="tile-grid">
        {tiles.map((tile) => (
          <Link key={tile.href} href={tile.href} className="tile">
            <span className="tile-icon">{tile.icon}</span>
            <strong>{tile.title}</strong>
            <span className="muted">{tile.subtitle}</span>
          </Link>
        ))}
      </section>

      <p className="muted back-link">
        <Link href="/sources">← Vissza a forrásokhoz</Link>
      </p>
    </main>
  );
}
