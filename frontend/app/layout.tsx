import './globals.css';

export const metadata = { title: 'Toolkit Peptide Intelligence', description: 'Scientific intelligence for peptide research and pharmaceutical development.' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
