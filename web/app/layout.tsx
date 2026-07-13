import type { Metadata } from "next";
import { IBM_Plex_Mono, Instrument_Serif, Manrope } from "next/font/google";
import { Navbar } from "@/components/navbar";
import { SmoothScroll } from "@/components/providers/smooth-scroll";
import "./globals.css";

const sans = Manrope({ subsets: ["latin"], variable: "--font-geist-sans" });
const mono = IBM_Plex_Mono({
  weight: ["400", "500"],
  subsets: ["latin"],
  variable: "--font-geist-mono",
});
const instrument = Instrument_Serif({
  weight: "400",
  subsets: ["latin"],
  variable: "--font-instrument",
});

export const metadata: Metadata = {
  title: "FactoryPulse",
  description: "Multimodal anomaly triage for manufacturing lines",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${sans.variable} ${mono.variable} ${instrument.variable} font-sans antialiased`}>
        <SmoothScroll>
          <Navbar />
          {children}
        </SmoothScroll>
      </body>
    </html>
  );
}
