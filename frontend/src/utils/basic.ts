/**
 * Safely joins a base URL with additional path segments.
 * Ensures the base path ends with '/' so relative paths are appended (not replaced).
 * 
 * NOTE: `base` must contain a host name, or exception will be thrown
 * 
 * @example
 * joinUrl('https://api.com/v1', 'users', '123') 
 * → 'https://api.com/v1/users/123'
 * 
 * @example
 * joinUrl(new URL('/api', 'https://site.com'), 'data')
 * → 'https://site.com/api/data'
 */
export function joinURL(
  base: string | URL,
  ...paths: Array<string | number>
): URL {
  const baseUrl = new URL(base.toString());

  // Normalize base path to end with '/' 
  // => NOTE this, if not ends with `/`, the following 
  // `new URL(relativePath, baseUrl)` will **replace** the path instead of append it.
  if (!baseUrl.pathname.endsWith('/')) {
    baseUrl.pathname += '/';
  }

  // Clean and join path segments
  const cleanPaths = paths
    .map(p => String(p).trim())
    .filter(p => p.length > 0)
    .map(p => p.replace(/^\/+|\/+$/g, '')); // Remove leading/trailing slashes

  const relativePath = cleanPaths.join('/');

  // Use URL constructor to resolve safely (handles encoding, etc.)
  return new URL(relativePath, baseUrl);
}

/***
 * normalize path.
 * It’s primarily intended for local file paths, 
 * but it’s safe to use in the URL path component—except when the path is empty.
 * => If path is empty, result will be `.` instead of `.` (following the posix logic.)
 */
export function normalizePath(p: string): string {
  // for windows compatibility
  const path = p.replace(/\\/g, '/');

  const segments = path.split('/');

  const stack: string[] = [];
  for (const seg of segments) {
    if (seg === '' || seg === '.') {
      continue;
    } else if (seg === '..') {
      stack.pop();
    } else {
      stack.push(seg);
    }
  }

  let result = stack.join('/');
  if (path.startsWith('/')) {
    result = '/' + result;
  }
  if (result === '') result = '.';

  return result;
}
