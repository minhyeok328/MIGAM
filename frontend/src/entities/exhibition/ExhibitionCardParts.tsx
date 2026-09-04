import { useState } from 'react';
import { ArrowUpRight, CalendarDays, Info, MapPin } from 'lucide-react';
import type { ExhibitionView, MatchLevel } from '../../shared/api/schemas';

export type ExhibitionCardVariant = 'catalog' | 'editorial';

export type ExhibitionCardProps = {
  item: ExhibitionView;
  index?: number;
  demo?: boolean;
};

const lifecycle = {
  CURRENT: '현재 전시',
  UPCOMING: '곧 시작',
  ENDED: '종료 · 현재 관람 불가',
  CANCELED: '취소 · 현재 관람 불가',
};

const matches: Record<MatchLevel, string> = {
  VERY_CLOSE: '취향에 매우 가까운',
  GOOD_MATCH: '취향과 잘 맞는',
  SOME_MATCH: '취향과 이어지는',
  GENERAL: '발견해볼 전시',
  EXPLORATION: '새롭게 발견하는',
};

const day = (value: string) => value.replaceAll('-', '.');

export function ExhibitionTextFallback({ item, index }: { item: ExhibitionView; index: number }) {
  return (
    <>
      <div className="cover-title">
        <span className="cover-rule" aria-hidden="true" />
        <p>{item.institution}</p>
        <h3>{item.title}</h3>
      </div>
      <span className="cover-folio" aria-hidden="true">
        {String(index + 1).padStart(2, '0')} · 美感
      </span>
    </>
  );
}

export function ExhibitionMedia({
  item,
  index,
  showImage,
  onImageError,
}: {
  item: ExhibitionView;
  index: number;
  showImage: boolean;
  onImageError: () => void;
}) {
  return (
    <div className={`card-cover ${showImage ? 'has-image' : ''}`}>
      {showImage && (
        <img
          src={item.image!}
          alt={`${item.title} 공식 이미지`}
          loading="lazy"
          referrerPolicy="no-referrer"
          onError={onImageError}
        />
      )}
      <div className="cover-top">
        <span className="editorial-label">{String(index + 1).padStart(2, '0')} / 전시</span>
        <span className={`status-tag status-${item.lifecycle.toLowerCase()}`}>
          {lifecycle[item.lifecycle]}
        </span>
      </div>
      {!showImage && <ExhibitionTextFallback item={item} index={index} />}
    </div>
  );
}

function ExhibitionDetails({
  item,
  showImage,
  demo,
}: {
  item: ExhibitionView;
  showImage: boolean;
  demo: boolean;
}) {
  return (
    <div className="card-body">
      {showImage && <h3 className="image-card-title">{item.title}</h3>}
      {item.matchLevel && <div className="match-label">{matches[item.matchLevel]}</div>}
      {item.reason && <p className="reason">{item.reason}</p>}
      {item.verification && (
        <ul className="verification-labels">
          {item.verification.map((label) => (
            <li key={label}>
              <Info size={14} aria-hidden="true" />
              {label}
            </li>
          ))}
        </ul>
      )}
      <p className="card-meta">
        <CalendarDays size={16} aria-hidden="true" />
        <span>
          {day(item.startDate)} — {day(item.endDate)}
        </span>
      </p>
      <p className="card-meta">
        <MapPin size={16} aria-hidden="true" />
        <span>
          {item.area} {item.district} · {item.venue}
        </span>
      </p>
      {item.freshness === 'STALE' && (
        <p className="freshness-warning">최근 운영 정보의 재확인이 필요합니다.</p>
      )}
      {showImage && item.credit && <p className="credit">{item.credit}</p>}
      <details className="source-details">
        <summary>출처와 확인 정보</summary>
        <p>
          {item.sourceOwner}
          <br />
          확인: {new Date(item.verifiedAt).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}
        </p>
        {!demo && item.mediaPage && (
          <a
            href={item.mediaPage}
            target="_blank"
            rel="noopener noreferrer"
            referrerPolicy="no-referrer"
          >
            이미지 출처 페이지 ↗
          </a>
        )}
      </details>
      <div className="card-footer">
        {demo ? (
          <span className="demo-card-note">가상 전시 · UI 체험용</span>
        ) : (
          <a
            href={item.officialUrl}
            target="_blank"
            rel="noopener noreferrer"
            referrerPolicy="no-referrer"
          >
            공식 페이지에서 확인 <ArrowUpRight size={17} aria-hidden="true" />
          </a>
        )}
      </div>
    </div>
  );
}

export function ExhibitionCardLayout({
  item,
  index = 0,
  demo = false,
  variant,
}: ExhibitionCardProps & { variant: ExhibitionCardVariant }) {
  const [failedImage, setFailedImage] = useState<string | null>(null);
  const showImage = item.image !== null && item.image !== failedImage;

  return (
    <article className={`exhibition-card exhibition-card--${variant}`} data-card-variant={variant}>
      <ExhibitionMedia
        item={item}
        index={index}
        showImage={showImage}
        onImageError={() => setFailedImage(item.image)}
      />
      <ExhibitionDetails item={item} showImage={showImage} demo={demo} />
    </article>
  );
}
