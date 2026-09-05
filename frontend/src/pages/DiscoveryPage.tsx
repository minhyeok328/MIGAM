import * as Tabs from '@radix-ui/react-tabs';
import { useDiscovery } from '../app/providers';
import { SiteShell } from '../app/SiteShell';
import { SearchPanel } from '../features/discovery/SearchPanel';
import { RecommendationPanel } from '../features/discovery/RecommendationPanel';

export function DiscoveryPage() {
  const { state, demo } = useDiscovery();

  return (
    <SiteShell currentPage="discover" tone="paper" demo={demo}>
      <main id="main-content" className="discovery-page" tabIndex={-1}>
        <section
          id="discovery-tools"
          className="page-width discovery-workspace"
          aria-labelledby="discovery-title"
          tabIndex={-1}
        >
          <Tabs.Root
            value={state.tab}
            onValueChange={(value) => state.setTab(value as 'search' | 'recommend')}
          >
            <div className="discovery-heading">
              <h1 id="discovery-title">전시 찾기</h1>
              <Tabs.List className="discovery-tabs" aria-label="전시 발견 방법">
                <Tabs.Trigger value="search">전시 둘러보기</Tabs.Trigger>
                <Tabs.Trigger value="recommend">조건으로 추천받기</Tabs.Trigger>
              </Tabs.List>
            </div>
            <Tabs.Content value="search">
              <SearchPanel />
            </Tabs.Content>
            <Tabs.Content value="recommend">
              <RecommendationPanel />
            </Tabs.Content>
          </Tabs.Root>
        </section>
      </main>
    </SiteShell>
  );
}
