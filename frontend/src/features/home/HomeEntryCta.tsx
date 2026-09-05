import { ArrowRight } from 'lucide-react';

export function HomeEntryCta() {
  return (
    <section className="home-entry-cta theme-limestone" aria-labelledby="home-entry-title">
      <div className="page-width home-entry-inner">
        <div className="home-entry-copy">
          <h2 id="home-entry-title">어떤 전시가 끌리나요?</h2>
          <p>가고 싶은 지역과 날짜, 나에게 중요한 조건으로 찾아보세요.</p>
        </div>
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
