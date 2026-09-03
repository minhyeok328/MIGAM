import { Providers } from './providers';
import { DiscoveryPage } from '../pages/DiscoveryPage';
import type { DiscoveryApi } from '../shared/api/client';

export function App({ api, demo = false }: { api?: DiscoveryApi; demo?: boolean }) {
  return (
    <Providers api={api} demo={demo}>
      <DiscoveryPage />
    </Providers>
  );
}
