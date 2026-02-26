import { useState } from "react";
import { Link, NavLink, useNavigate, type NavigateFunction } from "react-router-dom";
import { redirectToAuth } from "supertokens-auth-react";
import { signOut } from "supertokens-auth-react/recipe/session";
import { JumpOutSPARouteLogic, ROUTES } from "../../routes";
import { useIsAdmin, useEmail } from "../../utils/frontendHooks";
import { SiteConfig } from "../../config";


export default function TopNavbar() {
  return (
    <header className="sticky top-0 z-[100] h-[70px] bg-[var(--c-bg-nav)] backdrop-blur-[10px] border-b border-[var(--border-color)] flex items-center shadow-none">

      <nav className="w-full max-w-[var(--container-width)] mx-auto px-4 flex justify-between items-center">

        <div className="flex items-center">
          <Link
            to='/'
            className='text-[1.25rem] font-extrabold text-[var(--c-brand)] hover:opacity-80 transition-opacity flex gap-2 items-center'
          >
            {SiteConfig.appLocaleName}
          </Link>
        </div>

        <div className="flex items-center gap-0">

          <div className="hidden sm:flex">
            <ul className="menu menu-horizontal p-0 gap-0 text-[var(--c-text-muted)] font-medium">
              <UserAuthComponent />
            </ul>
          </div>

          <div className="dropdown dropdown-end sm:hidden">
            <div tabIndex={0} role="button" className="btn btn-ghost btn-sm px-1 text-[var(--c-text-muted)] hover:bg-transparent">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h8m-8 6h16" />
              </svg>
            </div>

            <ul
              tabIndex={-1}
              className="menu menu-md dropdown-content z-[1001] mt-3 w-32 p-2 shadow-[var(--shadow-sm)] rounded-lg bg-[var(--c-bg-nav)] backdrop-blur-[10px] border border-[var(--border-color)]"
            >
              <UserAuthComponent />
            </ul>
          </div>

        </div>
      </nav>
    </header>
  );
}

const SignInUpComponent = () => (
  <>
    <a onClick={() => redirectToAuth({ show: "signin" })} className='font-medium text-[var(--c-text-muted)] hover:text-[var(--c-brand)] hover:bg-transparent active:!bg-transparent focus:!bg-transparent transition-colors cursor-pointer'>
      登录
    </a>
    <a onClick={() => redirectToAuth({ show: "signup" })} className='font-medium text-[var(--c-text-muted)] hover:text-[var(--c-brand)] hover:bg-transparent active:!bg-transparent focus:!bg-transparent transition-colors cursor-pointer'>
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

const HelloSignOutComponent = ({ userDisplayName, onSignOut, isAdmin, isSigningOut, navigate }: HelloSignOutProps) => {
  const navItemBaseClass = "font-medium hover:bg-transparent active:!bg-transparent focus:!bg-transparent transition-colors cursor-pointer block";
  return (<>
    <li className="hidden sm:flex">
      <span
        className="select-text cursor-default text-[var(--c-text-muted)] hover:bg-transparent active:!bg-transparent focus:!bg-transparent">
        Hi, {userDisplayName}
      </span>
    </li>

    <div className="hidden sm:block w-[1px] h-[1.6rem] bg-[#e5e7eb] self-center mx-2"></div>

    <li className="tracking-widest">
      <NavLink
        to={ROUTES.DASHBOARD}
        className={({ isActive }) =>
          `${navItemBaseClass} ${isActive
            ? "text-[var(--c-brand)]" // 对齐 &.active { color: var(--c-brand); }
            : "text-[var(--c-text-muted)] hover:text-[var(--c-brand)]"
          }`
        }
      >
        个人页
      </NavLink>
    </li>

    <li className="tracking-widest">
      <button
        onClick={() => { navigate(JumpOutSPARouteLogic.genRedirect2DocRoot()); }}
        className={`${navItemBaseClass} text-[var(--c-text-muted)] hover:text-[var(--c-brand)] text-left`}
      >
        文档页
      </button>
    </li>

    {isAdmin === true && (
      <li className="tracking-widest">
        <NavLink
          to={ROUTES.MANAGE}
          className={({ isActive }) =>
            `${navItemBaseClass} ${isActive
              ? "text-[var(--c-brand)]"
              : "text-[var(--c-text-muted)] hover:text-[var(--c-brand)]"
            }`
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
        className={`${navItemBaseClass} text-[var(--c-text-muted)] hover:text-[var(--c-brand)] text-left`}
      >
        {isSigningOut ? <span className="loading loading-dots"></span> : "退出登录"}
      </button>
    </li>
  </>);
};



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
