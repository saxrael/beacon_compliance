import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/context/ThemeContext";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Beacon Compliance OS — Potter's House Christian Mission UK (SC054652)",
  description:
    "Agentic OSCR-compliance web application for Potter's House Christian Mission UK (SCIO, SC054652). Deterministic Receipts & Payments accounts, Trustees' Annual Report synthesis, and trustee sign-off.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="light" suppressHydrationWarning>
      <body className={`${inter.className} bg-[#F8F7F4] dark:bg-[#090D16] text-slate-900 dark:text-slate-100 antialiased min-h-screen transition-colors duration-300`}>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
