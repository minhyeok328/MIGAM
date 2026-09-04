import { Landmark } from 'lucide-react';
import type { ExhibitionView, InstitutionView } from '../shared/api/schemas';
import { CatalogExhibitionCard } from './exhibition/CatalogExhibitionCard';
import { EditorialExhibitionCard } from './exhibition/EditorialExhibitionCard';
import type { ExhibitionCardVariant } from './exhibition/ExhibitionCardParts';

export function ExhibitionCard({
  item,
  index = 0,
  demo = false,
  variant = 'catalog',
}: {
  item: ExhibitionView;
  index?: number;
  demo?: boolean;
  variant?: ExhibitionCardVariant;
}) {
  const Card = variant === 'editorial' ? EditorialExhibitionCard : CatalogExhibitionCard;
  return <Card item={item} index={index} demo={demo} />;
}

export function InstitutionCard({ item }: { item: InstitutionView }) {
  return (
    <article className="institution-card">
      <div className="flex items-center justify-between">
        <Landmark size={28} strokeWidth={1.2} aria-hidden="true" />
        <span className="editorial-label">문화예술 공간</span>
      </div>
      <h3>{item.name}</h3>
      <p>
        {item.area} {item.district}
      </p>
      <p className="institution-count">
        검색 가능한 전시 <strong>{item.exhibitionCount}개</strong>
      </p>
    </article>
  );
}
