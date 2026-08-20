import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F8F7F4" },
    { media: "(prefers-color-scheme: dark)", color: "#070A11" },
  ],
};

export const metadata: Metadata = {
  title: "Beacon Compliance — Potter's House Christian Mission UK (SC054652)",
  description:
    "Scottish charity annual filing and statutory compliance portal for Potter's House Christian Mission UK (SCIO, SC054652). Prepare Receipts & Payments accounts, Trustees' Annual Reports, and sign off annual returns for the Scottish Charity Regulator (OSCR).",
  icons: {
    icon: [
      { url: "/assets/logo_mark.png", type: "image/png" },
      { url: "/assets/logo.png", type: "image/png" },
    ],
    shortcut: "/assets/logo_mark.png",
    apple: "/assets/logo_mark.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <body className={`${inter.className} bg-[#F8F7F4] dark:bg-[#070A11] text-slate-900 dark:text-slate-100 antialiased min-h-screen w-full max-w-[100vw] overflow-x-hidden transition-colors duration-300`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
