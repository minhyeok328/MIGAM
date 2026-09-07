import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, Info } from 'lucide-react';
import { useDiscovery, usePersonal } from '../../app/providers';
import { recommendationSignals } from '../personal/store';
import { areas, moods, accessibilityOptions, sensoryOptions } from './forms';
import { ConditionDialog } from './ConditionDialog';
import { ExhibitionCard } from '../../entities/ExhibitionCard';
import { EmptyState, ErrorNotice, FormError, LoadingState } from '../../shared/ui/Feedback';
import type { TasteFeature } from '../personal/store';

export function RecommendationPanel() {
  const { state, api, demo } = useDiscovery();
  const personal = usePersonal();
  const signals = recommendationSignals(personal.data);
  const preferences = [
    ...(signals.preferred_features ?? []),
    ...(state.recommendationRequest.preferred_features ?? []),
  ];
  const preferredFeatures = preferences.filter(
    (value, index) =>
      preferences.findIndex((other) => other.axis === value.axis && other.value === value.value) ===
      index,
  );
  const [error, setError] = useState('');
  const draft = state.recommendationDraft;
  const query = useQuery({
    queryKey: ['recommendations', state.recommendationRevision, personal.revision],
    queryFn: async ({ signal }) => {
      const artworkFeatures: TasteFeature[] = [];
      let skippedArtworks = 0;
      for (let offset = 0; offset < personal.data.artworks.length; offset += 8) {
        signal.throwIfAborted();
        const results = await Promise.allSettled(
          personal.data.artworks.slice(offset, offset + 8).map((id) => api.artwork(id, signal)),
        );
        for (const result of results) {
          if (result.status !== 'fulfilled' || result.value.artwork.is_demo !== demo) {
            skippedArtworks++;
            continue;
          }
          artworkFeatures.push(
            ...result.value.artwork.features.map(({ axis, value }) => ({ axis, value })),
          );
        }
      }
      signal.throwIfAborted();
      const allFeatures = [...preferredFeatures, ...artworkFeatures];
      const uniqueFeatures = allFeatures
        .filter(
          (feature, index) =>
            allFeatures.findIndex(
              (other) => other.axis === feature.axis && other.value === feature.value,
            ) === index,
        )
        .slice(0, 100);
      const result = await api.recommend(
        {
          ...signals,
          ...state.recommendationRequest,
          ...(uniqueFeatures.length ? { preferred_features: uniqueFeatures } : {}),
        },
        signal,
      );
      return { ...result, skippedArtworks };
    },
  });
  const applied = state.recommendationRequest;
  return (
    <>
      <form
        className="recommend-form"
        autoComplete="off"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          try {
            state.applyRecommendation();
            setError('');
          } catch (e) {
            setError((e as Error).message);
          }
        }}
      >
        <div className="form-section-label">
          <span className="editorial-label">01 / DISCOVER</span>
          <h2>어느 기간, 어느 지역의 전시를 찾나요?</h2>
          <span>선택한 기간과 지역의 전시를 찾아요</span>
        </div>
        <div className="filter-grid recommendation-filters">
          <label className="field">
            시·도
            <select
              value={draft.area}
              onChange={(e) => state.setRecommendation({ area: e.target.value, district: '' })}
            >
              <option value="">모든 지역</option>
              {areas.map((area) => (
                <option key={area}>{area}</option>
              ))}
            </select>
          </label>
          <label className="field">
            시·군·구
            <input
              maxLength={100}
              disabled={!draft.area}
              value={draft.district}
              placeholder="전체"
              onChange={(e) => state.setRecommendation({ district: e.target.value })}
            />
          </label>
          <label className="field">
            찾을 기간 시작일
            <input
              type="date"
              value={draft.start}
              onChange={(e) => state.setRecommendation({ start: e.target.value })}
            />
          </label>
          <label className="field">
            찾을 기간 종료일
            <input
              type="date"
              value={draft.end}
              onChange={(e) => state.setRecommendation({ end: e.target.value })}
            />
          </label>
        </div>
        <p className="helper-note">
          선택 기간에 열리는 전시를 찾아요. 날짜는 전시 기간 기준이며, 휴관일·운영시간·예약은 각
          전시의 공식 안내에서 확인해주세요.
        </p>
        <fieldset className="mood-section">
          <legend>
            <span className="editorial-label">02 / FEELING</span>
            <span>지금 끌리는 분위기가 있나요?</span>
          </legend>
          <p>
            선택하지 않아도 괜찮아요. 분위기는 필수가 아닌 선호예요.{' '}
            <span>{draft.moods.length}/3 선택</span>
          </p>
          <div className="mood-grid">
            {moods.map((mood) => (
              <label
                key={mood.value}
                className={`mood-option ${draft.moods.includes(mood.value) ? 'selected' : ''}`}
              >
                <input
                  type="checkbox"
                  checked={draft.moods.includes(mood.value)}
                  disabled={draft.moods.length >= 3 && !draft.moods.includes(mood.value)}
                  onChange={() =>
                    state.setRecommendation({
                      moods: draft.moods.includes(mood.value)
                        ? draft.moods.filter((value) => value !== mood.value)
                        : [...draft.moods, mood.value],
                    })
                  }
                />
                <span>
                  <strong>{mood.label}</strong>
                  <small>{mood.description}</small>
                </span>
              </label>
            ))}
          </div>
        </fieldset>
        <div className="recommend-actions">
          <ConditionDialog />
          <p>
            지금의 선택만 사용해요.
            <br />
            입력한 조건은 저장하지 않습니다.
          </p>
          <button className="primary-button" type="submit">
            이 조건으로 추천받기
            <ArrowUpRight size={20} aria-hidden="true" />
          </button>
        </div>
        <FormError message={error} />
      </form>
      <section className="results-section" aria-label="추천 전시">
        <div className="section-heading">
          <div>
            <span className="editorial-label">SELECTED FOR YOU</span>
            <h2>이런 전시는 어떠세요?</h2>
          </div>
          <p role="status">
            {query.data ? `${query.data.recommendations.length}개의 추천` : '추천 준비 중'}
          </p>
        </div>
        <div className="applied-tags" aria-label="적용한 추천 조건">
          {!!personal.data.taste.length && <span>저장한 취향 반영</span>}
          {!!personal.data.artworks.length && <span>관심 작품의 확인된 특성 반영</span>}
          {!!personal.data.exhibitions.length && <span>관심 전시 반영</span>}
          {!!personal.data.institutions.length && <span>관심 기관 반영</span>}
          <span>
            {applied.region
              ? `${applied.region.area} ${applied.region.district ?? ''}`
              : '모든 지역'}
          </span>
          {applied.exhibition_dates && (
            <span>
              전시 기간 {applied.exhibition_dates.start} — {applied.exhibition_dates.end}
            </span>
          )}
          {Object.entries(accessibilityOptions)
            .filter(([code]) => applied.required_accessibility?.some((value) => value === code))
            .map(([code, label]) => (
              <span key={code}>{label} · 필수</span>
            ))}
          {Object.entries(sensoryOptions)
            .filter(([code]) => applied.avoided_sensory?.some((value) => value === code))
            .map(([code, label]) => (
              <span key={code}>{label} 회피 · 필수</span>
            ))}
          {moods
            .filter((mood) =>
              applied.preferred_features?.some(
                (feature) => feature.axis === 'MOOD' && feature.value === mood.value,
              ),
            )
            .map((mood) => (
              <span key={mood.value}>{mood.label} · 선호</span>
            ))}
        </div>
        <p className="result-caution">
          {applied.exhibition_dates
            ? '선택 기간과 전시 기간이 겹치는 전시입니다. 실제 개관일·운영시간·예약은 공식 안내에서 확인해주세요.'
            : '취향과 관심을 바탕으로 전시를 제안해요. 관람 정보는 상세와 공식 안내에서 확인해주세요.'}
        </p>
        {query.isPending && <LoadingState />}
        {query.isError && <ErrorNotice error={query.error} retry={() => void query.refetch()} />}
        {!!query.data?.skippedArtworks && (
          <p role="status">
            관심 작품 {query.data.skippedArtworks}개의 정보를 확인하지 못해 해당 작품의 특성은
            제외했어요.{' '}
            <button className="text-button" onClick={() => void query.refetch()}>
              다시 확인
            </button>
          </p>
        )}
        {query.data && !query.data.recommendations.length && <EmptyState recommendation />}
        <div className="results-grid editorial-results-grid">
          {query.data?.recommendations.map((item, index) => (
            <ExhibitionCard
              key={item.id}
              item={item}
              index={index}
              demo={demo}
              variant="editorial"
            />
          ))}
        </div>
      </section>
      {!!query.data?.needsVerification.length && (
        <section className="verification-section" aria-label="방문 전 확인이 필요한 전시">
          <div className="section-heading">
            <div>
              <span className="editorial-label">BEFORE YOUR VISIT</span>
              <h2>방문 전 확인이 필요한 전시</h2>
            </div>
            <Info size={24} strokeWidth={1.25} aria-hidden="true" />
          </div>
          <p className="result-caution">
            가격·예약·시간 정보가 부족해 주요 추천과 구분했어요. 선택한 필수조건을 충족한다고 볼 수
            없습니다.
          </p>
          <div className="results-grid editorial-results-grid verification-results-grid">
            {query.data.needsVerification.map((item, index) => (
              <ExhibitionCard
                key={item.id}
                item={item}
                index={index}
                demo={demo}
                variant="editorial"
              />
            ))}
          </div>
        </section>
      )}
    </>
  );
}
