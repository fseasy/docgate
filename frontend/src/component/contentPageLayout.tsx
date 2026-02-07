import React from 'react';

import TopNavbar from './nav/TopNav';

interface LayoutProps {
  children: React.ReactNode;
}

export default function ContentPageLayout({ children }: LayoutProps) {
  return (
    <div className='min-h-screen bg-base-300'>
      {/* 顶部导航 */}
      <TopNavbar />

      {/* 主内容区 */}
      <div className='container sm:p-6 sm:w-3xl sm:mx-auto'>
        {children}
      </div>
    </div>
  );
};
