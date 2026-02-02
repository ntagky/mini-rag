import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "next-themes";
import { AppSidebar } from "@/components/custom/app-sidebar";
import { DynamicBreadcrumb } from "@/components/custom/dynamic-breadcrumb";
import { AnimatedThemeToggler } from "@/components/ui/animated-theme-toggler";
import { Separator } from "@/components/ui/separator";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import Link from "next/link";
import { Icons } from "@/lib/dataclasses";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "MiniRAG",
  description: "Mini, yet precise",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" style={{"colorScheme": "dark"} as React.CSSProperties}>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <SidebarProvider>
            <AppSidebar />
            <SidebarInset>
              <header className="flex h-16 shrink-0 items-center gap-2 px-4">
                <div className="flex flex-row w-full items-center gap-2 justify-between">
                  <div className="flex items-center gap-2">
                    <SidebarTrigger className="-ml-1" />
                    <Separator
                      orientation="vertical"
                      className="mr-2 data-[orientation=vertical]:h-4"
                    />
                    <DynamicBreadcrumb></DynamicBreadcrumb>
                  </div>
                  <div className="flex gap-4 items-center">
                    <p>ntagkonikos @ pfizer</p>
                    <Link href={"https://www.linkedin.com/in/alexandros-ntagkonikos/"} target="_blank">
                      <Icons.linkedin className="size-5" />
                    </Link>
                    <Link href={"https://github.com/ntagky"} target="_blank">
                      <Icons.github className="size-5" />
                    </Link>
                    <Separator
                      orientation="vertical"
                      className="mr-2 data-[orientation=vertical]:h-4"
                    />
                    <AnimatedThemeToggler />
                  </div>
                </div>
              </header>
              <Separator />
              <div className="flex flex-1 h-screen overflow-y-auto flex-col gap-4 p-4 pt-0">
                {children}
              </div>
            </SidebarInset>
          </SidebarProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
