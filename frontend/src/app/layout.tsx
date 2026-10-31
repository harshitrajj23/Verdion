import type { Metadata } from "next";
import { Inter, Fraunces } from "next/font/google";
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

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-fraunces",
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
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body className="min-h-screen bg-marshmallow text-ink antialiased font-sans selection:bg-bubblegum-soft selection:text-bubblegum-deep">
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
