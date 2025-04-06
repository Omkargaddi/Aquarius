import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "./components/header"; 
import Footer from "./components/Footer";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: "NFT Fraud Detector",
  description: "AI-powered tool to detect fraudulent NFTs",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Header />
        <main className=" main-section">{children}</main>
      </body>
    </html>
  );
}
