import { SiteConfig } from "../config";

interface StUser {
  id: string;
  isPrimaryUser: boolean;
  emails: string[];
  loginMethods: Record<string, unknown>[];
  timeJoined: number;
}

interface GetUserSuccess {
  error: null;
  user: StUser;
}

interface GetUserError {
  error: string;
  user: null;
}

type GetUserResponse = GetUserSuccess | GetUserError;

// You need session context to call this.
const fetchSessionSupertokensUserById = async () => {
  try {
    const apiUrl = SiteConfig.apiDomain + "/get_current_supertokens_user";
    const response = await fetch(apiUrl, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });
    if (!response.ok) {
      throw new Error(`Failed on api call, err=${response}`);
    }
    const data: GetUserResponse = await response.json();
    if (data.error) {
      throw new Error(`Failed on server side, err=${data.error}`);
    }
    return data.user;
  } catch (error) {
    const errMsg =
      error instanceof Error ? error.message : typeof error === "string" ? error : "Unknow error in Frontend";
    console.log(`fetchSupertokensUserById failed: ${errMsg}`);
    return null;
  }
};

export type { StUser, GetUserResponse };
export { fetchSessionSupertokensUserById };
