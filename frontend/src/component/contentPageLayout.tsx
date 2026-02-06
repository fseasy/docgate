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
      <div className='max-w-3xl mx-auto p-6'>
        {children}

      </div>
    </div>
  );
};
