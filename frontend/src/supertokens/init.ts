import SuperTokens, { } from "supertokens-auth-react";
import EmailPassword from "supertokens-auth-react/recipe/emailpassword";
import Session from "supertokens-auth-react/recipe/session";
import { SiteConfig } from "../config";
import { ZhUiTrans } from "./emailPasswordUi.zh";
import { ROUTES, JumpOutSPARouteLogic, QUERY_KEYS } from "../routes";
import { extractURLPathname, normalizePath } from "../utils/basic";
import EmailVerification from "supertokens-auth-react/recipe/emailverification";


export function initSuperTokens() {
  SuperTokens.init({
    appInfo: {
      appName: SiteConfig.appName,
      apiDomain: SiteConfig.apiDomain,
      websiteDomain: SiteConfig.websiteDomain,
      apiBasePath: SiteConfig.apiAuthBasePath,
      websiteBasePath: SiteConfig.websiteAuthBasePath,
    },
    style: customizeStyle(),
    recipeList: [
      EmailVerification.init({ mode: "REQUIRED" }),
      customizedEmailPassword(),
      Session.init(),
    ],
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
        } else {
          // no redirect path. Let's go to the doc root
          return JumpOutSPARouteLogic.genRedirect2DocRoot();
        }
      }
      // Fail. redirect to website level root to skip the auth loop.
      return JumpOutSPARouteLogic.genRedirect2IndexRoot();
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
            id: "prepaid-code",
            label: "预付款代码（也可后续购买)",
            placeholder: "如果您已提前购买，请输入获得的 code",
            optional: true,
            getDefaultValue: () => {
              if (typeof window === "undefined") {
                return "";
              }

              const params = new URLSearchParams(window.location.search);
              return params.get(QUERY_KEYS.PREPAID_CODE) ?? "";
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

const customizeStyle = () => {
  // 1. dark mode style
  // 2. add dynamic-dots animation when button disabled.
  return `
    @media (prefers-color-scheme: dark) {
        [data-supertokens~=container] {
          --palette-background: 51, 51, 51;
          --palette-inputBackground: 41, 41, 41;
          --palette-inputBorder: 41, 41, 41;
          --palette-textTitle: 255, 255, 255;
          --palette-textLabel: 255, 255, 255;
          --palette-textPrimary: 255, 255, 255;
          --palette-error: 173, 46, 46;
          --palette-textInput: 169, 169, 169;
          --palette-textLink: 114,114,114;
          --palette-textGray: 158, 158, 158;
          --palette-superTokensBrandingBackground: var(--palette-inputBackground);
          --palette-superTokensBrandingText: var(--palette-textInput);
        }
    }

    [data-supertokens~="button"]:disabled {
      /* This makes the "..." text invisible but keeps the button width */
      color: transparent !important;
      position: relative;
      cursor: wait;
    }

    /* 2. Overlay the new animation */
    [data-supertokens~="button"]:disabled::after {
      content: "";
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
      
      /* Text styling for your dots */
      color: rgb(var(--palette-buttonText)); /* Match your button text color */
      font-weight: bold;
      font-size: 1.2rem;
      letter-spacing: 2px;
      
      /* The Animation */
      animation: dynamicDots 1.5s infinite;
    }

    /* 3. The Keyframes for . -> .. -> ... */
    @keyframes dynamicDots {
      0%   { content: "."; }
      33%  { content: ".."; }
      66%  { content: "..."; }
      100% { content: "."; }
    }
  `;
};