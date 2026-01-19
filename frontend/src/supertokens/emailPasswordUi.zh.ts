// see https://supertokens.com/docs/references/frontend-sdks/prebuilt-ui/translations for details

export const ZhUiTrans: Record<string, string | undefined> = {
  // ===== Email & Password =====
  EMAIL_PASSWORD_EMAIL_LABEL: "邮箱",
  EMAIL_PASSWORD_EMAIL_PLACEHOLDER: "请输入邮箱地址",
  EMAIL_PASSWORD_PASSWORD_LABEL: "密码",
  EMAIL_PASSWORD_PASSWORD_PLACEHOLDER: "请输入密码",

  EMAIL_PASSWORD_SIGN_IN_FORGOT_PW_LINK: "忘记密码？",
  EMAIL_PASSWORD_SIGN_IN_SUBMIT_BTN: "登录",
  EMAIL_PASSWORD_SIGN_IN_WRONG_CREDENTIALS_ERROR: "邮箱或密码不正确",

  EMAIL_PASSWORD_SIGN_UP_SUBMIT_BTN: "注册",
  EMAIL_PASSWORD_EMAIL_ALREADY_EXISTS: "该邮箱已注册，请直接登录",

  // ===== Reset password (request) =====
  EMAIL_PASSWORD_RESET_HEADER_TITLE: "重置密码",
  EMAIL_PASSWORD_RESET_HEADER_SUBTITLE: "请输入你的邮箱，我们将向你发送重置链接",

  EMAIL_PASSWORD_RESET_SEND_FALLBACK_EMAIL: "邮箱",
  EMAIL_PASSWORD_RESET_SEND_BEFORE_EMAIL: "我们已向",
  EMAIL_PASSWORD_RESET_SEND_AFTER_EMAIL: "发送了一封重置密码的邮件",

  EMAIL_PASSWORD_RESET_RESEND_LINK: "重新发送",
  EMAIL_PASSWORD_RESET_SEND_BTN: "发送重置邮件",
  EMAIL_PASSWORD_RESET_SIGN_IN_LINK: "返回登录",

  // ===== Reset password (submit new password) =====
  EMAIL_PASSWORD_RESET_SUBMIT_PW_SUCCESS_HEADER_TITLE: "密码重置成功",
  EMAIL_PASSWORD_RESET_SUBMIT_PW_SUCCESS_DESC: "你的密码已更新，现在可以使用新密码登录",
  EMAIL_PASSWORD_RESET_SUBMIT_PW_SUCCESS_SIGN_IN_BTN: "前往登录",

  EMAIL_PASSWORD_NEW_PASSWORD_LABEL: "新密码",
  EMAIL_PASSWORD_NEW_PASSWORD_PLACEHOLDER: "请输入新密码",
  EMAIL_PASSWORD_CONFIRM_PASSWORD_LABEL: "确认密码",
  EMAIL_PASSWORD_CONFIRM_PASSWORD_PLACEHOLDER: "请再次输入密码",

  EMAIL_PASSWORD_RESET_SUBMIT_PW_HEADER_TITLE: "设置新密码",
  EMAIL_PASSWORD_RESET_SUBMIT_PW_HEADER_SUBTITLE: "请输入并确认你的新密码",
  EMAIL_PASSWORD_RESET_SUBMIT_PW_CHANGE_PW_BTN: "确认修改",

  EMAIL_PASSWORD_RESET_PASSWORD_INVALID_TOKEN_ERROR: "重置链接无效或已过期",

  // ===== Field / validation errors =====
  ERROR_EMAIL_NON_STRING: "邮箱格式不正确",
  ERROR_EMAIL_INVALID: "请输入有效的邮箱地址",
  ERROR_PASSWORD_NON_STRING: "密码格式不正确",
  ERROR_PASSWORD_TOO_SHORT: "密码长度至少为 8 位",
  ERROR_PASSWORD_TOO_LONG: "密码长度不能超过 100 位",
  ERROR_PASSWORD_NO_ALPHA: "密码需包含至少一个字母",
  ERROR_PASSWORD_NO_NUM: "密码需包含至少一个数字",
  ERROR_CONFIRM_PASSWORD_NO_MATCH: "两次输入的密码不一致",
  ERROR_NON_OPTIONAL: "该字段为必填项",

  // ===== Raw backend error string overrides =====
  "This email already exists. Please sign in instead.": "该邮箱已注册，请直接登录",
  "Field is not optional": "该字段为必填项",
  "Password must contain at least 8 characters, including a number": "密码至少 8 位，并包含数字",
  "Password's length must be lesser than 100 characters": "密码长度不能超过 100 位",
  "Password must contain at least one alphabet": "密码需包含至少一个字母",
  "Password must contain at least one number": "密码需包含至少一个数字",
  "Email is invalid": "邮箱地址无效",

  "Reset password link was not created because of account take over risk. Please contact support. (ERR_CODE_001)":
    "出于安全原因，无法发送重置链接，请联系支持",

  "Cannot sign up due to security reasons. Please try logging in, use a different login method or contact support. (ERR_CODE_007)":
    "出于安全原因，无法注册账号，请尝试登录或联系支持",

  "Cannot sign in due to security reasons. Please try resetting your password, use a different login method or contact support. (ERR_CODE_008)":
    "出于安全原因，无法登录，请尝试重置密码或联系支持",

  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_009)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_010)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_011)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_012)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_013)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_014)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_015)":
    "出于安全原因，无法登录或注册，请联系支持",
  "Cannot sign in / up due to security reasons. Please contact support. (ERR_CODE_016)":
    "出于安全原因，无法登录或注册，请联系支持",

  // ===== Email verification =====
  EMAIL_VERIFICATION_RESEND_SUCCESS: "验证邮件已重新发送",
  EMAIL_VERIFICATION_SEND_TITLE: "验证你的邮箱",
  EMAIL_VERIFICATION_SEND_DESC_START: "我们已向",
  EMAIL_VERIFICATION_SEND_DESC_STRONG: "你的邮箱",
  EMAIL_VERIFICATION_SEND_DESC_END: "发送了一封验证邮件，请查收",

  EMAIL_VERIFICATION_RESEND_BTN: "重新发送验证邮件",
  EMAIL_VERIFICATION_LOGOUT: "退出登录",

  EMAIL_VERIFICATION_SUCCESS: "邮箱验证成功",
  EMAIL_VERIFICATION_CONTINUE_BTN: "继续",
  EMAIL_VERIFICATION_CONTINUE_LINK: "继续",

  EMAIL_VERIFICATION_EXPIRED: "验证链接已过期",
  EMAIL_VERIFICATION_ERROR_TITLE: "验证失败",
  EMAIL_VERIFICATION_ERROR_DESC: "验证链接无效或已过期，请重新发送验证邮件",

  EMAIL_VERIFICATION_LINK_CLICKED_HEADER: "邮箱验证成功",
  EMAIL_VERIFICATION_LINK_CLICKED_DESC: "你的邮箱已成功验证",
  EMAIL_VERIFICATION_LINK_CLICKED_CONTINUE_BUTTON: "继续",

  // ===== Auth page shell =====
  AUTH_PAGE_HEADER_TITLE_SIGN_IN_AND_UP: "登录或注册",
  AUTH_PAGE_HEADER_TITLE_SIGN_IN: "登录",
  AUTH_PAGE_HEADER_TITLE_SIGN_UP: "注册",
  AUTH_PAGE_HEADER_TITLE_SIGN_IN_UP_TO_APP: "登录以继续使用应用",

  AUTH_PAGE_HEADER_SUBTITLE_SIGN_IN_START: "还没有账号？",
  AUTH_PAGE_HEADER_SUBTITLE_SIGN_IN_SIGN_UP_LINK: "立即注册",
  AUTH_PAGE_HEADER_SUBTITLE_SIGN_IN_END: "",

  AUTH_PAGE_HEADER_SUBTITLE_SIGN_UP_START: "已经有账号？",
  AUTH_PAGE_HEADER_SUBTITLE_SIGN_UP_SIGN_IN_LINK: "去登录",
  AUTH_PAGE_HEADER_SUBTITLE_SIGN_UP_END: "",

  AUTH_PAGE_FOOTER_START: "继续即表示你同意",
  AUTH_PAGE_FOOTER_TOS: "服务条款",
  AUTH_PAGE_FOOTER_AND: "和",
  AUTH_PAGE_FOOTER_PP: "隐私政策",
  AUTH_PAGE_FOOTER_END: "",

  DIVIDER_OR: "或",

  BRANDING_POWERED_BY_START: "技术支持：",
  BRANDING_POWERED_BY_END: " - fseasy",

  SOMETHING_WENT_WRONG_ERROR: "出了点问题",
  SOMETHING_WENT_WRONG_ERROR_RELOAD: "请刷新页面后重试",
};
