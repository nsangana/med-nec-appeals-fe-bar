// Numeric / date formatting helpers. SQL DECIMAL/BIGINT can arrive as strings,
// so always coerce before formatting.
export const toNumber = (value: number | string | null | undefined): number =>
  value == null ? 0 : Number(value);

export const formatCurrency = (value: number | string | null | undefined): string =>
  toNumber(value).toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  });

export const formatDate = (value: string | null | undefined): string => {
  if (!value) return '—';
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

// Volume paths are stored fully-qualified; the files plugin routes take a path
// relative to the volume root. All appeal PDFs live at the volume root, so the
// basename is the relative path.
export const fileBasename = (path: string | null | undefined): string | null => {
  if (!path) return null;
  const parts = path.split('/').filter(Boolean);
  return parts.length ? parts[parts.length - 1] : null;
};
