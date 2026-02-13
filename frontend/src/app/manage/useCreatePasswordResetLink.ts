import { useState } from "react";
import { createPasswordResetLink } from "../../utils/api";

type CreatePasswordResetLinkResponse =
  | { status: "idle"; }
  | { status: "loading"; }
  | { status: "success"; link: string; }
  | {
    status: "error";
    error: string;
  };

export const useCreatePasswordResetLink = () => {
  const [result, setResult] = useState<CreatePasswordResetLinkResponse>({ status: "idle" });

  const createLink = async (email: string) => {
    setResult({ status: "loading" });
    const apiResult = await createPasswordResetLink(email);
    if (apiResult.is_success && apiResult.link) {
      setResult({
        status: "success",
        link: apiResult.link,
      });
    } else {
      setResult({
        status: "error",
        error: apiResult.fail_reason || "Unknown error",
      });
    }
  };

  return { result, createLink };
};
