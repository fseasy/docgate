import { useState } from "react";
import { Link, NavLink, useNavigate, type NavigateFunction } from "react-router-dom";
import { redirectToAuth } from "supertokens-auth-react";
import { signOut } from "supertokens-auth-react/recipe/session";
import { JumpOutSPARouteLogic, ROUTES } from "../../routes";
import { useIsAdmin, useEmail } from "../../utils/frontendHooks";
import { SiteConfig } from "../../config";


export default function TopNavbar() {
  return (
    <nav className='navbar bg-base-100 shadow-sm'>
      <div className="navbar-start">
        <Link to='/' className='btn btn-ghost text-xl'>
          {SiteConfig.appLocaleName}
        </Link>
      </div>

      <div className="navbar-end ">
        <div className="hidden sm:flex">
          <ul className="menu menu-horizontal px-1">
            <UserAuthComponent />
          </ul>
        </div>
        <div className="dropdown dropdown-end">
          <div tabIndex={0} role="button" className="btn btn-ghost sm:hidden">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"> <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" /> </svg>
          </div>
          <ul tabIndex={-1} className="menu menu-md dropdown-content bg-base-100 z-99 mt-3 w-32 items-end-safe p-2 shadow">
            <UserAuthComponent />
          </ul>
        </div>
      </div>
    </nav>
  );
}

const SignInUpComponent = () => (
  <>
    <a onClick={() => redirectToAuth({ show: "signin" })} className='btn btn-ghost text-info'>
      登录
    </a>
    <a onClick={() => redirectToAuth({ show: "signup" })} className='btn btn-ghost'>
      注册
    </a>
  </>
);

interface HelloSignOutProps {
  userDisplayName: string;
  onSignOut: () => void;
  isAdmin: boolean;
  isSigningOut: boolean;
  navigate: NavigateFunction;
}

const HelloSignOutComponent = ({ userDisplayName, onSignOut, isAdmin, isSigningOut, navigate }: HelloSignOutProps) => (
  <>
    <li className="hidden sm:flex">
      <span
        className="select-text cursor-default text-base-content active:bg-transparent focus:bg-transparent hover:bg-transparent">
        Hi, {userDisplayName}
      </span>
    </li>

    <div className="divider divider-horizontal"></div>

    <li className="tracking-widest">
      <NavLink
        to={ROUTES.DASHBOARD}
        className={({ isActive }) =>
          isActive
            ? "font-semibold text-base-content/70"
            : ""
        }
      >
        个人页
      </NavLink>
    </li>

    <li className="tracking-widest">
      <button
        onClick={() => { navigate(JumpOutSPARouteLogic.genRedirect2DocRoot()); }}
      >
        文档页
      </button>
    </li>

    {isAdmin === true && (
      <li className="tracking-widest">
        <NavLink
          to={ROUTES.MANAGE}
          className={({ isActive }) =>
            isActive
              ? "font-semibold text-base-content/70"
              : ""
          }
        >
          管理
        </NavLink>
      </li>
    )
    }

    <li className="tracking-widest">
      <button
        onClick={onSignOut}
        disabled={isSigningOut}
      >
        {isSigningOut ? <span className="loading loading-dots"></span> : "退出登录"}
      </button>
    </li>
  </>
);



const UserAuthComponent = () => {
  const emailStatus = useEmail();
  const navigate = useNavigate();

  const adminStatus = useIsAdmin();
  const isAdmin = !adminStatus.loading && adminStatus.isAdmin;
  const [isSigningOut, setIsSigninOut] = useState<boolean>(false);

  async function logoutClicked() {
    setIsSigninOut(true);
    await signOut();
    navigate(JumpOutSPARouteLogic.genRedirectRelativeURL("/")); // Jump Out SPA for root!
  }

  if (emailStatus.loading || !emailStatus.email) {
    return <SignInUpComponent />;
  }

  return <HelloSignOutComponent
    userDisplayName={emailStatus.email}
    onSignOut={logoutClicked}
    isAdmin={isAdmin}
    isSigningOut={isSigningOut}
    navigate={navigate}
  />;
};
