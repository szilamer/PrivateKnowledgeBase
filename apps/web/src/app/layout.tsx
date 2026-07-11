import type { Metadata } from "next";
import "./globals.css";
import { AppNav } from "@/components/AppNav";

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
    <html lang="hu">
      <body>
        <AppNav />
        {children}
      </body>
    </html>
  );
}
