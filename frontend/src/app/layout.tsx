import type { Metadata } from "next";
import "./globals.css";
import ClientAuthProvider from "@/components/ClientAuthProvider";

export const metadata: Metadata = {
  title: "AIRMS - AI Risk Management System",
  description: "Comprehensive AI risk detection, analysis, and mitigation tools for safe AI interactions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <ClientAuthProvider>
          {children}
        </ClientAuthProvider>
      </body>
    </html>
  );
}
