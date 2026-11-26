// Narrowing helpers for analytics query rows. The generated row type for a query is only as precise
// as the typegen run (it needs the table to exist), so read fields through a runtime check.
export function firstRow(data: unknown): Record<string, unknown> | undefined {
  if (!Array.isArray(data)) return undefined;
  const first: unknown = data[0];
  return first !== null && typeof first === 'object' ? (first as Record<string, unknown>) : undefined;
}

export function stringField(row: Record<string, unknown> | undefined, key: string): string {
  const value = row?.[key];
  return typeof value === 'string' ? value : '';
}
