import React, { Suspense } from "react";
import type { Metadata, Viewport } from "next";
import { Poppins } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider"
import { AppSidebar } from "@/components/app-sidebar";
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { VideoQueueProvider } from "@/context/video-queue-context";
import { JobsProvider } from "@/context/jobs-context";
import { ImageSettingsProvider } from "@/context/image-settings-context";
import { FolderProvider } from "@/context/folder-context";
import { VideoQueueClient } from "@/components/video-queue-client";
import { RefreshJobsButton } from "@/components/refresh-jobs-button";
import { Toaster } from "@/components/ui/sonner";
import { AnimatedLayout } from "@/components/animated-layout";
import { MediaProvider } from "@/context/media-context";
import Script from "next/script";

type RootLayoutProps = {
  children: React.ReactNode
}

const poppins = Poppins({
  weight: ['400', '500', '600', '700'],
  subsets: ["latin"],
  variable: "--font-poppins",
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Starbucks Video Studio",
  description: "AI-powered Content Generation",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/logo/starbucks-logo.svg", type: "image/svg+xml" },
      { url: "/logo/icon-192.png", sizes: "192x192", type: "image/png" },
    ],
    apple: "/logo/icon-192.png",
    shortcut: "/logo/starbucks-logo.svg",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Starbucks Video Studio",
  },
  other: {
    "mobile-web-app-capable": "yes",
    "apple-mobile-web-app-capable": "yes",
    "apple-mobile-web-app-status-bar-style": "default",
    "msapplication-TileColor": "#00704A",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  themeColor: "#00704A",
};

export default async function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" suppressHydrationWarning className={`${poppins.variable} antialiased`}>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link rel="dns-prefetch" href={process.env.NEXT_PUBLIC_API_HOSTNAME || "localhost"} />
        <meta name="format-detection" content="telephone=no" />
      </head>
      <body className="overflow-hidden" style={{ fontFamily: 'var(--font-poppins), -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }}>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <MediaProvider>
            <VideoQueueProvider>
              <JobsProvider>
                <ImageSettingsProvider>
                  <FolderProvider>
                    <div className="relative flex min-h-screen h-screen">              
                      <SidebarProvider
                        style={
                          {
                            "--sidebar-width": "12rem",
                          } as React.CSSProperties
                        }
                        className="flex h-full w-full"
                      >
                        <Suspense fallback={
                          <div className="w-[var(--sidebar-width)] shrink-0 border-r h-full" />
                        }>
                          <AppSidebar />
                        </Suspense>
                        <SidebarInset className="flex-1 flex flex-col h-full w-full">
                          <div className="flex h-14 items-center gap-2 border-b shrink-0 px-3">
                            <SidebarTrigger />
                            <Separator orientation="vertical" className="mx-2 h-4" />
                            <div className="ml-auto flex items-center space-x-2">
                              <RefreshJobsButton />
                              <VideoQueueClient />
                            </div>
                          </div>
                          <main className="flex-1 overflow-auto w-full transition-all duration-200">
                            <AnimatedLayout>
                              {children}
                            </AnimatedLayout>
                          </main>
                        </SidebarInset>
                      </SidebarProvider>
                    </div>
                    <Toaster />
                  </FolderProvider>
                </ImageSettingsProvider>
              </JobsProvider>
            </VideoQueueProvider>
          </MediaProvider>
        </ThemeProvider>
        <Script
          id="sw-register"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js')
                    .then(function(registration) {
                      console.log('SW registered: ', registration);
                    })
                    .catch(function(registrationError) {
                      console.log('SW registration failed: ', registrationError);
                    });
                });
              }
            `,
          }}
        />
        <Script
          id="resource-preload"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              if ('fetch' in window) {
                fetch('/api/environment', { method: 'HEAD' }).catch(() => {});
              }
              if ('requestIdleCallback' in window) {
                requestIdleCallback(() => {
                  const links = ['/gallery', '/new-image', '/new-video'];
                  links.forEach(link => {
                    const linkEl = document.createElement('link');
                    linkEl.rel = 'prefetch';
                    linkEl.href = link;
                    document.head.appendChild(linkEl);
                  });
                });
              }
            `,
          }}
        />
      </body>
    </html>
  )
}
