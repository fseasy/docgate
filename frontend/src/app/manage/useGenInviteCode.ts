import { useState } from "react";
import { genInviteCode } from "../../utils/api";

type GenInviteCodeResponse =
  | { status: "idle"; }
  | { status: "loading"; }
  | { status: "success"; code: string; lifetime: string; }
  | {
    status: "error";
    error: string;
  };

export const useGenInviteCode = () => {
  const [result, setResult] = useState<GenInviteCodeResponse>({ status: "idle" });

  const generate = async () => {
    setResult({ status: "loading" });
    const apiResult = await genInviteCode();
    if (apiResult.error === null) {
      setResult({
        status: "success",
        code: apiResult.code,
        lifetime: apiResult.lifetime,
      });
    } else {
      setResult({
        status: "error",
        error: apiResult.error,
      });
    }
  };

  return { result, generate };
};
