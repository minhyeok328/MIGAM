import { useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { SlidersHorizontal, X } from 'lucide-react';
import { useDiscovery } from '../../app/providers';
import { FormError } from '../../shared/ui/Feedback';
import { areas, type SearchDraft } from './forms';

export function SearchFilterDialog({ count }: { count: number }) {
  const { state } = useDiscovery();
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState(state.appliedSearchDraft);
  const [error, setError] = useState('');
  const update = (patch: Partial<SearchDraft>) => setDraft((value) => ({ ...value, ...patch }));

  return (
    <Dialog.Root
      open={open}
      onOpenChange={(value) => {
        setDraft(state.appliedSearchDraft);
        setError('');
        setOpen(value);
      }}
    >
      <Dialog.Trigger asChild>
        <button className="search-filter-trigger" type="button">
          <SlidersHorizontal size={16} aria-hidden="true" />
          필터{count > 0 && <span className="condition-count">{count}</span>}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="condition-dialog search-filter-dialog">
          <div className="dialog-heading">
            <Dialog.Title>검색 필터</Dialog.Title>
            <Dialog.Close asChild>
              <button className="icon-button" type="button" aria-label="필터 닫기">
                <X size={22} aria-hidden="true" />
              </button>
            </Dialog.Close>
          </div>
          <Dialog.Description>필요한 조건만 골라주세요.</Dialog.Description>
          <form
            autoComplete="off"
            noValidate
            onSubmit={(event) => {
              event.preventDefault();
              try {
                state.refineSearch({
                  type: draft.type,
                  area: draft.area,
                  district: draft.district,
                  lifecycle: draft.lifecycle,
                });
                setOpen(false);
              } catch (e) {
                setError((e as Error).message);
              }
            }}
          >
            <div className="search-filter-fields">
              <label className="field">
                대상
                <select
                  value={draft.type}
                  onChange={(e) => update({ type: e.target.value as SearchDraft['type'] })}
                >
                  <option value="EXHIBITION">전시</option>
                  <option value="INSTITUTION">기관</option>
                  <option value="ALL">전체</option>
                </select>
              </label>
              <div className="filter-grid two-fields">
                <label className="field">
                  시·도
                  <select
                    value={draft.area}
                    onChange={(e) => update({ area: e.target.value, district: '' })}
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
                    placeholder="전체"
                    maxLength={100}
                    disabled={!draft.area}
                    value={draft.district}
                    onChange={(e) => update({ district: e.target.value })}
                  />
                </label>
              </div>
              <label className="field">
                전시 상태
                <select
                  value={draft.lifecycle}
                  aria-describedby="search-lifecycle-help"
                  onChange={(e) =>
                    update({ lifecycle: e.target.value as SearchDraft['lifecycle'] })
                  }
                >
                  <option value="DEFAULT">기본</option>
                  <option value="CURRENT">현재 전시</option>
                  <option value="UPCOMING">예정 전시</option>
                  <option value="ENDED">종료 전시</option>
                  <option value="CANCELED">취소된 전시</option>
                  <option value="ALL">모든 상태</option>
                </select>
              </label>
              <p id="search-lifecycle-help" className="search-filter-help">
                기본은 현재·예정 전시입니다. 검색어가 있으면 종료·취소된 전시도 포함합니다.
              </p>
            </div>
            <FormError message={error} />
            <div className="search-filter-actions">
              <Dialog.Close asChild>
                <button className="secondary-button" type="button">
                  취소
                </button>
              </Dialog.Close>
              <button className="primary-button" type="submit">
                필터 적용
              </button>
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
