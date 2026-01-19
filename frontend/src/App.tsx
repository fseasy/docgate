import { SuperTokensWrapper } from "supertokens-auth-react";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import * as reactRouterDom from "react-router-dom";
import { getSuperTokensRoutesForReactRouterDom } from "supertokens-auth-react/ui";
import { SessionAuth } from "supertokens-auth-react/recipe/session";
import { EmailPasswordPreBuiltUI } from "supertokens-auth-react/recipe/emailpassword/prebuiltui";
import Dashboard from "./app/dashboard";
import Home from "./app/home";
import ManageDashboard from "./app/manage";
import AdminRouteAuth from "./supertokens/RouteAuth";

import "./App.css";

function App() {
  return (
    <SuperTokensWrapper>
      <BrowserRouter>
        <Routes>
          <Route path='/' element={<Home />} />
          {/* This shows the login UI on "/auth" route */}
          {getSuperTokensRoutesForReactRouterDom(reactRouterDom, [EmailPasswordPreBuiltUI])}

          {/* This protects the "/dashboard" route so that it shows
                            <Dashboard /> only if the user is logged in.
                            Else it redirects the user to "/auth" */}
          <Route
            path='/dashboard'
            element={
              <SessionAuth>
                <Dashboard />
              </SessionAuth>
            }
          />
          <Route
            path='/manage'
            element={
              <AdminRouteAuth>
                <ManageDashboard />
              </AdminRouteAuth>
            }
          />
        </Routes>
      </BrowserRouter>
    </SuperTokensWrapper>
  );
}

export default App;
