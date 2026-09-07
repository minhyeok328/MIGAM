import * as Dialog from '@radix-ui/react-dialog';
import { SlidersHorizontal, X, ArrowRight } from 'lucide-react';
import { useDiscovery } from '../../app/providers';
import { accessibilityOptions, sensoryOptions } from './forms';

export function ConditionDialog() {
  const { state } = useDiscovery();
  const draft = state.recommendationDraft;
  const count = draft.accessibility.length + draft.sensory.length;
  function toggle(group: 'accessibility' | 'sensory', value: string) {
    state.setRecommendation({
      [group]: draft[group].includes(value)
        ? draft[group].filter((item) => item !== value)
        : [...draft[group], value],
    });
  }
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button type="button" className="secondary-button">
          <SlidersHorizontal size={17} aria-hidden="true" />
          자세한 조건{count > 0 && <span className="condition-count">{count}</span>}
        </button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="condition-dialog">
          <div className="dialog-heading">
            <span className="editorial-label">ACCESS & SENSORY</span>
            <Dialog.Close asChild>
              <button className="icon-button" type="button" aria-label="조건 패널 닫기">
                <X size={22} />
              </button>
            </Dialog.Close>
          </div>
          <Dialog.Title>접근성·감각 조건</Dialog.Title>
          <Dialog.Description>
            꼭 필요한 조건은 엄격하게 지켜요. 선택은 아래 추천 버튼을 누를 때 적용됩니다.
          </Dialog.Description>
          <fieldset className="condition-group">
            <legend>필수 접근성</legend>
            <p>확인되지 않은 전시는 추천과 확인 필요 목록 모두에서 제외합니다.</p>
            <div className="check-grid">
              {Object.entries(accessibilityOptions).map(([value, label]) => (
                <label key={value}>
                  <input
                    type="checkbox"
                    checked={draft.accessibility.includes(value)}
                    onChange={() => toggle('accessibility', value)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset className="condition-group">
            <legend>반드시 피할 감각 자극</legend>
            <p>해당 자극이 없다고 확인된 전시만 추천합니다.</p>
            <div className="check-grid">
              {Object.entries(sensoryOptions).map(([value, label]) => (
                <label key={value}>
                  <input
                    type="checkbox"
                    checked={draft.sensory.includes(value)}
                    onChange={() => toggle('sensory', value)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <Dialog.Close asChild>
            <button className="primary-button dialog-done" type="button">
              조건 선택 완료
              <ArrowRight size={18} aria-hidden="true" />
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
