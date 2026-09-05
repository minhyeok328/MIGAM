import { act, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useHomeReveal } from './useHomeReveal';

function HomeContent() {
  const ref = useHomeReveal();
  return (
    <main ref={ref}>
      <h2 data-reveal="up">미감의 관점</h2>
      <figure data-reveal="fade" aria-label="장식 사진" />
      <a href="/discover">전시 둘러보기</a>
    </main>
  );
}

function setupMotion({ reduce = false, top = 1200 } = {}) {
  let onIntersection: IntersectionObserverCallback;
  let onPreferenceChange: (event: MediaQueryListEvent) => void;
  const observer = { observe: vi.fn(), unobserve: vi.fn(), disconnect: vi.fn() };
  const createObserver = vi.fn(function (callback: IntersectionObserverCallback) {
    onIntersection = callback;
    return observer;
  });
  const preference = {
    matches: reduce,
    addEventListener: vi.fn((_: string, callback: typeof onPreferenceChange) => {
      onPreferenceChange = callback;
    }),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal('IntersectionObserver', createObserver);
  vi.stubGlobal(
    'matchMedia',
    vi.fn(() => preference),
  );
  vi.spyOn(Element.prototype, 'getBoundingClientRect').mockReturnValue({
    top,
    bottom: top + 100,
    left: 0,
    right: 100,
    width: 100,
    height: 100,
    x: 0,
    y: top,
    toJSON: () => ({}),
  });
  return {
    observer,
    preference,
    createObserver,
    enter: (target: Element) =>
      act(() =>
        onIntersection(
          [{ target, isIntersecting: true } as IntersectionObserverEntry],
          observer as unknown as IntersectionObserver,
        ),
      ),
    setReducedMotion: (matches: boolean) =>
      act(() => {
        preference.matches = matches;
        onPreferenceChange({ matches } as MediaQueryListEvent);
      }),
  };
}

afterEach(() => vi.unstubAllGlobals());

describe('home decorative reveals', () => {
  it('reveals offscreen decoration once and never defers a navigation link', () => {
    const motion = setupMotion();
    render(<HomeContent />);
    const heading = screen.getByRole('heading');
    const photo = screen.getByRole('figure');
    expect(heading).toHaveAttribute('data-reveal-state', 'pending');
    expect(photo).toHaveAttribute('data-reveal-state', 'pending');
    expect(screen.getByRole('link')).not.toHaveAttribute('data-reveal-state');
    motion.enter(heading);
    expect(heading).toHaveAttribute('data-reveal-state', 'visible');
    expect(motion.observer.unobserve).toHaveBeenCalledWith(heading);
  });

  it('keeps content already in the viewport immediately visible', () => {
    const motion = setupMotion({ top: 0 });
    render(<HomeContent />);
    expect(screen.getByRole('heading')).not.toHaveAttribute('data-reveal-state', 'pending');
    expect(motion.observer.observe).not.toHaveBeenCalled();
  });

  it('leaves content visible when the observation API is unavailable', () => {
    vi.stubGlobal('IntersectionObserver', undefined);
    render(<HomeContent />);
    expect(screen.getByRole('heading')).not.toHaveAttribute('data-reveal-state');
  });

  it('does not animate when reduced motion is already enabled', () => {
    const motion = setupMotion({ reduce: true });
    render(<HomeContent />);
    expect(motion.createObserver).not.toHaveBeenCalled();
    expect(screen.getByRole('heading')).not.toHaveAttribute('data-reveal-state');
  });

  it('reveals pending content immediately when reduced motion is enabled later', () => {
    const motion = setupMotion();
    render(<HomeContent />);
    motion.setReducedMotion(true);
    expect(screen.getByRole('heading')).not.toHaveAttribute('data-reveal-state');
    expect(screen.getByRole('figure')).not.toHaveAttribute('data-reveal-state');
    expect(motion.observer.disconnect).toHaveBeenCalled();
  });

  it('cleans up observers and media preference listeners on unmount', () => {
    const motion = setupMotion();
    const { unmount } = render(<HomeContent />);
    unmount();
    expect(motion.observer.disconnect).toHaveBeenCalled();
    expect(motion.preference.removeEventListener).toHaveBeenCalledWith(
      'change',
      expect.any(Function),
    );
  });

  it('does not hide a previously revealed section when motion preferences change twice', () => {
    const motion = setupMotion();
    render(<HomeContent />);
    const heading = screen.getByRole('heading');
    motion.enter(heading);
    motion.setReducedMotion(true);
    motion.setReducedMotion(false);
    expect(heading).not.toHaveAttribute('data-reveal-state', 'pending');
  });
});
