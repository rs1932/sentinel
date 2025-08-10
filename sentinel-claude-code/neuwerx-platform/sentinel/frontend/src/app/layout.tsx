import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/providers/QueryProvider";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { MainLayout } from "@/components/layout";
import { TerminologyWrapper } from "@/components/terminology";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Sentinel - Multi-tenant User Management",
  description: "A modern multi-tenant user management platform with role-based access control",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
        <QueryProvider>
          <AuthGuard>
            <TerminologyWrapper>
              <MainLayout>
                {children}
              </MainLayout>
            </TerminologyWrapper>
          </AuthGuard>
          <Toaster />
        </QueryProvider>
      </body>
    </html>
  );
}
