import { SiteShell } from '../app/SiteShell';
import { EditorialStatement } from '../features/home/EditorialStatement';
import { HomeEntryCta } from '../features/home/HomeEntryCta';
import { HomeFilm } from '../features/home/HomeFilm';
import { VisualChapters } from '../features/home/VisualChapters';

export function HomePage() {
  return (
    <SiteShell currentPage="home" tone="ink">
      <main id="main-content" className="home-page" tabIndex={-1}>
        <HomeFilm />
        <EditorialStatement />
        <VisualChapters />
        <HomeEntryCta />
      </main>
    </SiteShell>
  );
}
