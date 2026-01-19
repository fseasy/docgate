import { useState } from "react";
import { SiteConfig } from "../../config";

type GenInviteCodeResponse =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; code: string; lifetime: string }
  | {
      status: "error";
      error: string;
    };

export const useGenInviteCode = () => {
  const [result, setResult] = useState<GenInviteCodeResponse>({ status: "idle" });

  const generate = async () => {
    setResult({ status: "loading" });
    try {
      const apiUrl = SiteConfig.apiDomain + "/gen_invite_code";
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        throw new Error(`Failed on api call, err=${response}`);
      }
      const data = await response.json();
      if (data.error) {
        throw new Error(`Failed on server side, err=${data.error}`);
      }
      setResult({
        status: "success",
        code: data.code,
        lifetime: data.lifetime,
      });
    } catch (error) {
      const errMsg =
        error instanceof Error ? error.message : typeof error === "string" ? error : "Unknow error in Frontend";
      setResult({
        status: "error",
        error: errMsg,
      });
    }
  };

  return { result, generate };
};
