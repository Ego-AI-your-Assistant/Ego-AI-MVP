import navBg from '../../assets/navbar_bg/Analytics/group4.svg'

// export default function Header() {
//   return (
//     <nav className="flex justify-center gap-8 py-6 shadow-sm rounded-b-xl text-sm font-semibold"
//          style={{ backgroundImage: `url(${navBg})` }}>
//       {["Calendar", "Dashboards/Analytics", "Chat with AI", "Recommendations", "Geo-Assistant"].map((item) => (
//         <div key={item} className="px-4 py-2 rounded-full bg-white hover:bg-gray-100 cursor-pointer">
//           {item.toUpperCase()}
//         </div>
//       ))}
//     </nav>
//   )
// }

const tabs = ["Calendar", "Dashboards/Analytics", "Chat with AI", "Recommendations", "Geo-Assistant"]


export default function Header() {
  return (
    <nav
      className="relative h-32 shadow-sm rounded-b-xl"
      style={{ backgroundImage: `url(${navBg})` }}
    >
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 flex gap-3">
        {tabs.map((item) => {
          const isActive = item === "Recommendations"
          return (
            <div
              key={item}
              className={`
                relative min-w-[200px] text-center px-6 py-3 rounded-t-xl cursor-pointer text-sm font-semibold
                border border-gray-300 text-gray-800 transition-all duration-200
                backdrop-blur-md overflow-hidden
                ${isActive
                  ? "bg-white shadow-md scale-105 z-10"
                  : "bg-white/60 hover:bg-white/80"}
              `}
            >
              <span className="relative z-10">{item.toUpperCase()}</span>
              <div className="absolute bottom-0 left-0 w-full h-4 bg-gradient-to-b from-transparent to-white/70 pointer-events-none" />
            </div>
          )
        })}
      </div>
    </nav>
  )
}

