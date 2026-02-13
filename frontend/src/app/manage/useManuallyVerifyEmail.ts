import { useState } from "react";
import { manuallyVerifyEmail } from "../../utils/api";

type ManuallyVerifyEmailResponse =
  | { status: "idle"; }
  | { status: "loading"; }
  | { status: "success"; }
  | {
    status: "error";
    error: string;
  };

export const useManuallyVerifyEmail = () => {
  const [result, setResult] = useState<ManuallyVerifyEmailResponse>({ status: "idle" });

  const verifyEmail = async (email: string) => {
    setResult({ status: "loading" });
    const apiResult = await manuallyVerifyEmail(email);
    if (apiResult.is_success) {
      setResult({ status: "success" });
    } else {
      setResult({
        status: "error",
        error: apiResult.fail_reason || "Unknown error",
      });
    }
  };

  return { result, verifyEmail };
};
