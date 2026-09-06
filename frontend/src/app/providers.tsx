import { createContext, useContext, useState, type ReactNode } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useStore } from 'zustand';
import { createDiscoveryApi, type DiscoveryApi } from '../shared/api/client';
import { createPersonalStore, type PersonalStore } from '../features/personal/store';
import {
  createDiscoveryStore,
  type DiscoveryStore,
  type DiscoveryTab,
} from '../features/discovery/store';

const Context = createContext<{
  api: DiscoveryApi;
  store: DiscoveryStore;
  personal: PersonalStore;
  demo: boolean;
} | null>(null);
export function Providers({
  children,
  api,
  demo = false,
  initialTab = 'search',
}: {
  children: ReactNode;
  api?: DiscoveryApi;
  demo?: boolean;
  initialTab?: DiscoveryTab;
}) {
  const [store] = useState(() => createDiscoveryStore(initialTab));
  const [personal] = useState(() => createPersonalStore(demo));
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            gcTime: 0,
            retry: false,
            refetchOnWindowFocus: false,
            refetchOnReconnect: false,
          },
        },
      }),
  );
  const [defaultApi] = useState(() => createDiscoveryApi());
  return (
    <Context.Provider value={{ api: api ?? defaultApi, store, personal, demo }}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </Context.Provider>
  );
}
export function usePersonal() {
  const context = useContext(Context);
  if (!context) throw new Error('Discovery provider is required');
  return useStore(context.personal);
}
export function useDiscovery() {
  const context = useContext(Context);
  if (!context) throw new Error('Discovery provider is required');
  return { ...context, state: useStore(context.store) };
}
