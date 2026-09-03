import type { components } from '../shared/api/generated';

function duration(value: components['schemas']['DurationPreferenceRequest']) {
  return value;
}
duration({ mode: 'REQUIRED', minimum_minutes: 30 });
duration({ mode: 'PREFERRED', maximum_minutes: 90 });
duration({ mode: 'REQUIRED', minimum_minutes: 30, maximum_minutes: 90 });
// @ts-expect-error A duration must specify a numeric bound.
duration({ mode: 'REQUIRED' });
// @ts-expect-error The canonical mode is an enum, not arbitrary text.
duration({ mode: 'UNKNOWN', maximum_minutes: 90 });
// @ts-expect-error The canonical bound is a number.
duration({ mode: 'REQUIRED', maximum_minutes: '90' });
