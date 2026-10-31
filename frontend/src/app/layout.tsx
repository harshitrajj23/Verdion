import type { Metadata } from "next";
import "@/styles/globals.css";
import { StoreProvider } from "@/lib/store";
import { AppHeader } from "@/components/AppHeader";
import { AppSidebar } from "@/components/AppSidebar";
import { ToastContainer } from "@/components/ToastContainer";

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
    <html lang="en">
      <body className="min-h-screen bg-cream-100 text-ink antialiased font-sans selection:bg-lavender-200 selection:text-lavender-900">
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
