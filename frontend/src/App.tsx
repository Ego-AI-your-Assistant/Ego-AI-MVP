import Header from './components/Header'
import DayList from './components/DayList'
import Recommendations from './components/Recommendations'

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-[#d6eff1] to-white font-sans">
      <Header />
      <div className="flex p-6 gap-6">
        <DayList />
        <Recommendations />
      </div>
      <footer className="absolute bottom-0 w-full text-2xl text-center text-gray-400 py-4">
        <span className="font-bold text-purple-500">EGO</span><span className="text-green-400">:AI</span>
      </footer>
    </div>
  )
}