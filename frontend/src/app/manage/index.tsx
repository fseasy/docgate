import { SiteConfig } from "../../config";
import { useEffect, useState } from "react";
import { useGenInviteCode } from "./useGenInviteCode";
import TopNavbar from "../../component/nav/TopNav";
import { useClipboard } from "../../utils/frontendHooks";

export default function ManageDashboard() {
  const { result: genCodeResult, generate: genCode } = useGenInviteCode();

  const [inviteCodeLink, setInviteCodeLink] = useState<string>("");
  const [inviteCodeStr, setInviteCodeStr] = useState<string>("");
  const [inviteCodeResponse, setInviteCodeResponse] = useState<string>("");
  const { copied, copyToClipboard } = useClipboard();

  const makeInviteLink = (code: string) => `${SiteConfig.websiteDomain}/auth?show=signup&ic=${code}`;

  useEffect(() => {
    if (genCodeResult.status === "idle" || genCodeResult.status === "loading") {
      setInviteCodeStr("");
      setInviteCodeLink("");
      setInviteCodeResponse("");
      return;
    }
    setInviteCodeResponse(JSON.stringify(genCodeResult, null, 2));
    if (genCodeResult.status === "error") {
      setInviteCodeStr("");
      setInviteCodeLink("");
      return;
    }
    const code = genCodeResult.code!;
    setInviteCodeStr(code);
    setInviteCodeLink(makeInviteLink(code));
  }, [genCodeResult.status]);

  return (
    <>
      <div className='min-h-screen bg-base-200'>
        {/* 顶部导航 */}
        <TopNavbar />

        {/* 主内容区 */}
        <div className='max-w-3xl mx-auto p-6'>
          <div className='card bg-base-100 shadow-xl'>
            <div className='card-body space-y-4'>
              {/* 标题 */}
              <h2 className='card-title text-xl'>生成邀请链接（预付款注册链接）</h2>

              {/* 操作按钮 */}
              <div className='flex gap-5'>
                <button
                  className='btn btn-primary w-fit'
                  onClick={genCode}
                  disabled={genCodeResult.status === "loading"}
                >
                  {genCodeResult.status === "loading" ? "生成中…" : "生成新的邀请链接"}
                </button>
                <button
                  className='btn btn-secondary w-fit'
                  disabled={genCodeResult.status != "success"}
                  onClick={() => copyToClipboard(inviteCodeLink)}
                >
                  {copied ? "已复制 ✓" : "复制链接"}
                </button>
              </div>

              <div className='divider' />

              {/* 结果区 */}
              <div className='space-y-3'>
                <div>
                  <div className='text-sm text-gray-500'>邀请链接</div>
                  <div className='font-mono break-all'>{inviteCodeLink || "—"}</div>
                </div>

                <div>
                  <div className='text-sm text-gray-500'>邀请码</div>
                  <div className='font-mono'>{inviteCodeStr || "—"}</div>
                </div>

                <div>
                  <div className='text-sm text-gray-500'>请求 API 结果（debug）</div>
                  <pre className='bg-base-200 rounded p-2 text-sm overflow-x-auto'>{inviteCodeResponse || "—"}</pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
