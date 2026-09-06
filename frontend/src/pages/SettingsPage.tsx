import { useRef, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { useQueryClient } from '@tanstack/react-query';
import { useDiscovery, usePersonal } from '../app/providers';
import {
  emptyRecommendationDraft,
  emptySearchDraft,
  buildSearchRequest,
} from '../features/discovery/forms';
import { ProductLayout } from './ProductLayout';

const scopes = {
  taste: ['취향 초기화', '취향 선택만 삭제합니다. 관심과 최근 기록은 유지됩니다.'],
  likes: ['관심 목록 초기화', '관심 전시·작품·기관을 삭제합니다. 취향과 최근 기록은 유지됩니다.'],
  recent: ['최근 본 기록 삭제', '최근 본 전시 기록만 삭제합니다. 취향과 관심은 유지됩니다.'],
  all: [
    '모든 로컬 데이터 삭제',
    '이 브라우저의 미감 취향·관심·최근 기록과 현재 창의 비교·검색·방문 조건을 삭제합니다. 삭제한 데이터는 복구할 수 없습니다.',
  ],
} as const;
export function SettingsPage() {
  const personal = usePersonal();
  const { store } = useDiscovery();
  const client = useQueryClient();
  const [scope, setScope] = useState<keyof typeof scopes | null>(null);
  const [message, setMessage] = useState('');
  const trigger = useRef<HTMLButtonElement>(null);
  return (
    <ProductLayout
      title="내 데이터 관리"
      intro="회원가입 없이 이용합니다. 취향·관심·최근 본 전시는 현재 브라우저에 저장되며 다른 기기로 동기화되지 않습니다."
    >
      <section className="settings-summary">
        <h2>이 브라우저에 저장된 항목</h2>
        <p>
          취향 선택 {personal.data.taste.length}개 · 관심 전시 {personal.data.exhibitions.length}개
          · 관심 작품 {personal.data.artworks.length}개 · 관심 기관{' '}
          {personal.data.institutions.length}개 · 최근 본 전시 {personal.data.recent.length}개
        </p>
        <p>
          관심은 종류별 최대 100개, 최근 기록은 최대 20개입니다. 검색어·위치·추천 요청은 저장하지
          않습니다. 브라우저 데이터를 지우면 함께 사라집니다.
        </p>
      </section>
      <div className="settings-actions">
        {Object.entries(scopes).map(([key, [label, description]]) => (
          <section key={key}>
            <div>
              <h2>{label}</h2>
              <p>{description}</p>
            </div>
            <button
              className="secondary-button"
              onClick={(event) => {
                trigger.current = event.currentTarget;
                setScope(key as keyof typeof scopes);
              }}
            >
              {label}
            </button>
          </section>
        ))}
      </div>
      <p role="status">{message}</p>
      <Dialog.Root
        open={scope !== null}
        onOpenChange={(open) => {
          if (!open) setScope(null);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content
            className="condition-dialog reset-dialog"
            onCloseAutoFocus={(event) => {
              event.preventDefault();
              trigger.current?.focus();
            }}
          >
            <Dialog.Title>{scope ? scopes[scope][0] : '데이터 삭제'}</Dialog.Title>
            <Dialog.Description>{scope ? scopes[scope][1] : ''}</Dialog.Description>
            <div className="detail-actions">
              <Dialog.Close asChild>
                <button className="secondary-button">취소</button>
              </Dialog.Close>
              <button
                className="primary-button"
                onClick={async () => {
                  if (!scope) return;
                  personal.clear(scope);
                  if (scope === 'all') {
                    await client.cancelQueries();
                    client.clear();
                    store.setState((s) => ({
                      tab: 'search',
                      searchDraft: { ...emptySearchDraft },
                      appliedSearchDraft: { ...emptySearchDraft },
                      searchRequest: buildSearchRequest(emptySearchDraft),
                      recommendationDraft: { ...emptyRecommendationDraft },
                      recommendationRequest: { limit: 6 },
                      searchRevision: s.searchRevision + 1,
                      recommendationRevision: s.recommendationRevision + 1,
                    }));
                  }
                  setMessage('선택한 데이터를 초기화했어요.');
                  setScope(null);
                }}
              >
                삭제하기
              </button>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </ProductLayout>
  );
}
