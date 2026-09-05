import { useEffect, useState } from 'react';
import { ArrowDownRight, ArrowRight } from 'lucide-react';

function getMediaQueryMatch(query: string) {
  return typeof window.matchMedia === 'function' && window.matchMedia(query).matches;
}

function useMediaQuery(query: string) {
  const [matches, setMatches] = useState(() => getMediaQueryMatch(query));

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return;
    const mediaQuery = window.matchMedia(query);
    const handleChange = (event: MediaQueryListEvent) => setMatches(event.matches);

    setMatches(mediaQuery.matches);
    mediaQuery.addEventListener?.('change', handleChange);
    return () => mediaQuery.removeEventListener?.('change', handleChange);
  }, [query]);

  return matches;
}

export function HomeFilm() {
  const reducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
  const narrowViewport = useMediaQuery('(max-width: 767px)');
  const showVideo = !reducedMotion && !narrowViewport;

  return (
    <section className="home-film" aria-label="미감 소개">
      <picture className="home-film-poster" aria-hidden="true">
        <source
          media="(max-width: 767px)"
          srcSet="/assets/home/film/migam-home-poster-960.webp"
          type="image/webp"
        />
        <img
          src="/assets/home/film/migam-home-poster-1920.webp"
          width="1920"
          height="1080"
          alt=""
          decoding="async"
          fetchPriority="high"
        />
      </picture>
      {showVideo && (
        <video
          className="home-film-video"
          aria-hidden="true"
          poster="/assets/home/film/migam-home-poster-1920.webp"
          autoPlay
          muted
          loop
          playsInline
          preload="metadata"
        >
          <source src="/assets/home/film/migam-home-film-v1.webm" type="video/webm" />
          <source src="/assets/home/film/migam-home-film-v1.mp4" type="video/mp4" />
        </video>
      )}
      <div className="home-film-wash" aria-hidden="true" />
      <div className="page-width home-film-copy">
        <h1>
          당신의 감각으로, <br />
          전시를 발견하다.
        </h1>
        <p className="home-film-lede">지금의 취향과 일정에 맞는 전시를 만나보세요.</p>
        <div className="hero-actions">
          <a className="primary-button" href="/discover">
            전시 둘러보기
            <ArrowRight size={18} aria-hidden="true" />
          </a>
          <a className="secondary-button" href="/discover#recommend">
            조건으로 추천받기
            <ArrowDownRight size={18} aria-hidden="true" />
          </a>
        </div>
      </div>
    </section>
  );
}
