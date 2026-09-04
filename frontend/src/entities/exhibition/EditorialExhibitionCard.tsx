import { ExhibitionCardLayout, type ExhibitionCardProps } from './ExhibitionCardParts';

export function EditorialExhibitionCard(props: ExhibitionCardProps) {
  return <ExhibitionCardLayout {...props} variant="editorial" />;
}
