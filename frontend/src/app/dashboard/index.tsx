import { useEffect, useState } from "react";
import ContentPageLayout from "../../component/ContentPageLayout";
import { fetchUserDbInfo, type UserDbInfo } from "../../utils/api";


export default function Dashboard() {
  const [userData, setUserData] = useState<UserDbInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadUserData = async () => {
      try {
        const data = await fetchUserDbInfo();
        if (data) {
          setUserData(data);
        } else {
          setError("获取用户信息失败");
        }
      } catch (err) {
        setError(`加载用户数据时出错: ${err}`);
      }
    };

    loadUserData();
  }, []);

  const transformDateStr = (dateStr: undefined | string): string => {
    if (!dateStr) return "-";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString();
    } catch {
      return "-";
    }
  };

  if (error) {
    return (
      <ContentPageLayout>
        <div className="p-6 w-full bg-base-100 rounded-xl shadow-md space-y-6">
          <h2 className="text-2xl font-bold text-center">个人信息</h2>
          <div className="alert alert-error">
            <span>{error || "未知错误"}</span>
          </div>
        </div>
      </ContentPageLayout>
    );
  }

  return (
    <ContentPageLayout>
      <div className="p-6 w-full max-w-4xl mx-auto bg-base-100 sm:rounded-2xl shadow-lg space-y-8">
        {/* 头部 */}
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold">个人信息</h2>
          <p className="text-sm text-base-content/60">账户详情与订阅状态</p>
        </div>

        {/* 信息卡片网格 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* 邮箱 */}
          <div className="bg-base-200/50 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            </div>
            <div className="min-w-0">
              <div className="text-xs font-medium text-base-content/60 uppercase tracking-wider">邮箱</div>
              <div className="text-sm font-semibold truncate">{userData?.email ?? "-"}</div>
            </div>
          </div>

          {/* 注册时间 */}
          <div className="bg-base-200/50 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <div className="text-xs font-medium text-base-content/60 uppercase tracking-wider">注册时间</div>
              <div className="text-sm font-semibold">{transformDateStr(userData?.created_at)}</div>
            </div>
          </div>

          {/* 用户类别 */}
          <div className="bg-base-200/50 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-info/10 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-info" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-xs font-medium text-base-content/60 uppercase tracking-wider">用户类别</div>
              <div className="flex items-center gap-2">
                <span className="badge badge-info badge-sm">{userData?.tier ?? "-"}</span>
              </div>
            </div>
          </div>

          {/* 到期时间 */}
          <div className="bg-base-200/50 rounded-xl p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-warning/10 flex items-center justify-center shrink-0">
              <svg className="w-5 h-5 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <div className="text-xs font-medium text-base-content/60 uppercase tracking-wider">到期时间</div>
              <div className="text-sm font-semibold">{userData?.tier_lifetime ?? "-"}</div>
            </div>
          </div>
        </div>

        {/* 付费记录 */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-base-content/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <h3 className="text-lg font-bold">付费记录</h3>
          </div>

          {!userData?.pay_log || userData.pay_log.logs.length === 0 ? (
            <div className="bg-base-200/30 rounded-xl p-8 text-center">
              <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-base-300 flex items-center justify-center">
                <svg className="w-8 h-8 text-base-content/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-base-content/60 font-medium">暂无付费记录</p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-xl border border-base-300">
              <table className="table w-full">
                <thead className="bg-base-200">
                  <tr>
                    <th className="text-xs font-bold uppercase tracking-wider">日期</th>
                    <th className="text-xs font-bold uppercase tracking-wider">支付方式</th>
                    <th className="text-xs font-bold uppercase tracking-wider text-center">状态</th>
                    <th className="text-xs font-bold uppercase tracking-wider">详情</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-base-300">
                  {[...userData.pay_log.logs].reverse().map((record, index) => (
                    <tr key={index} className="hover:bg-base-200/50 transition-colors">
                      <td className="text-sm">{transformDateStr(record.date)}</td>
                      <td className="text-sm">
                        {record.method && <span className="badge badge-ghost badge-sm">{record.method}</span>}
                      </td>
                      <td className="text-center min-w-20">
                        <span className={`badge badge-sm ${record.is_success ? "badge-success" : "badge-error"}`}>
                          {record.is_success ? "成功" : "失败"}
                        </span>
                      </td>
                      <td className="text-sm text-base-content/80 max-w-xs truncate" title={record.log}>
                        {record.log}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </ContentPageLayout>
  );
}
