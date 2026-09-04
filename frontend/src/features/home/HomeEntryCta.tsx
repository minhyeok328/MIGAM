import { ArrowRight } from 'lucide-react';

export function HomeEntryCta() {
  return (
    <section className="home-entry-cta theme-ink" aria-labelledby="home-entry-title">
      <div className="page-width home-entry-inner">
        <p className="editorial-label">BEGIN WITH TODAY</p>
        <h2 id="home-entry-title">오늘의 감각이 향하는 전시를 찾아보세요.</h2>
        <p>
          이름으로 천천히 둘러보거나,
          <br />
          방문 조건에서 바로 시작할 수 있습니다.
        </p>
        <div className="home-entry-actions">
          <a className="home-entry-link" href="/discover">
            전시 둘러보기
            <ArrowRight size={20} aria-hidden="true" />
          </a>
          <a className="home-entry-link" href="/discover#recommend">
            조건으로 추천받기
            <ArrowRight size={20} aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}
