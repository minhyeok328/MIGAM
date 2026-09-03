import * as Tabs from '@radix-ui/react-tabs';
import { ArrowDownRight, Compass, SlidersHorizontal } from 'lucide-react';
import { useDiscovery } from '../app/providers';
import { SearchPanel } from '../features/discovery/SearchPanel';
import { RecommendationPanel } from '../features/discovery/RecommendationPanel';

export function DiscoveryPage() {
  const { state, demo } = useDiscovery();
  return (
    <>
      <a className="skip-link" href="#discovery">
        본문으로 바로가기
      </a>
      {demo && (
        <div className="demo-banner" role="note">
          로컬 데모 · 아래 전시와 기관은 가상 데이터이며 실제 전시가 아닙니다.
        </div>
      )}
      <header className="site-header">
        <div className="page-width header-inner">
          <a className="wordmark" href="#discovery" aria-label="미감, 발견 화면">
            <span className="wordmark-hanja">美感</span>
            <span>
              미감 <small>MIGAM</small>
            </span>
          </a>
          <span className="header-note">좋아하는 것부터 시작하는 전시 발견</span>
          <span className="edition-label">전시 발견 / 01</span>
        </div>
      </header>
      <main id="discovery" className="page-width" tabIndex={-1}>
        <section className="intro">
          <div>
            <p className="editorial-label intro-label">ART, AT YOUR OWN PACE</p>
            <h1>
              당신의 감각으로,
              <br />
              <span>전시를 발견하다.</span>
            </h1>
          </div>
          <div className="intro-note">
            <ArrowDownRight size={40} strokeWidth={1} aria-hidden="true" />
            <p>
              아는 만큼 보는 대신,
              <br />
              좋아하는 것부터 시작해보세요.
            </p>
            <small>이름으로 찾거나, 나의 관람 조건에서 시작하세요.</small>
          </div>
        </section>
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
      </main>
      <footer className="page-width site-footer">
        <div>
          <span className="footer-mark">美感</span>
          <p>당신의 속도로 발견하는 아름다움.</p>
        </div>
        <p>
          공식 출처와 확인된 정보를 바탕으로 안내합니다.
          <br />
          계정 없이, 지금의 선택만으로.
        </p>
        <span className="editorial-label">MIGAM · LOCAL EDITION</span>
      </footer>
    </>
  );
}
