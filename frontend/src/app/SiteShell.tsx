import { useEffect, useState, type ReactNode } from 'react';

export function SiteShell({
  children,
  currentPage,
  tone,
  demo = false,
}: {
  children: ReactNode;
  currentPage: 'home' | 'discover';
  tone: 'ink' | 'limestone' | 'paper';
  demo?: boolean;
}) {
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    if (currentPage !== 'home') {
      setCompact(false);
      return;
    }

    const updateHeader = () => {
      setCompact((wasCompact) => {
        if (window.innerWidth <= 700) return false;
        return window.scrollY > (wasCompact ? 40 : 120);
      });
    };

    updateHeader();
    window.addEventListener('scroll', updateHeader, { passive: true });
    window.addEventListener('resize', updateHeader);
    return () => {
      window.removeEventListener('scroll', updateHeader);
      window.removeEventListener('resize', updateHeader);
    };
  }, [currentPage]);

  return (
    <div className={`site-page site-page-${tone}`}>
      <a className="skip-link" href="#main-content">
        본문으로 바로가기
      </a>
      {demo && (
        <div className="demo-banner" role="note">
          로컬 데모 · 아래 전시와 기관은 가상 데이터이며 실제 전시가 아닙니다.
        </div>
      )}
      <div className={`site-header-frame site-header-frame-${currentPage}`}>
        <header
          className={`site-header site-header-${tone}${currentPage === 'home' && compact ? ' site-header-compact' : ''}`}
        >
          <div className="page-width header-inner">
            <a className="wordmark" href="/" aria-label="미감 홈">
              <span className="wordmark-hanja" aria-hidden="true">
                美感
              </span>
              <span>
                미감 <small>MIGAM</small>
              </span>
            </a>
            <span className="edition-label">
              {currentPage === 'home' ? 'ART, AT YOUR PACE' : 'EXHIBITION DISCOVERY'}
            </span>
          </div>
        </header>
      </div>
      {children}
      <div className="site-footer-shell theme-limestone">
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
      </div>
    </div>
  );
}
