import { genWebsiteFullURL } from "../../routes";
import { JumpOutSPARouteLogic } from "../../routes";

export default function JumpOutSPA() {
  const redirectURL = JumpOutSPARouteLogic.extractRedirectURLAndUnquote(window.location.href);
  const from = window.location.pathname;
  const tURL = redirectURL || genWebsiteFullURL({ basePath: "/", queryParams: { from: from } });
  window.location.replace(tURL);
  return null;
}