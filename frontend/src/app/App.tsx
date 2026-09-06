import { Providers } from './providers';
import { DiscoveryPage } from '../pages/DiscoveryPage';
import { HomePage } from '../pages/HomePage';
import { HomePreviewPage } from '../pages/HomePreviewPage';
import { NotFoundPage } from '../pages/NotFoundPage';
import type { DiscoveryApi } from '../shared/api/client';
import { useEffect, useState } from 'react';
import { useDiscovery } from './providers';
import { ExhibitionDetailPage, InstitutionDetailPage } from '../pages/DetailPage';
import { SavedPage } from '../pages/SavedPage';
import { ComparePage } from '../pages/ComparePage';
import { SettingsPage } from '../pages/SettingsPage';
import { TastePage } from '../pages/TastePage';
import { ArtworkPage, ArtworkDetailPage } from '../pages/ArtworkPage';

function ProductRoute({ pathname, hash }: { pathname: string; hash: string }) {
  const { store } = useDiscovery();
  useEffect(() => {
    if (pathname === '/discover' && hash === '#recommend') store.getState().setTab('recommend');
  }, [pathname, hash, store]);
  if (pathname === '/discover') return <DiscoveryPage />;
  if (pathname === '/saved') return <SavedPage />;
  if (pathname === '/compare') return <ComparePage />;
  if (pathname === '/settings') return <SettingsPage />;
  if (pathname === '/taste') return <TastePage />;
  if (pathname === '/artworks') return <ArtworkPage />;
  const match = pathname.match(/^\/(exhibitions|institutions|artworks)\/([1-9]\d*)$/);
  if (match && Number.isSafeInteger(Number(match[2])))
    return match[1] === 'artworks' ? (
      <ArtworkDetailPage key={match[2]} id={Number(match[2])} />
    ) : match[1] === 'exhibitions' ? (
      <ExhibitionDetailPage key={match[2]} id={Number(match[2])} />
    ) : (
      <InstitutionDetailPage key={match[2]} id={Number(match[2])} />
    );
  return <NotFoundPage />;
}

export function App({
  api,
  demo = false,
  homePreview = false,
}: {
  api?: DiscoveryApi;
  demo?: boolean;
  homePreview?: boolean;
}) {
  const [location, setLocation] = useState(() => window.location.pathname + window.location.hash);
  useEffect(() => {
    const update = () => setLocation(window.location.pathname + window.location.hash);
    function navigate(event: MouseEvent) {
      if (
        event.defaultPrevented ||
        event.button !== 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      const anchor = event.target instanceof Element ? event.target.closest('a') : null;
      if (
        !anchor ||
        anchor.target ||
        anchor.hasAttribute('download') ||
        !anchor.getAttribute('href')?.startsWith('/')
      )
        return;
      const url = new URL(anchor.href);
      if (url.origin !== window.location.origin) return;
      event.preventDefault();
      window.history.pushState(null, '', url.pathname + url.hash);
      update();
    }
    window.addEventListener('popstate', update);
    document.addEventListener('click', navigate);
    return () => {
      window.removeEventListener('popstate', update);
      document.removeEventListener('click', navigate);
    };
  }, []);
  useEffect(() => {
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    document.getElementById('main-content')?.focus({ preventScroll: true });
  }, [location]);
  const [rawPath, fragment] = location.split('#');
  const pathname = rawPath.replace(/\/+$/, '') || '/';

  if (pathname === '/') return <HomePage />;

  if (
    pathname === '/discover' ||
    ['/saved', '/compare', '/settings', '/taste', '/artworks'].includes(pathname) ||
    /^\/(exhibitions|institutions|artworks)\/[1-9]\d*$/.test(pathname)
  ) {
    if (homePreview) return <HomePreviewPage />;

    const initialTab = fragment === 'recommend' ? 'recommend' : 'search';
    return (
      <Providers api={api} demo={demo} initialTab={initialTab}>
        <ProductRoute pathname={pathname} hash={fragment ? `#${fragment}` : ''} />
      </Providers>
    );
  }

  return <NotFoundPage />;
}
