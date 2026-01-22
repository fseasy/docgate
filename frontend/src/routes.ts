import { SiteConfig } from "./config";

const basePath = SiteConfig.websiteCommonBasePath;

export const ROUTES = {
  DASHBOARD: `/${basePath}/dashboard`,
  MANAGE: `/${basePath}/manage`,
  PURCHASE: `/${basePath}/purchase`
};
