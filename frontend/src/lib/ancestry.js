export const GENERATION_YEARS = 27; // rough average

export function yearsToGenerations(years) {
  return Math.round(years / GENERATION_YEARS);
}

export function ancestorSlots(generations) {
  // About 117 billion humans have ever lived, roughly 2^37
  if (generations > 36) return null;
  return 2 ** generations;
}

export function nearestMilestone(milestones, yearsAgo) {
  return milestones.reduce((best, m) =>
    Math.abs(m.yearsAgo - yearsAgo) < Math.abs(best.yearsAgo - yearsAgo) ? m : best
  );
}