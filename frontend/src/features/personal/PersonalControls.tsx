import { Heart, Columns3 } from 'lucide-react';
import { usePersonal } from '../../app/providers';

export function LikeButton({
  id,
  kind = 'exhibitions',
}: {
  id: number;
  kind?: 'exhibitions' | 'institutions' | 'artworks';
}) {
  const state = usePersonal();
  const liked = state.data[kind].includes(id);
  const full = !liked && state.data[kind].length >= 100;
  return (
    <button
      className="text-button"
      type="button"
      aria-pressed={liked}
      disabled={full}
      onClick={() => state.toggleLike(kind, id)}
    >
      <Heart size={17} fill={liked ? 'currentColor' : 'none'} aria-hidden="true" />
      {liked ? '관심 해제' : full ? '관심은 최대 100개' : '관심 저장'}
    </button>
  );
}
export function CompareButton({ id }: { id: number }) {
  const state = usePersonal();
  const selected = state.compare.includes(id);
  const full = !selected && state.compare.length >= 3;
  return (
    <button
      className="text-button"
      type="button"
      aria-pressed={selected}
      disabled={full}
      onClick={() => state.toggleCompare(id)}
    >
      <Columns3 size={17} aria-hidden="true" />
      {selected ? '비교 제외' : full ? '비교는 최대 3개' : '비교 추가'}
    </button>
  );
}
export function ProductNavigation() {
  const state = usePersonal();
  const links = [
    ['/discover', '전시 찾기'],
    ['/artworks', '작품'],
    ['/taste', '취향'],
    ['/saved', '관심 목록'],
    ['/compare', `비교 ${state.compare.length}`],
    ['/settings', '내 데이터'],
  ];
  return (
    <div className="page-width product-navigation-wrap">
      <nav className="product-navigation" aria-label="미감 메뉴">
        {links.map(([href, label]) => (
          <a
            key={href}
            href={href}
            aria-current={window.location.pathname === href ? 'page' : undefined}
          >
            {label}
          </a>
        ))}
      </nav>
      {state.storageFailed && (
        <p className="storage-notice" role="status">
          브라우저에 저장하지 못했어요. 현재 창에서는 선택이 유지됩니다.{' '}
          <button className="text-button" onClick={state.retrySave}>
            저장 다시 시도
          </button>
        </p>
      )}
    </div>
  );
}
