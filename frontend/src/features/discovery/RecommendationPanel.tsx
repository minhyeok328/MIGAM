import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { ArrowUpRight, Info } from 'lucide-react';
import { useDiscovery } from '../../app/providers';
import { areas, moods, accessibilityOptions, sensoryOptions, reservationOptions } from './forms';
import { ConditionDialog } from './ConditionDialog';
import { ExhibitionCard } from '../../entities/ExhibitionCard';
import { EmptyState, ErrorNotice, FormError, LoadingState } from '../../shared/ui/Feedback';

export function RecommendationPanel() {
  const { state, api, demo } = useDiscovery();
  const [error, setError] = useState('');
  const draft = state.recommendationDraft;
  const query = useQuery({
    queryKey: ['recommendations', state.recommendationRevision],
    queryFn: ({ signal }) => api.recommend(state.recommendationRequest, signal),
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
          <span className="editorial-label">01 / VISIT</span>
          <h2>언제, 어디에서 만나볼까요?</h2>
          <span>선택한 방문 조건은 필수로 지켜요</span>
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
            방문 시작일
            <input
              type="date"
              value={draft.start}
              onChange={(e) => state.setRecommendation({ start: e.target.value })}
            />
          </label>
          <label className="field">
            방문 종료일
            <input
              type="date"
              value={draft.end}
              onChange={(e) => state.setRecommendation({ end: e.target.value })}
            />
          </label>
          <label className="field">
            최대 예산 (원)
            <input
              type="number"
              min="0"
              step="1"
              value={draft.budget}
              placeholder="제한 없음 · 무료는 0"
              onChange={(e) => state.setRecommendation({ budget: e.target.value })}
            />
          </label>
        </div>
        <p className="helper-note">
          날짜는 전시 기간과 비교합니다. 휴관일·개관 시간·예약 가능 여부는 공식 페이지에서
          확인해주세요.
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
            <span className="editorial-label">SELECTED FOR YOUR VISIT</span>
            <h2>이런 전시는 어떠세요?</h2>
          </div>
          <p role="status">
            {query.data ? `${query.data.recommendations.length}개의 추천` : '추천 준비 중'}
          </p>
        </div>
        <div className="applied-tags" aria-label="적용한 추천 조건">
          <span>
            {applied.region
              ? `${applied.region.area} ${applied.region.district ?? ''}`
              : '모든 지역'}
          </span>
          {applied.visit_dates && (
            <span>
              {applied.visit_dates.start} — {applied.visit_dates.end}
            </span>
          )}
          {applied.max_budget_krw !== undefined && (
            <span>최대 {applied.max_budget_krw.toLocaleString()}원</span>
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
          {applied.reservation && (
            <span>
              {applied.reservation.types.map((value) => reservationOptions[value]).join(', ')} ·{' '}
              {applied.reservation.mode === 'REQUIRED' ? '필수' : '선호'}
            </span>
          )}
          {applied.duration && (
            <span>
              관람시간{' '}
              {applied.duration.minimum_minutes !== undefined &&
                `${applied.duration.minimum_minutes}분 이상 `}
              {applied.duration.maximum_minutes !== undefined &&
                `${applied.duration.maximum_minutes}분 이하 `}
              · {applied.duration.mode === 'REQUIRED' ? '필수' : '선호'}
            </span>
          )}
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
          전시 기간 기준의 추천입니다. 실제 개관 여부는 방문 전에 확인해주세요.
        </p>
        {query.isPending && <LoadingState />}
        {query.isError && <ErrorNotice error={query.error} retry={() => void query.refetch()} />}
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
