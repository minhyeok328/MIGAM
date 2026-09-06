import { Providers } from './providers';
import { DiscoveryPage } from '../pages/DiscoveryPage';
import { HomePage } from '../pages/HomePage';
import { HomePreviewPage } from '../pages/HomePreviewPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import type { DiscoveryApi } from '../shared/api/client';

export function App({
  api,
  demo = false,
  homePreview = false,
}: {
  api?: DiscoveryApi;
  demo?: boolean;
  homePreview?: boolean;
}) {
  const pathname = window.location.pathname.replace(/\/+$/, '') || '/';

  if (pathname === '/') return <HomePage />;

  if (pathname === '/discover') {
    if (homePreview) return <HomePreviewPage />;
    const initialTab = window.location.hash === '#recommend' ? 'recommend' : 'search';
    return (
      <Providers api={api} demo={demo} initialTab={initialTab}>
        <DiscoveryPage />
      </Providers>
    );
  }

  return <NotFoundPage />;
}
