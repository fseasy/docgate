import { useEffect, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { redirectToAuth } from "supertokens-auth-react";
import { signOut, useSessionContext } from "supertokens-auth-react/recipe/session";
import { ROUTES } from "../../routes";
import type { StUser } from "../../utils/api";
import { fetchSessionSupertokensUserById } from "../../utils/api";
import { useIsAdmin } from "../../utils/frontendHooks";

const UserAuthComponent = () => {
  const session = useSessionContext();
  const doesSessionExist = !session.loading && session.doesSessionExist;

  const navigate = useNavigate();

  const [user, setUser] = useState<StUser | null>(null);
  const [userLoading, setUserLoading] = useState(true);
  const pageLoading = session.loading || userLoading;

  const adminStatus = useIsAdmin();
  const isAdmin = !adminStatus.loading && adminStatus.isAdmin;

  useEffect(() => {
    if (!doesSessionExist) {
      setUser(null);
      return;
    }
    let cancelled = false;

    setUserLoading(true);
    (async () => {
      try {
        const userData = await fetchSessionSupertokensUserById();
        if (!cancelled) setUser(userData);
      } catch (error) {
        console.error("Failed to fetch user:", error);
      } finally {
        if (cancelled) setUserLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [doesSessionExist]);

  async function logoutClicked() {
    await signOut();
    setUser(null); // ! very important. to sync the nav bar.
    navigate("/");
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
  }

  const HelloSignOutComponent = ({ userDisplayName, onSignOut, isAdmin }: HelloSignOutProps) => (
    <>
      <span className='hidden md:inline text-white'>Hi, {userDisplayName}</span>

      {isAdmin === true && (
        <NavLink
          to={ROUTES.MANAGE}
          className={({ isActive }) =>
            isActive
              ? "text-base-content font-semibold border-b-2 border-primary"
              : "text-base-content/70 hover:text-base-content border-b-2 border-transparent"
          }
        >
          管理
        </NavLink>
      )}

      <button
        onClick={onSignOut}
        className='text-base-content/70 hover:text-base-content border-b-2 border-transparent cursor-pointer'
      >
        退出登录
      </button>
    </>
  );

  if (pageLoading || !user || user.emails.length === 0) {
    return <SignInUpComponent />;
  }

  return <HelloSignOutComponent userDisplayName={user.emails[0]} onSignOut={logoutClicked} isAdmin={isAdmin} />;
};

function TopNavbar() {
  return (
    <nav className='navbar bg-base-100 sticky top-0 z-50 shadow'>
      <div className='navbar-start'>
        <Link to='/' className='text-xl font-bold'>
          {import.meta.env.VITE_HOST_NAME}
        </Link>
      </div>

      <div className='navbar-end'>
        <div className='flex items-center gap-3'>
          <UserAuthComponent />
        </div>
      </div>
    </nav>
  );
}

export default TopNavbar;
