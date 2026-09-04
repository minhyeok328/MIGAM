import { ExhibitionCardLayout, type ExhibitionCardProps } from './ExhibitionCardParts';

export function CatalogExhibitionCard(props: ExhibitionCardProps) {
  return <ExhibitionCardLayout {...props} variant="catalog" />;
}
