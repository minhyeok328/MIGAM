import { useState } from 'react';
import { usePersonal } from '../app/providers';
import type { TasteFeature } from '../features/personal/store';
import { ProductLayout } from './ProductLayout';
import { moods } from '../features/discovery/forms';

export const mediaLabels: Record<string, string> = {
  PAINTING: '회화',
  SCULPTURE: '조각',
  CRAFT: '공예',
  PHOTOGRAPHY: '사진',
  VIDEO: '영상',
  SOUND: '사운드',
  INSTALLATION: '설치',
  PERFORMANCE: '퍼포먼스',
  INTERACTIVE: '인터랙티브',
  MEDIA_ART: '미디어아트',
  DESIGN: '디자인',
  ARCHITECTURE: '건축',
};
const questions: {
  title: string;
  description: string;
  axis: TasteFeature['axis'];
  options: [string, string][];
}[] = [
  {
    title: '어떤 표현에 먼저 눈길이 가나요?',
    description: '좋아하는 매체를 모두 골라주세요.',
    axis: 'MEDIA_GROUP',
    options: Object.entries(mediaLabels).slice(0, 4),
  },
  {
    title: '움직임과 소리도 궁금한가요?',
    description: '직접 재생하지 않고 관심 있는 매체를 선택합니다.',
    axis: 'MEDIA_GROUP',
    options: Object.entries(mediaLabels).slice(4, 8),
  },
  {
    title: '공간과 새로운 기술 중 무엇이 끌리나요?',
    description: '모르는 매체는 건너뛰어도 괜찮아요.',
    axis: 'MEDIA_GROUP',
    options: Object.entries(mediaLabels).slice(8),
  },
  {
    title: '조용히 머무는 시간은 어떤가요?',
    description: '지금 원하는 감상 분위기를 골라주세요.',
    axis: 'MOOD',
    options: moods
      .filter((v) => ['CALM', 'REFLECTIVE'].includes(v.value))
      .map((v) => [v.value, v.label]),
  },
  {
    title: '공간에 푹 빠지는 경험은 어떤가요?',
    description: '여러 항목을 함께 선택할 수 있어요.',
    axis: 'MOOD',
    options: moods
      .filter((v) => ['IMMERSIVE', 'LIVELY'].includes(v.value))
      .map((v) => [v.value, v.label]),
  },
  {
    title: '직접 참여하거나 낯선 표현을 만나고 싶나요?',
    description: '선택하지 않은 항목을 싫어한다고 판단하지 않아요.',
    axis: 'MOOD',
    options: moods
      .filter((v) => ['PARTICIPATORY', 'EXPERIMENTAL'].includes(v.value))
      .map((v) => [v.value, v.label]),
  },
  {
    title: '한 번 더 만나고 싶은 재료는?',
    description: '앞에서 고른 매체를 더하거나 해제할 수 있어요.',
    axis: 'MEDIA_GROUP',
    options: Object.entries(mediaLabels).filter(([v]) =>
      ['PAINTING', 'SCULPTURE', 'CRAFT', 'PHOTOGRAPHY'].includes(v),
    ),
  },
  {
    title: '오늘의 감상 분위기를 다시 살펴볼까요?',
    description: '선택한 내용만 취향으로 저장하며 언제든 수정할 수 있어요.',
    axis: 'MOOD',
    options: moods.map((v) => [v.value, v.label]),
  },
];
export function TastePage() {
  const personal = usePersonal();
  const [selected, setSelected] = useState<TasteFeature[]>(personal.data.taste);
  const [step, setStep] = useState(0);
  const [done, setDone] = useState(false);
  const question = questions[step];
  function toggle(value: string) {
    setSelected((current) =>
      current.some((f) => f.axis === question.axis && f.value === value)
        ? current.filter((f) => !(f.axis === question.axis && f.value === value))
        : [...current, { axis: question.axis, value }],
    );
  }
  function save() {
    personal.setTaste(selected);
    setDone(true);
  }
  const label = (feature: TasteFeature) =>
    mediaLabels[feature.value] ??
    moods.find((m) => m.value === feature.value)?.label ??
    feature.value;
  return (
    <ProductLayout
      title={done ? '지금 끌리는 취향' : '나의 감각 찾기'}
      intro="정답은 없어요. 선택하지 않거나 건너뛴 답은 부정적인 신호로 쓰지 않습니다. 선택은 취향 저장을 누르면 이 브라우저에만 보관됩니다."
    >
      {done ? (
        <section className="taste-result">
          <h2>{selected.length ? '이런 표현에 마음이 머물렀어요.' : '아직 탐색이 적어요.'}</h2>
          <p>
            {selected.length
              ? selected.map(label).join(' · ')
              : '취향이 없어도 전시를 자유롭게 둘러볼 수 있어요.'}
          </p>
          <p>
            지역과 날짜를 정하기 전에는 취향과 가까운 전시를 안내합니다. 실제 방문 정보는 전시별로
            확인해주세요.
          </p>
          <div className="detail-actions">
            <a className="primary-button" href="/discover#recommend">
              취향과 가까운 전시 보기
            </a>
            <button
              className="secondary-button"
              onClick={() => {
                setDone(false);
                setStep(0);
              }}
            >
              선택 수정
            </button>
          </div>
        </section>
      ) : (
        <section className="taste-question">
          <p className="editorial-label" role="status">
            {step + 1} / {questions.length}
          </p>
          <progress value={step + 1} max={questions.length} aria-label="취향 테스트 진행" />
          <h2>{question.title}</h2>
          <p>{question.description}</p>
          <fieldset>
            <legend className="sr-only">취향 복수 선택</legend>
            <div className="taste-options">
              {question.options.map(([value, text]) => (
                <label key={value}>
                  <input
                    type="checkbox"
                    checked={selected.some((f) => f.axis === question.axis && f.value === value)}
                    onChange={() => toggle(value)}
                  />
                  <span>{text}</span>
                </label>
              ))}
            </div>
          </fieldset>
          <div className="detail-actions">
            <button
              className="secondary-button"
              disabled={step === 0}
              onClick={() => setStep((n) => n - 1)}
            >
              이전
            </button>
            {step < questions.length - 1 && (
              <>
                <button className="secondary-button" onClick={() => setStep((n) => n + 1)}>
                  건너뛰기
                </button>
                <button className="primary-button" onClick={() => setStep((n) => n + 1)}>
                  다음
                </button>
              </>
            )}
            <button className="secondary-button" onClick={save}>
              취향 저장
            </button>
            <a className="text-button" href="/discover">
              저장하지 않고 나가기
            </a>
          </div>
          <p className="detail-note">
            사용 권리가 확인된 작품 이미지가 없어 현재는 매체와 감상 상황으로 진행합니다.
          </p>
        </section>
      )}
    </ProductLayout>
  );
}
