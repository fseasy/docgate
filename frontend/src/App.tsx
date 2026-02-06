import { lazy, Suspense } from "react";
import * as reactRouterDom from "react-router-dom";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { SuperTokensWrapper } from "supertokens-auth-react";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import { SessionAuth } from "supertokens-auth-react/recipe/session";
import { getSuperTokensRoutesForReactRouterDom } from "supertokens-auth-react/ui";
import { EmailVerificationPreBuiltUI } from "supertokens-auth-react/recipe/emailverification/prebuiltui";


import { ROUTES } from "./routes";
import AdminRouteAuth from "./supertokens/RouteAuth";

import "./App.css";

const ManageDashboard = lazy(() => import("./app/manage"));
const Dashboard = lazy(() => import("./app/dashboard"));
const Purchase = lazy(() => import("./app/purchase"));
const GoDocs = lazy(() => import("./app/jump-out-spa"));
const NotFoundPage = lazy(() => import("./app/not-found-page"));

function App() {
  return (
    <SuperTokensWrapper>
      <BrowserRouter>
        <Suspense fallback={null}>
          <Routes>
            {/* This shows the login UI on "websiteBasePath" route */}
            {getSuperTokensRoutesForReactRouterDom(
              reactRouterDom,
              [EmailPasswordPreBuiltUI, EmailVerificationPreBuiltUI]
            )}

            {/* This protects the "/dashboard" route so that it shows
                <Dashboard /> only if the user is logged in.
                Else it redirects the user to "/auth" 
            */}
            <Route
              path={ROUTES.DASHBOARD}
              element={
                <SessionAuth>
                  <Dashboard />
                </SessionAuth>
              }
            />
            <Route
              path={ROUTES.MANAGE}
              element={
                <AdminRouteAuth>
                  <ManageDashboard />
                </AdminRouteAuth>
              }
            />
            <Route
              path={ROUTES.PURCHASE}
              element={
                <SessionAuth>
                  <Purchase />
                </SessionAuth>
              }
            />
            <Route
              path={ROUTES.JUMP_OUT_REDIRECT}
              element={
                <GoDocs />
              }
            />
            {/* catch all the others unknown path */}
            <Route
              path="*"
              element={
                <NotFoundPage />
              }
            />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </SuperTokensWrapper>
  );
}

export default App;
