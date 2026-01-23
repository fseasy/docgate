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
type InviteCodeResult =
  | {
    error: string;
  }
  | {
    error: null,
    code: string,
    lifetime: string;
  };

export const genInviteCode = async (): Promise<InviteCodeResult> => {
  try {
    const apiUrl = getApiURL("GEN_INVITE_CODE");
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: InviteCodeResult = await response.json();
    if (data.error !== null) {
      throw new Error(`Failed on server side, err=${data.error}`);
    }
    return { error: null, code: data.code, lifetime: data.lifetime };
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknown error in Frontend";
    console.log(`genInviteCode failed: ${errMsg}`);

    return { error: errMsg };
  }
};


