import { ArrowLeft } from 'lucide-react';
import { SiteShell } from '../app/SiteShell';

export function NotFoundPage() {
  return (
    <SiteShell currentPage="home" tone="paper">
      <main id="main-content" className="not-found-page page-width" tabIndex={-1}>
        <p className="editorial-label">404 · PAGE NOT FOUND</p>
        <h1>페이지를 찾을 수 없어요.</h1>
        <p>주소를 다시 확인하거나 미감의 홈에서 새로운 전시 탐색을 시작해보세요.</p>
        <a className="secondary-button" href="/">
          <ArrowLeft size={18} aria-hidden="true" />
          홈으로 돌아가기
        </a>
      </main>
    </SiteShell>
  );
}
