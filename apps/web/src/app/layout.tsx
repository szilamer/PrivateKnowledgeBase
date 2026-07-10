import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Private Knowledge Base",
  description: "AI-powered personal knowledge operations system",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
