import { SiteShell } from '../app/SiteShell';
import { HomeEntryCta } from '../features/home/HomeEntryCta';
import { HomeFilm } from '../features/home/HomeFilm';
import { VisualChapters } from '../features/home/VisualChapters';
import { useHomeReveal } from '../features/home/useHomeReveal';

export function HomePage() {
  const revealRef = useHomeReveal();
  return (
    <SiteShell currentPage="home" tone="limestone">
      <main ref={revealRef} id="main-content" className="home-page" tabIndex={-1}>
        <HomeFilm />
        <VisualChapters />
        <HomeEntryCta />
      </main>
    </SiteShell>
  );
}
