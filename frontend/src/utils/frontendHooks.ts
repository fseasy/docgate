import { useState, useEffect } from "react";
import Session, { useSessionContext } from "supertokens-auth-react/recipe/session";
import { UserRoleClaim } from "supertokens-auth-react/recipe/userroles";
import { useNavigate } from "react-router-dom";
import { fetchSessionSupertokensUserById } from "./api";

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

type EmailStatus = { loading: true; } | { loading: false; email: string; } | { loading: false, email: undefined; };

export const useEmail = (): EmailStatus => {
  const [emailStatus, setEmailStatus] = useState<EmailStatus>({ loading: true });
  const session = useSessionContext();

  useEffect(() => {
    let isMount = true;

    const loadEmail = async () => {
      if (session.loading) {
        return;
      }
      const sessionEmail = session.accessTokenPayload.email;
      if (sessionEmail) {
        if (isMount) setEmailStatus({ loading: false, email: sessionEmail });
        return;
      }
      try {
        if (isMount) {
          const userData = await fetchSessionSupertokensUserById();
          if (isMount) setEmailStatus({ loading: false, email: userData?.emails[0] });
        }
      } catch (err) {
        console.error("Fetch user data failed", { err });
        if (isMount) setEmailStatus({ loading: false, email: undefined });
      }
    };
    loadEmail();

    return () => { isMount = false; };

  }, [session.loading]);

  return emailStatus;
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

/*****
 * Used for dev, export the navigator to console.
 */
export const devUseConsoleNavigate = () => {
  const navigate = useNavigate();
  useEffect(() => {
    (window as any).navigate = navigate;
  }, [navigate]);
};
