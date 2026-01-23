import { SiteConfig } from "../config";
import { genWebsiteFullURL } from "../routes";

export function customizeAuthURL(options: {
  show: "signin" | "signup";
  queryParams?: Record<string, string | number | boolean | undefined>;
}) {
  const { show, queryParams = {} } = options;
  const updatedOptions = { show, ...queryParams };
  return genWebsiteFullURL({ basePath: SiteConfig.websiteAuthBasePath, queryParams: updatedOptions });
}
