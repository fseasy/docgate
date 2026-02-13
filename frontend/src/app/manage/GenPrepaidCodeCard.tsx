import { customizeAuthURL } from "../../supertokens/url";
import { useGenPrepaidCode } from "./useGenPrepaidCode";
import { QUERY_KEYS } from "../../routes";
import { CopyField } from "./CopyField";

export function GenPrepaidCodeCard() {
  const { result: genCodeResult, generate: genCode } = useGenPrepaidCode();

  const makeInviteLink = (code: string) => customizeAuthURL({
    show: "signup", queryParams: { [QUERY_KEYS.PREPAID_CODE]: code }
  });

  const isIdleOrLoading =
    genCodeResult.status === "idle" ||
    genCodeResult.status === "loading";

  const inviteCodeResponse = isIdleOrLoading
    ? ""
    : JSON.stringify(genCodeResult, null, 2);

  const isCodeGenSuccess = genCodeResult.status === "success";
  const inviteCodeStr = isCodeGenSuccess ? genCodeResult.code : "";
  const inviteCodeLink = isCodeGenSuccess ? makeInviteLink(genCodeResult.code) : "";


  return (
    <div className='card bg-base-100 shadow-xl'>
      <div className='card-body space-y-4'>
        <h2 className='card-title text-xl'>生成预付款注册链接</h2>

        <p>用户购买后，生成此链接供用户完成注册并绑定预付费码。</p>

        <div className='flex gap-5'>
          <button
            className='btn btn-primary w-fit'
            onClick={genCode}
            disabled={genCodeResult.status === "loading"}
          >
            {genCodeResult.status === "loading" ? "生成中…" : "生成新的链接"}
          </button>
        </div>

        <div className='divider' />

        <div className='space-y-5'>
          <CopyField
            label="预付款码"
            value={inviteCodeStr}
            disabled={!isCodeGenSuccess}
            size="sm"
          />
          <CopyField
            label="预付款链接"
            value={inviteCodeLink}
            disabled={!isCodeGenSuccess}
            size="sm"
          />
          <div>
            <div className='text-sm text-gray-500'>请求 API 结果（debug）</div>
            <pre className='bg-base-200 rounded p-2 text-sm overflow-x-auto'>{inviteCodeResponse || "—"}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
