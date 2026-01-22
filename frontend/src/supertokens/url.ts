import { SiteConfig } from "../config";

export function customizeAuthURL(options: {
  show: "signin" | "signup";
  queryParams?: Record<string, string | number | boolean | undefined>;
}) {
  const { show, queryParams } = options;

  // Prefer window.location.origin, just in case. In most cases, it equals site.websiteDomain
  const domain = typeof window !== "undefined" ? window.location.origin : SiteConfig.websiteDomain;

  const url = new URL(SiteConfig.websiteAuthBasePath, domain);
  url.searchParams.set("show", show);
  if (queryParams) {
    for (const [key, value] of Object.entries(queryParams)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}
