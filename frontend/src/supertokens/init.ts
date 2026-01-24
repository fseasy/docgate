import SuperTokens, { } from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";
import { SiteConfig } from "../config";
import { ZhUiTrans } from "./emailPasswordUi.zh";
import { ROUTES, JumpOutSPARouteLogic } from "../routes";
import { extractURLPathname, normalizePath } from "../utils/basic";

export function initSuperTokens() {
  SuperTokens.init({
    appInfo: {
      appName: SiteConfig.appName,
      apiDomain: SiteConfig.apiDomain,
      websiteDomain: SiteConfig.websiteDomain,
      apiBasePath: SiteConfig.apiAuthBasePath,
      websiteBasePath: SiteConfig.websiteAuthBasePath,
    },
    recipeList: [customizedEmailPassword(), Session.init()],
    useShadowDom: false,
    languageTranslations: {
      translations: {
        zh: ZhUiTrans,
      },
      defaultLanguage: "zh",
    },
    getRedirectionURL: async (context) => {
      if (context.action === "SUCCESS") {
        const givenQuotedPath = context.redirectToPath;
        if (givenQuotedPath !== undefined) {
          // decide path target: SPA or static?
          const routeKey = getCorrespondingSPARoute(givenQuotedPath);
          if (routeKey === null) {
            // static! Let's proxy it to SPA's index4redirect page
            return JumpOutSPARouteLogic.genRedirectRelativeURL(givenQuotedPath);
          }
          // still in SPO, directly return
          return givenQuotedPath;
        }
      }
      // nothing. go to the jump out quote and redirect to website level root.
      return JumpOutSPARouteLogic.genRedirectRelativeURL("/");
    }
  });

  // SuperTokens.loadTranslation({
  //   "zh": ZhUiTrans
  // });

  // SuperTokens.changeLanguage("zh")
}

function customizedEmailPassword() {
  return EmailPassword.init({
    signInAndUpFeature: {
      signUpForm: {
        formFields: [
          {
            id: "password",
            label: "密码",
            validate: async (value) => {
              if (!value) return "请输入密码";
              if (/\s/.test(value)) return "密码不能包含空格或其他空白字符";
              if (value.length < 4) return "密码长度至少为 4 位";
              if (value.length > 32) return "密码长度最长 32 位";
              return undefined;
            },
          },
          {
            id: "confirm-password",
            label: "确认密码",
            optional: false,
            placeholder: "请再次输入以确认密码",
            validate: async (value) => {
              if (!value) return "请再次输入密码";
              if (typeof document === "undefined") return undefined;

              const pwdInput = document.querySelector(
                'input[data-supertokens="input input-password"][name="password"]',
              ) as HTMLInputElement | null;

              if (!pwdInput) return undefined;

              if (value !== pwdInput.value) {
                return "两次输入的密码不一致";
              }

              return undefined;
            },
            nonOptionalErrorMsg: "该字段不能为空",
          },
          {
            id: "invite-code",
            label: "预付款代码（也可后续购买)",
            placeholder: "如果您已提前购买，请输入获得的 code",
            optional: true,
            getDefaultValue: () => {
              if (typeof window === "undefined") {
                return "";
              }

              const params = new URLSearchParams(window.location.search);
              return params.get("ic") ?? "";
            },
          },
        ],
      },
    },
  });
}


const getCorrespondingSPARoute = (pathOrURL: string): keyof typeof ROUTES | null => {
  // NOTE: we don't consider cross-domain route in current situation.
  const exactPath = normalizePath(extractURLPathname(pathOrURL)); // normalize here due to ROUTES are normalized.
  for (const [key, value] of Object.entries(ROUTES)) {
    if (exactPath === value) {
      return key as keyof typeof ROUTES;
    }
  }
  return null;
};