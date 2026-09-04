const chapters = [
  {
    id: 'space-temperature',
    number: '01',
    eyebrow: 'SPACE / LIGHT',
    title: '공간의 온도',
    statement: '빛의 결을 따라, 공간은 저마다 다른 온도를 남깁니다.',
    description: '넓이보다 오래 머물고 싶은 감각을 살펴봅니다.',
    src: '/assets/home/film/migam-film-05-glass-corridor-1920.webp',
    variant: 'space',
  },
  {
    id: 'lingering-gaze',
    number: '02',
    eyebrow: 'PAUSE / GAZE',
    title: '머무는 시선',
    statement: '한 걸음 멈춘 자리에서, 비로소 보이는 것이 있습니다.',
    description: '작품보다 먼저 마음이 머무는 순간을 따라갑니다.',
    src: '/assets/home/film/migam-film-04-paused-gaze-1920.webp',
    variant: 'gaze',
  },
  {
    id: 'material-sense',
    number: '03',
    eyebrow: 'MATERIAL / TOUCH',
    title: '재료의 감각',
    statement: '종이의 결, 흙의 온기, 금속의 고요를 가까이 봅니다.',
    description: '이름보다 표면과 빛에 끌리는 취향도 좋은 출발점입니다.',
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
          <div className="page-width visual-chapter-copy">
            <div className="visual-chapter-heading">
              <span className="visual-chapter-number">{chapter.number}</span>
              <div>
                <p className="editorial-label">{chapter.eyebrow}</p>
                <h2 id={`${chapter.id}-title`}>{chapter.title}</h2>
              </div>
            </div>
            <p className="visual-chapter-statement">{chapter.statement}</p>
            <p className="visual-chapter-description">{chapter.description}</p>
          </div>
          <figure className="visual-chapter-media" aria-hidden="true">
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
