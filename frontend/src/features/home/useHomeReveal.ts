import { useEffect, useRef } from 'react';

export function useHomeReveal() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root || typeof IntersectionObserver !== 'function') return;

    const elements = Array.from(root.querySelectorAll<HTMLElement>('[data-reveal]'));
    const revealed = new WeakSet<Element>();
    const preference = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    let observer: IntersectionObserver | undefined;

    const clear = () => {
      observer?.disconnect();
      elements.forEach((element) => element.removeAttribute('data-reveal-state'));
    };

    const observe = () => {
      clear();
      if (preference?.matches) return;

      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            if (!entry.isIntersecting) continue;
            revealed.add(entry.target);
            entry.target.setAttribute('data-reveal-state', 'visible');
            observer?.unobserve(entry.target);
          }
        },
        { rootMargin: '0px 0px -16px 0px', threshold: 0 },
      );

      for (const element of elements) {
        if (revealed.has(element)) continue;
        // Leave the initial viewport and restored scroll position immediately readable.
        if (element.getBoundingClientRect().top < window.innerHeight) {
          revealed.add(element);
          continue;
        }
        element.dataset.revealState = 'pending';
        observer.observe(element);
      }
    };

    observe();
    preference?.addEventListener('change', observe);
    return () => {
      clear();
      preference?.removeEventListener('change', observe);
    };
  }, []);

  return ref;
}
