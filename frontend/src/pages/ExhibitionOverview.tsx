import { useState } from 'react';
import { ArrowUpRight, CalendarDays, MapPin } from 'lucide-react';
import type { ExhibitionDetail } from '../shared/api/schemas';

const states = {
  CURRENT: '현재 전시',
  UPCOMING: '예정 전시',
  ENDED: '종료 · 현재 관람 불가',
  CANCELED: '취소 · 현재 관람 불가',
};
const noteKinds: Record<string, string> = {
  관람료: 'PRICE',
  '운영일·시간': 'HOURS',
  예약: 'RESERVATION',
};
const day = (value: string) => value.replaceAll('-', '.');
const checkedDay = (value: string) =>
  new Date(value).toLocaleDateString('ko-KR', { timeZone: 'Asia/Seoul' });

export function ExhibitionOverview({
  detail,
  demo,
  visits,
  facts,
}: {
  detail: ExhibitionDetail;
  demo: boolean;
  visits: string[][];
  facts: string[][];
}) {
  const { item, content } = detail;
  const [imageFailed, setImageFailed] = useState(false);
  const note = (kind: string) => content?.visit_notes.find((entry) => entry.kind === kind)?.text;
  const displayedVisits = visits.flatMap(([label, value, state]) => {
    if (state === 'CONFLICT') return [[label, value]];
    const reviewed = note(noteKinds[label]);
    if (reviewed && (state !== 'CONFIRMED' || label === '운영일·시간')) return [[label, reviewed]];
    return state === 'CONFIRMED' ? [[label, value]] : [];
  });
  const displayedFacts = facts.filter(([, , state]) => state !== 'UNKNOWN');
  const age = note('AGE');
  if (age && !displayedFacts.some(([label]) => label === '연령 조건'))
    displayedVisits.push(['관람 연령', age]);
  return (
    <>
      <div className="exhibition-meta">
        <span className={`status-tag status-${item.lifecycle.toLowerCase()}`}>
          {states[item.lifecycle]}
        </span>
        <p>
          <CalendarDays size={17} aria-hidden="true" />
          <span>
            {day(item.startDate)} — {day(item.endDate)}
          </span>
        </p>
        <p>
          <MapPin size={17} aria-hidden="true" />
          <span>
            {item.area} {item.district} · {note('LOCATION') ?? item.venue}
          </span>
        </p>
      </div>
      <div className="exhibition-reading-grid">
        <section className="exhibition-story" aria-labelledby="exhibition-story-title">
          {item.image && !imageFailed && (
            <figure className="exhibition-image">
              <img
                src={item.image}
                alt={`${item.title} 공식 이미지`}
                referrerPolicy="no-referrer"
                onError={() => setImageFailed(true)}
              />
              {item.credit && <figcaption>{item.credit}</figcaption>}
            </figure>
          )}
          <span className="editorial-label">ABOUT THE EXHIBITION</span>
          <h2 id="exhibition-story-title">어떤 전시인가요?</h2>
          {content ? (
            <>
              <p className="exhibition-introduction">{content.introduction}</p>
              {content.highlights.length > 0 && (
                <div className="exhibition-highlights">
                  <h3>눈여겨볼 이야기</h3>
                  <ul>
                    {content.highlights.map((highlight) => (
                      <li key={highlight}>{highlight}</li>
                    ))}
                  </ul>
                </div>
              )}
              <p className="exhibition-attribution">
                {content.source_owner} 전시 안내를 바탕으로 정리했습니다.
                <br />
                <time dateTime={content.reviewed_at}>{checkedDay(content.reviewed_at)} 확인</time>
              </p>
            </>
          ) : (
            <p className="exhibition-introduction">전시 소개를 준비하고 있어요.</p>
          )}
          {demo && <p className="detail-note">가상 전시 · UI 체험용</p>}
        </section>
        <section className="detail-facts exhibition-visit" aria-labelledby="visit-title">
          <h2 id="visit-title">관람 안내</h2>
          {displayedVisits.length > 0 && (
            <dl>
              {displayedVisits.map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          )}
          {displayedFacts.length > 0 && (
            <>
              <h3>접근성·감각 정보</h3>
              <dl>
                {displayedFacts.map(([label, value]) => (
                  <div key={label}>
                    <dt>{label}</dt>
                    <dd>{value}</dd>
                  </div>
                ))}
              </dl>
            </>
          )}
          <div className="exhibition-official">
            <p>
              {displayedVisits.length
                ? '방문 전 변경 사항과 예약·접근성 등 추가 안내를 확인해 주세요.'
                : '관람료·운영시간·예약 등 아직 확인하지 못한 정보는 공식 안내에서 확인해 주세요.'}
            </p>
            {!demo && (
              <a
                className="secondary-button"
                href={item.officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                referrerPolicy="no-referrer"
              >
                공식 전시 안내 <ArrowUpRight size={17} aria-hidden="true" />
              </a>
            )}
          </div>
          {!demo &&
            detail.visit_information.reservation.state === 'CONFIRMED' &&
            detail.visit_information.reservation.official_urls
              .filter((url) => url !== item.officialUrl)
              .map((url) => (
                <a
                  key={url}
                  className="text-button"
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  referrerPolicy="no-referrer"
                >
                  공식 예약 안내 ↗
                </a>
              ))}
          <details className="source-details">
            <summary>출처와 확인 정보</summary>
            <p>
              기간·장소: {item.sourceOwner} · {checkedDay(item.verifiedAt)} 확인
            </p>
            {item.freshness === 'STALE' && <p>기간·장소 정보는 재확인이 필요합니다.</p>}
            {content && (
              <p>
                소개·관람 안내: {content.source_owner} · {checkedDay(content.reviewed_at)} 확인
              </p>
            )}
            {[
              ...detail.visit_information.price.evidence,
              ...detail.visit_information.reservation.evidence,
              ...detail.visit_information.duration.evidence,
              ...detail.visit_information.accessibility.flatMap((fact) => fact.evidence),
              ...detail.visit_information.sensory.flatMap((fact) => fact.evidence),
              ...detail.operating_schedule.rules.map((rule) => rule.evidence),
            ].map((proof, index) => (
              <p key={index}>
                {proof.source.source_owner} ·{' '}
                {proof.scope === 'INSTITUTION' ? '기관 공통 안내' : '전시 안내'} ·{' '}
                {checkedDay(proof.verified_at)}
              </p>
            ))}
          </details>
        </section>
      </div>
    </>
  );
}
