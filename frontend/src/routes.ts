import { SiteConfig } from "./config";
import { joinURL, normalizePath } from "./utils/basic";

const basePath = SiteConfig.websiteCommonBasePath;

export const ROUTES = {
  DASHBOARD: normalizePath(`/${basePath}/dashboard`),
  MANAGE: normalizePath(`/${basePath}/manage`),
  PURCHASE: normalizePath(`/${basePath}/purchase`),
  INDEX_PROXY: '/', // A proxy from react-ts project => static docs
};


const API_ROUTES = {
  USER_SUPERTOKENS_INFO: "/user/get-supertokens-info",
  GEN_INVITE_CODE: "/admin/gen-invite-code",
} as const;

export type APIRouteName = keyof typeof API_ROUTES;

export const getApiURL = (name: APIRouteName): string => {
  const path = API_ROUTES[name];
  const finalUrl = joinURL(SiteConfig.apiDomain, SiteConfig.apiCommonBasePath, path);
  return finalUrl.toString();
};

/**  
 * Generate website full url on the base path.
 * NOTE: don't encode query params unless you intended to - encoding is already handled internally
 * 
 * @example
 * genWebsiteFullURL({basePath: "example/docs", queryParams: {from: "/abc"}})
 * -> SiteConfig.websiteDomain/example/docs?from=$2Fabc
**/
export function genWebsiteFullURL(options: {
  basePath: string;
  queryParams?: Record<string, string | number | boolean | undefined>;
}) {
  const { basePath, queryParams = {} } = options;

  // Prefer window.location.origin, just in case. In most cases, it equals site.websiteDomain
  const domain = typeof window !== "undefined" ? window.location.origin : SiteConfig.websiteDomain;

  const url = joinURL(domain, basePath);
  for (const [key, value] of Object.entries(queryParams)) {
    if (value !== undefined) {
      url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}
