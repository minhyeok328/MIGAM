import * as Tabs from '@radix-ui/react-tabs';
import { Compass, SlidersHorizontal } from 'lucide-react';
import { useDiscovery } from '../app/providers';
import { SiteShell } from '../app/SiteShell';
import { SearchPanel } from '../features/discovery/SearchPanel';
import { RecommendationPanel } from '../features/discovery/RecommendationPanel';

export function DiscoveryPage() {
  const { state, demo } = useDiscovery();

  return (
    <SiteShell
      currentPage="discover"
      tone="paper"
      demo={demo}
      onRecommendClick={() => state.setTab('recommend')}
    >
      <main id="main-content" className="discovery-page" tabIndex={-1}>
        <section
          id="discovery-tools"
          className="page-width discovery-workspace"
          aria-labelledby="discovery-title"
          tabIndex={-1}
        >
          <header className="discovery-intro">
            <span className="editorial-label">FIND YOUR EXHIBITION</span>
            <h1 id="discovery-title">오늘의 전시를 찾는 두 가지 방법</h1>
            <p>이름으로 둘러보거나, 지금의 방문 조건에서 시작하세요.</p>
          </header>
          <Tabs.Root
            value={state.tab}
            onValueChange={(value) => state.setTab(value as 'search' | 'recommend')}
          >
            <Tabs.List className="discovery-tabs" aria-label="전시 발견 방법">
              <Tabs.Trigger value="search">
                <Compass size={18} aria-hidden="true" />
                전시 둘러보기
              </Tabs.Trigger>
              <Tabs.Trigger value="recommend">
                <SlidersHorizontal size={18} aria-hidden="true" />
                조건으로 추천받기
              </Tabs.Trigger>
            </Tabs.List>
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
