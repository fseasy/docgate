import TopNavbar  from "../../component/nav/TopNav";

export default function Home() {
  return (
    <>
      <TopNavbar />

      <div
        className='relative w-full aspect-1920/600 overflow-hidden' // 1. 替换为图片实际的宽高比
        style={{
          backgroundImage: "url('/site-banner.png')",
          backgroundSize: "cover", // 使用 cover 确保铺满
          backgroundPosition: "center",
        }}
      >
        {/* 背景遮罩 */}
        <div className='absolute inset-0 bg-black/5' />

        {/* 3. 使用百分比定位文字，确保位置固定 */}
        <div className='absolute top-[30%] right-[25%] z-10 text-center text-white'>
          {/* 4. 使用 vw 或 clamp 让文字大小也随屏幕缩放 */}
          <p className='text-[1.2vw] tracking-widest mb-[1vw]'>Learn it. Say it.</p>

          <h1 className='text-[4vw] font-bold tracking-tight leading-tight mb-[1.5vw]'>大娟的亲子英语</h1>

          <p className='text-[1.6vw] leading-relaxed text-gray-600 opacity-90 bg-orange-100 rounded-[1.6vw] px-6 py-2 inline-block'>
            让父母开口说，让孩子自然习得
          </p>
        </div>
      </div>
    </>
  );
}
