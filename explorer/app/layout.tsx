import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist" });

export const metadata: Metadata = {
  title: "Matinee Idle Archive",
  description:
    "21 years of Radio New Zealand's legendary summer music show — 15,000+ rare, obscure and divisive songs played by Phil O'Brien and Simon Morris.",
  openGraph: {
    title: "Matinee Idle Archive",
    description: "Explore 21 years of Radio New Zealand's legendary summer music show.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.variable} h-full`}>
      <body className="min-h-full bg-neutral-950 text-neutral-100 font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
