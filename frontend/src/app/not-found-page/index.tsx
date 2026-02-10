import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import ContentPageLayout from "../../component/ContentPageLayout";
import { isPathPrefixBelongsToSPA, JumpOutSPARouteLogic, ROUTES } from "../../routes";

export default function NotFoundPage() {
  const pathname = window.location.pathname;

  const navigate = useNavigate();
  const isInSPA = isPathPrefixBelongsToSPA(pathname);
  const fullUrl = window.location.href;

  useEffect(() => {
    let tgtUrl = "";
    if (isInSPA) {
      tgtUrl = ROUTES.DASHBOARD;
    } else {
      tgtUrl = JumpOutSPARouteLogic.genRedirectRelativeURL(fullUrl);
    }
    const timer = setTimeout(() => navigate(tgtUrl), 1000);
    return () => clearTimeout(timer);
  }, [isInSPA, fullUrl, navigate]);

  return (
    <ContentPageLayout>
      <div className="flex items-center justify-center h-[70vh]">
        <div className="card bg-base-100 h-[50vh] items-center justify-center w-full">
          <h2 className="text-5xl m-9">
            404 Page Not Found
          </h2>
          <div>
            <p><code>{pathname}</code> isn't a known url.</p>
            {isInSPA
              ? <p>Redirecting to <code>dashboard</code></p>
              : <p>Redirecting to <code>{fullUrl}</code></p>
            }
          </div>
        </div>
      </div>
    </ContentPageLayout>
  );
}