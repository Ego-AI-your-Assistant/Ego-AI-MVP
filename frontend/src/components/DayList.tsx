const days = ["30.06 Mon", "01.07 Tue", "02.07 Wed", "03.07 Fri", "04.07 Sat"]

export default function DayList() {
  return (
    <aside className="bg-purple-100 rounded-3xl p-4 w-1/4 min-w-[180px]">
      <h2 className="font-bold text-center mb-4">LIST OF DAYS</h2>
      <div className="flex flex-col gap-3">
        {days.map((day, idx) => (
          <div key={idx} className="bg-purple-200 rounded-full py-2 px-4 text-center cursor-pointer hover:bg-purple-300 transition">
            {day}
          </div>
        ))}
      </div>
    </aside>
  )
}