import { getApiURL } from "../routes";

export interface StUser {
  id: string;
  isPrimaryUser: boolean;
  emails: string[];
  loginMethods: Record<string, unknown>[];
  timeJoined: number;
}

type GetUserRawResponse =
  | {
    error: null;
    user: StUser;
  }
  | {
    error: string;
    user: null;
  };

/**
 * Get Supertokens User info in the current session.
 * - You need session context to call this.
 *  */
export const fetchSessionSupertokensUserById = async (): Promise<StUser | null> => {
  try {
    const apiUrl = getApiURL("USER_SUPERTOKENS_INFO");
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: GetUserRawResponse = await response.json();
    if (data.error) {
      throw new Error(`Failed on server side, err=${data.error}`);
    }
    return data.user;
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`fetchSupertokensUserById failed: ${errMsg}`);
    return null;
  }
};

/** for both raw & api function response */
type PrepaidCodeResult =
  | {
    error: string;
  }
  | {
    error: null,
    code: string,
    lifetime: string;
  };

export const genPrepaidCode = async (): Promise<PrepaidCodeResult> => {

  const apiUrl = getApiURL("GEN_PREPAID_CODE");
  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: PrepaidCodeResult = await response.json();
    if (data.error !== null) {
      throw new Error(`Failed on server side, err=${data.error}`);
    }
    return { error: null, code: data.code, lifetime: data.lifetime };
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`genPrepaidCode failed: ${errMsg}`);

    return { error: errMsg };
  }
};

type CreatePasswordResetLinkResult = {
  is_success: boolean;
  link: string | null;
  fail_reason: string | null;
};

export const createPasswordResetLink = async (email: string): Promise<CreatePasswordResetLinkResult> => {
  try {
    const apiUrl = getApiURL("CREATE_PASSWORD_RESET_LINK");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email }),
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: CreatePasswordResetLinkResult = await response.json();
    return data;
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`createPasswordResetLink failed: ${errMsg}`);
    return { is_success: false, link: null, fail_reason: errMsg };
  }
};

type ManuallyVerifyEmailResult = {
  is_success: boolean;
  fail_reason: string | null;
};

export const manuallyVerifyEmail = async (email: string): Promise<ManuallyVerifyEmailResult> => {
  try {
    const apiUrl = getApiURL("MANUALLY_VERIFY_EMAIL");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ email }),
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: ManuallyVerifyEmailResult = await response.json();
    return data;
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`manuallyVerifyEmail failed: ${errMsg}`);
    return { is_success: false, fail_reason: errMsg };
  }
};

type PurchaseByCodeResult = {
  fail_reason: string | null;
};

/**
 * purchase by code to current user
 * - You need session context to call this.
 */
export const purchaseByCode = async (inviteCode: string): Promise<PurchaseByCodeResult> => {
  try {
    const apiUrl = getApiURL("PURCHASE_BY_CODE");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ prepaid_code: inviteCode }),
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, status=${response.status}`);
    }
    const data: PurchaseByCodeResult = await response.json();
    return data;
  } catch (error) {
    const errMsg = `Unexpected error: ${error}`;
    console.log(`bindPrepaidCode failed: ${errMsg}`);
    return { fail_reason: errMsg };
  }
};

/** PayLog unit from backend */
export interface PayLogUnit {
  method: string | null;
  log: string;
  is_success: boolean;
  date: string;
}

/** PayLog from backend */
export interface PayLog {
  logs: PayLogUnit[];
}

/** User info from database */
export interface UserDbInfo {
  id: string;
  email: string;
  created_at: string;
  tier: string;
  tier_lifetime: string;
  pay_log: PayLog;
}

/**
 * Get current user's database info
 * - You need session context to call this.
 */
export const fetchUserDbInfo = async (): Promise<UserDbInfo | null> => {
  try {
    const apiUrl = getApiURL("USER_DB_INFO");
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, status=${response.status}`);
    }
    const data: UserDbInfo = await response.json();
    return data;
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`fetchUserDbInfo failed: ${errMsg}`);
    return null;
  }
};


type PaywallAfterPayResult = {
  fail_reason: string | null;
};

/**
 * Call Paywall After-Pay process.
 * No exception will be throw. error will be recorded to fail_reason
 */
export const paywallAfterPayProcess = async (email: string): Promise<PaywallAfterPayResult> => {
  try {
    const apiUrl = getApiURL("STRIPE_AFTER_PAY");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ target_email: email }),
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, status=${response.status}`);
    }
    const data: PaywallAfterPayResult = await response.json();
    return data;
  } catch (error) {
    const errMsg = `Unexpected error: ${error}`;
    console.log(`bindPrepaidCode failed: ${errMsg}`);
    return { fail_reason: errMsg };
  }
};