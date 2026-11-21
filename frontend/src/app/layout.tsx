import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "RAVENX AI – Intelligence That Sees What Others Miss",
  description:
    "Advanced AI document quality inspection platform detecting nuanced errors, structural defects, and cross-document inconsistencies.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body
        className="min-h-full"
        style={{
          background: "#F5F6F8",
          color: "#17191F",
        }}
      >
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
