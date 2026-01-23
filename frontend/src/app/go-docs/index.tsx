import { useEffect } from "react";
import { genWebsiteFullURL } from "../../routes";

export default function GoDocs() {
  const from = window.location.pathname;
  const rootURL = genWebsiteFullURL({ basePath: "/", queryParams: { from: from } });
  useEffect(() => {
    window.location.replace(rootURL);
  }, []);

  return (<>
    <div className="min-h-screen bg-base-200 max-w-3xl mx-auto p-6">
      <div>登录成功，正在跳转...</div>
      <div><a href={rootURL}>点击手动跳转</a></div >
    </div>
  </>);
}