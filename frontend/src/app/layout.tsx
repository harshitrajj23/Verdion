import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "@/styles/globals.css";
import { StoreProvider } from "@/lib/store";
import { AppHeader } from "@/components/AppHeader";
import { AppSidebar } from "@/components/AppSidebar";
import { ToastContainer } from "@/components/ToastContainer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export const metadata: Metadata = {
  title: "VERIDION | Decentralized Legal Intelligence Protocol",
  description: "Coordinating specialized AI agents to research legal questions, create competing evidence-backed arguments, forecast outcomes, and resolve uncertainties on-chain.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="min-h-screen bg-verdion-950 text-slate-100 antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
        <StoreProvider>
          <div className="flex flex-col min-h-screen">
            <AppHeader />
            <div className="flex flex-1">
              <AppSidebar />
              <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
                {children}
              </main>
            </div>
            <ToastContainer />
          </div>
        </StoreProvider>
      </body>
    </html>
  );
}
