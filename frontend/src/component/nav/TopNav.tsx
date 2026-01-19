import { useEffect, useState } from "react";
import { signOut, useSessionContext } from "supertokens-auth-react/recipe/session";
import { fetchSessionSupertokensUserById } from "../../utils/api";
import { useNavigate, Link, NavLink } from "react-router-dom";
import type { StUser } from "../../utils/api";
import { useIsAdmin } from "../../utils/frontendHooks";

const UserAuthComponent = () => {
  const session = useSessionContext();
  const navigate = useNavigate();
  const [user, setUser] = useState<StUser | null>(null);
  const [loading, setLoading] = useState(true);
  const adminStatus = useIsAdmin();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (session.loading) {
      setLoading(true);
      return;
    }
    if (!session.doesSessionExist) {
      setLoading(false);
      setUser(null);
      return;
    }
    const loadUser = async () => {
      try {
        const userData = await fetchSessionSupertokensUserById();
        setUser(userData);
      } catch (error) {
        setUser(null);
        console.error("Failed to fetch user:", error);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, [session.loading]);

  useEffect(() => {
    if (adminStatus.loading) {
      return;
    }
    setIsAdmin(adminStatus.isAdmin);
  }, [adminStatus.loading]);

  async function logoutClicked() {
    await signOut();
    setUser(null); // ! very important. to sync the nav bar.
    navigate("/");
  }

  const SignInUpComponent = () => (
    <>
      <Link to='/auth?show=signin' className='btn btn-ghost text-info'>
        登录
      </Link>
      <Link to='/auth?show=signup' className='btn btn-ghost'>
        注册
      </Link>
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
          to='/manage'
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

  if (loading || !user || user.emails.length === 0) {
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
