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
      <div className="p-6 w-full bg-base-100 rounded-xl shadow-md space-y-6">
        <h2 className="text-2xl font-bold text-center">个人信息</h2>

        <div className="grid grid-cols-2 gap-4">
          {/* 邮箱 */}
          <div className="flex justify-between">
            <span className="text-lg font-medium">邮箱:</span>
            <span>{userData?.email ?? "-"}</span>
          </div>

          {/* 注册时间 */}
          <div className="flex justify-between">
            <span className="text-lg font-medium">注册时间:</span>
            <span>{userData?.created_at ?? "-"}</span>
          </div>

          {/* 用户类别 */}
          <div className="flex justify-between">
            <span className="text-lg font-medium">用户类别:</span>
            <span className="text-info">
              {userData?.tier ?? "-"}
            </span>
          </div>

          {/* 套餐到期时间 */}
          <div className="flex justify-between">
            <span className="text-lg font-medium">到期时间:</span>
            <span>{userData?.tier_lifetime ?? "-"}</span>
          </div>
        </div>

        {/* 付费记录 */}
        <div>
          <h3 className="text-xl font-medium mb-3">付费记录</h3>
          {!userData?.pay_log || userData.pay_log.logs.length === 0 ? (
            <div className="text-center py-4 text-base-content/70">暂无付费记录</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="table w-full">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>支付方式</th>
                    <th>状态</th>
                    <th>日志</th>
                  </tr>
                </thead>
                <tbody>
                  {userData.pay_log.logs.map((record, index) => (
                    <tr key={index}>
                      <td>{record.date}</td>
                      <td>{record.method}</td>
                      <td>
                        <span
                          className={`badge ${record.is_success ? "badge-success" : "badge-error"}`}
                        >
                          {record.is_success ? "成功" : "失败"}
                        </span>
                      </td>
                      <td>{record.log}</td>
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
