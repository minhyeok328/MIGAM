import { useEffect, useRef } from 'react';
import { AlertCircle, ArrowRight, SearchX } from 'lucide-react';
import { DiscoveryApiError } from '../api/client';

export function ErrorNotice({ error, retry }: { error: unknown; retry: () => void }) {
  return (
    <div className="feedback error-notice" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <div>
        <strong>전시 정보를 불러오지 못했어요.</strong>
        <p>
          {error instanceof DiscoveryApiError && error.kind === 'contract'
            ? '응답 형식을 확인할 수 없어 내용을 표시하지 않았어요. 입력한 조건은 유지됩니다.'
            : '로컬 API 연결을 확인해주세요. 입력한 조건과 이미 불러온 목록은 유지됩니다.'}
        </p>
      </div>
      <button className="text-button" type="button" onClick={retry}>
        다시 시도 <ArrowRight size={16} aria-hidden="true" />
      </button>
    </div>
  );
}
export function FormError({ message }: { message: string }) {
  const ref = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    if (message) ref.current?.focus();
  }, [message]);
  return message ? (
    <p ref={ref} tabIndex={-1} role="alert" className="form-error">
      {message}
    </p>
  ) : null;
}
export function EmptyState({ recommendation = false }: { recommendation?: boolean }) {
  return (
    <div className="empty-state" role="status">
      <SearchX size={28} strokeWidth={1.25} aria-hidden="true" />
      <h3>{recommendation ? '조건에 맞는 전시가 없어요.' : '찾으시는 전시나 기관이 없어요.'}</h3>
      <p>
        선택한 조건은 그대로 유지했습니다.
        <br />
        입력한 이름이나 조건을 직접 확인해주세요.
      </p>
    </div>
  );
}
export function LoadingState() {
  return (
    <div aria-live="polite">
      <p className="loading-label">전시를 불러오고 있어요.</p>
      <div className="results-grid" aria-hidden="true">
        {[0, 1, 2].map((key) => (
          <div key={key} className="skeleton-card" />
        ))}
      </div>
    </div>
  );
}
