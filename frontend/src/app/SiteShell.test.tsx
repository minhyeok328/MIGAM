import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { SiteShell } from './SiteShell';

function shell(currentPage: 'home' | 'discover' = 'home') {
  return (
    <SiteShell currentPage={currentPage} tone="limestone">
      <main id="main-content">본문</main>
    </SiteShell>
  );
}

function scrollTo(y: number) {
  vi.stubGlobal('scrollY', y);
  fireEvent.scroll(window);
}

beforeEach(() => {
  vi.stubGlobal('innerWidth', 1280);
  vi.stubGlobal('scrollY', 0);
});

afterEach(() => vi.unstubAllGlobals());

describe('home header sizing', () => {
  it('compacts after scrolling and restores near the top without toggling around the threshold', () => {
    render(shell());
    const header = screen.getByRole('banner');

    expect(header).not.toHaveClass('site-header-compact');
    scrollTo(160);
    expect(header).toHaveClass('site-header-compact');
    scrollTo(100);
    expect(header).toHaveClass('site-header-compact');
    scrollTo(0);
    expect(header).not.toHaveClass('site-header-compact');
    scrollTo(100);
    expect(header).not.toHaveClass('site-header-compact');
  });

  it('uses a restored scroll position and keeps mobile at its normal height after resizing', () => {
    vi.stubGlobal('scrollY', 360);
    render(shell());
    const header = screen.getByRole('banner');

    expect(header).toHaveClass('site-header-compact');
    vi.stubGlobal('innerWidth', 700);
    fireEvent.resize(window);
    expect(header).not.toHaveClass('site-header-compact');
    scrollTo(500);
    expect(header).not.toHaveClass('site-header-compact');
    vi.stubGlobal('innerWidth', 1280);
    fireEvent.resize(window);
    expect(header).toHaveClass('site-header-compact');
  });

  it('returns to the fixed header on discovery even when arriving from a compact home header', () => {
    const { rerender } = render(shell());
    scrollTo(360);
    expect(screen.getByRole('banner')).toHaveClass('site-header-compact');

    rerender(shell('discover'));
    expect(screen.getByRole('banner')).not.toHaveClass('site-header-compact');
    scrollTo(500);
    expect(screen.getByRole('banner')).not.toHaveClass('site-header-compact');
  });

  it('removes its scroll and resize listeners on unmount', () => {
    const addListener = vi.spyOn(window, 'addEventListener');
    const removeListener = vi.spyOn(window, 'removeEventListener');
    const { unmount } = render(shell());
    const sizingListeners = addListener.mock.calls.filter(([event]) =>
      ['scroll', 'resize'].includes(event),
    );

    expect(sizingListeners.map(([event]) => event).sort()).toEqual(['resize', 'scroll']);
    unmount();
    for (const [event, listener] of sizingListeners) {
      expect(removeListener).toHaveBeenCalledWith(event, listener);
    }
  });
});
