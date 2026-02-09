import { useState } from "react";
import { genPrepaidCode } from "../../utils/api";

type GenPrepaidCodeResponse =
  | { status: "idle"; }
  | { status: "loading"; }
  | { status: "success"; code: string; lifetime: string; }
  | {
    status: "error";
    error: string;
  };

export const useGenPrepaidCode = () => {
  const [result, setResult] = useState<GenPrepaidCodeResponse>({ status: "idle" });

  const generate = async () => {
    setResult({ status: "loading" });
    const apiResult = await genPrepaidCode();
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
