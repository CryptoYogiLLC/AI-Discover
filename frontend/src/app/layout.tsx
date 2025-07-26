import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "./providers";
import { AuthLayout } from "@/components/auth-layout";
import { SkipLink } from "@/components/skip-link";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI-Discover - Automated Application Discovery",
  description:
    "Intelligent application discovery and cloud migration assessment platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <SkipLink />
        <Providers>
          <AuthLayout>{children}</AuthLayout>
        </Providers>
      </body>
    </html>
  );
}
