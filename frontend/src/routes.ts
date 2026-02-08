import { SiteConfig } from "./config";
import { joinURL, normalizePath } from "./utils/basic";

const basePath = SiteConfig.websiteReactBasePath;

export const ROUTES = {
  DASHBOARD: normalizePath(`/${basePath}/dashboard`),
  MANAGE: normalizePath(`/${basePath}/manage`),
  PURCHASE: normalizePath(`/${basePath}/purchase`),
  // A redirect proxy from react-ts project => static docs by refresh window(jump out SPA)
  JUMP_OUT_REDIRECT: normalizePath(`/${basePath}/jo`),
};


const API_ROUTES = {
  USER_SUPERTOKENS_INFO: "/user/get-supertokens-info",
  USER_DB_INFO: "/user/get",
  PURCHASE_BY_CODE: "/user/purchase-by-code",
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

/******
 * Used to Jump out the SPA site (let the Nginx to re-decide the actual source)
 */
export class JumpOutSPARouteLogic {
  static readonly REDIRECT_RELATIVE_URL_PREFIX = `${ROUTES.JUMP_OUT_REDIRECT}?s=`;

  /***
   * Generate redirect relative (not targeted for full href) url.
   * @param quotedRedirectURL quoted relative url. 
   *                          BUT IN FACT you can just set any value here because 
   *                          it can handle this condition.
   */
  static genRedirectRelativeURL(quotedRedirectURL: string): string {
    return `${JumpOutSPARouteLogic.REDIRECT_RELATIVE_URL_PREFIX}${quotedRedirectURL}`;
  }

  /*****
   * A helper function
   */
  static genRedirect2DocRoot(): string {
    return JumpOutSPARouteLogic.genRedirectRelativeURL(SiteConfig.websiteDocRootPath);
  }

  /*****A helper function */
  static genRedirect2IndexRoot(): string {
    return JumpOutSPARouteLogic.genRedirectRelativeURL(SiteConfig.websiteIndexRootPath);
  }

  static extractRedirectURLAndUnquote(s: string): string {
    // manually split string, instead of using URLSearchParams
    // in case the original redirect url isn't quoted properly.

    const qIndex = s.indexOf(JumpOutSPARouteLogic.REDIRECT_RELATIVE_URL_PREFIX);
    if (qIndex == -1) {
      return null;
    }
    const vIndex = qIndex + JumpOutSPARouteLogic.REDIRECT_RELATIVE_URL_PREFIX.length;
    const quotedV = s.slice(vIndex);
    try {
      return decodeURIComponent(quotedV);
    } catch (error) {
      console.error("JumpOutSPARouteLogic: failed to decode quoted url: ", quotedV, "error=", error, ", return raw");
      return quotedV;
    }
  }
}

/***
 * Check if pathname startswith basePath. 
 * useful when redirect on unknown url.
 */
export function isPathPrefixBelongsToSPA(pathname: string): boolean {
  const trimSlashBase = basePath.replace(/^\/+/, "");
  const trimSlashPath = pathname.replace(/^\/+/, "");
  return trimSlashPath.startsWith(trimSlashBase);
}