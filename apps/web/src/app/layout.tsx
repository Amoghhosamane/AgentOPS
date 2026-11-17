import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AgentOps — AI Agent Observability & Tracing Platform',
  description: 'Enterprise AI Agent Observability, Distributed Tracing, and Automated Evaluation SaaS.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#090E1A] text-slate-100 antialiased selection:bg-blue-600 selection:text-white">
        {children}
      </body>
    </html>
  );
}
