import { useState, useEffect } from "react";
import Session, { useSessionContext } from "supertokens-auth-react/recipe/session";
import { UserRoleClaim } from "supertokens-auth-react/recipe/userroles";
import { useNavigate, } from "react-router-dom";
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
  const session = useSessionContext();
  const payloadEmail = session.loading ? undefined : session.accessTokenPayload.email;
  const [apiFetching, setApiFetching] = useState<boolean>(false);
  const [apiEmail, setApiEmail] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (session.loading || payloadEmail || apiFetching || apiEmail != undefined) return;

    // Fetching
    let isMount = true;

    const fetchEmail = async () => {
      setApiFetching(true);
      try {
        const userData = await fetchSessionSupertokensUserById();
        if (isMount) setApiEmail(userData?.emails[0]);
      } catch (err) {
        console.error("Fetch user data failed", { err });
        if (isMount) setApiEmail(undefined);
      } finally {
        if (isMount) setApiFetching(false);
      }
    };
    fetchEmail();

    return () => { isMount = false; };

  }, [session.loading, payloadEmail, apiFetching, apiEmail]);

  if (session.loading) return { loading: true };
  if (payloadEmail) return { loading: false, email: payloadEmail };
  if (apiFetching) return { loading: true };
  return { loading: false, email: apiEmail };
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
export const useConsoleNavigate = () => {
  const navigate = useNavigate();
  useEffect(() => {
    if (typeof window !== "undefined") {
      window.navigate = navigate;
    }
  }, [navigate]);
};
