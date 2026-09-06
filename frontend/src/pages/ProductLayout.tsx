import type { ReactNode } from 'react';
import { SiteShell } from '../app/SiteShell';
import { useDiscovery } from '../app/providers';
import { ProductNavigation } from '../features/personal/PersonalControls';

export function ProductLayout({
  title,
  intro,
  children,
}: {
  title: string;
  intro?: string;
  children: ReactNode;
}) {
  const { demo } = useDiscovery();
  return (
    <SiteShell currentPage="discover" tone="paper" demo={demo}>
      <ProductNavigation />
      <main id="main-content" className="page-width product-content" tabIndex={-1}>
        <div className="product-heading">
          <h1>{title}</h1>
          {intro && <p>{intro}</p>}
        </div>
        {children}
      </main>
    </SiteShell>
  );
}
