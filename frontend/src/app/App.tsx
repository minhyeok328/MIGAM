import { Providers } from './providers';
import { DiscoveryPage } from '../pages/DiscoveryPage';
import { HomePage } from '../pages/HomePage';
import { NotFoundPage } from '../pages/NotFoundPage';
import type { DiscoveryApi } from '../shared/api/client';

export function App({ api, demo = false }: { api?: DiscoveryApi; demo?: boolean }) {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';

  if (pathname === '/') return <HomePage />;

  if (pathname === '/discover') {
    const initialTab = window.location.hash === '#recommend' ? 'recommend' : 'search';
    return (
      <Providers api={api} demo={demo} initialTab={initialTab}>
        <DiscoveryPage />
      </Providers>
    );
  }

  return <NotFoundPage />;
}
