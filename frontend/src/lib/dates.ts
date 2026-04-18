function parseDate(value: string) {
  return new Date(`${value}T00:00:00`);
}

function toIsoDate(date: Date) {
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDateRangeLabel(startDate: string, endDate: string) {
  const start = parseDate(startDate);
  const end = parseDate(endDate);
  return `${start.toLocaleDateString(undefined, { month: "short", day: "numeric" })} to ${end.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric"
  })}`;
}

export function getNextMondayDate(baseDate = new Date()) {
  const day = baseDate.getDay();
  const offset = day === 1 ? 7 : (8 - day) % 7 || 7;
  const nextMonday = new Date(baseDate);
  nextMonday.setDate(baseDate.getDate() + offset);
  return toIsoDate(nextMonday);
}

export function formatLongDate(value: string) {
  return parseDate(value).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric"
  });
}
