import { useState } from "react";
import Session from "supertokens-auth-react/recipe/session";
import { UserRoleClaim } from "supertokens-auth-react/recipe/userroles";

type AdminStatus = { loading: true; } | { loading: false; isAdmin: boolean; };

export const useIsAdmin = (): AdminStatus => {
  const claimValue = Session.useClaimValue(UserRoleClaim);
  if (claimValue.loading || !claimValue.doesSessionExist) {
    return { loading: true };
  }
  const roles = claimValue.value;
  const isAdmin = Array.isArray(roles) && roles.includes("admin");
  return { loading: false, isAdmin: isAdmin };
};

interface UseClipboardOptions {
  timeout?: number;
}

export type CopyStatus = "idle" | "success" | "fail";

export const useClipboard = (options: UseClipboardOptions = {}) => {
  const { timeout = 2000 } = options;
  const [copyStatus, setCopyStatus] = useState<CopyStatus>("idle");

  const copyToClipboard = async (text: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopyStatus("success");
    } catch (err) {
      console.error("复制失败:", err);
      setCopyStatus("fail");
    } finally {
      setTimeout(() => setCopyStatus("idle"), timeout);
    }
  };

  return { copyStatus, copyToClipboard };
};
