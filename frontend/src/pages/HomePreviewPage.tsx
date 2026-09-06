import { ArrowLeft } from 'lucide-react';
import { SiteShell } from '../app/SiteShell';

export function HomePreviewPage() {
  return (
    <SiteShell currentPage="home" tone="paper">
      <main id="main-content" className="not-found-page page-width" tabIndex={-1}>
        <p className="editorial-label">미감 · 디자인 미리보기</p>
        <h1>지금은 홈 디자인을 살펴보는 중이에요.</h1>
        <p>이 링크는 홈 디자인에 대한 의견을 나누기 위한 임시 페이지예요.</p>
        <p>전시 탐색과 조건 추천은 다음에 만나볼 수 있어요.</p>
        <a className="secondary-button" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          홈으로 돌아가기
        </a>
      </main>
    </SiteShell>
  );
}
