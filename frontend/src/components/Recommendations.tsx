const recs = Array(4).fill("Lorem ipsum dolor sit amet, consectetur adipiscing elit.")

export default function Recommendations() {
  return (
    <section className="bg-purple-100 rounded-3xl p-6 w-full">
      <h2 className="text-2xl font-bold mb-6">RECOMMENDATIONS</h2>
      <div className="flex flex-col gap-4">
        {recs.map((text, idx) => (
          <div key={idx} className="bg-purple-200 rounded-2xl p-4 flex flex-col gap-3 md:flex-row md:justify-between items-center">
            <span className="text-sm font-semibold text-center md:text-left">{text}</span>
            <div className="flex gap-2">
              <button className="bg-white rounded-full px-4 py-1 text-sm hover:bg-green-100">APPLY</button>
              <button className="bg-white rounded-full px-4 py-1 text-sm hover:bg-red-100">DENY</button>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}