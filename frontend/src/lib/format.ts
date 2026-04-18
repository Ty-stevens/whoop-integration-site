export function minutesLabel(minutes: number) {
  return `${Math.round(minutes)} min`;
}

export function secondsToDurationLabel(seconds: number) {
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder > 0 ? `${hours} hr ${remainder} min` : `${hours} hr`;
}

export function nullableNumberLabel(value: number | null, suffix = "") {
  return value === null ? "-" : `${Math.round(value)}${suffix}`;
}
