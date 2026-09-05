const chapters = [
  {
    id: 'space-temperature',
    number: '01',
    title: '공간의 온도',
    description: '빛이 드는 방향과 여백 사이에서, 오래 머물고 싶은 공간을 찾아보세요.',
    src: '/assets/home/film/migam-film-05-glass-corridor-1920.webp',
    variant: 'space',
  },
  {
    id: 'lingering-gaze',
    number: '02',
    title: '머무는 시선',
    description: '한 걸음 멈춰 바라볼 때, 지나쳤던 작품이 새롭게 다가옵니다.',
    src: '/assets/home/film/migam-film-04-paused-gaze-1920.webp',
    variant: 'gaze',
  },
  {
    id: 'material-sense',
    number: '03',
    title: '재료의 감각',
    description: '종이의 결, 흙의 온기, 금속 위의 빛. 마음이 끌리는 작은 차이를 만나보세요.',
    src: '/assets/home/film/migam-film-03-material-study-1920.webp',
    variant: 'material',
  },
] as const;

export function VisualChapters() {
  return (
    <div className="visual-chapters">
      {chapters.map((chapter) => (
        <section
          key={chapter.id}
          className={`visual-chapter visual-chapter-${chapter.variant}`}
          aria-labelledby={`${chapter.id}-title`}
        >
          <div className="page-width visual-chapter-copy" data-reveal="up">
            <div className="visual-chapter-heading">
              <span className="visual-chapter-number" aria-hidden="true">
                {chapter.number}
              </span>
              <h2 id={`${chapter.id}-title`}>{chapter.title}</h2>
            </div>
            <p className="visual-chapter-description">{chapter.description}</p>
          </div>
          <figure className="visual-chapter-media" data-reveal="fade" aria-hidden="true">
            <img
              src={chapter.src}
              width="1920"
              height="1080"
              alt=""
              loading="lazy"
              decoding="async"
            />
          </figure>
        </section>
      ))}
    </div>
  );
}
