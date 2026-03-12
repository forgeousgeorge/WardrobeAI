import { NavLink } from 'react-router-dom'

const tabs = [
  {
    to: '/wardrobe',
    label: 'Wardrobe',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M4 6h16M4 10h16M4 14h16M4 18h16" />
      </svg>
    ),
  },
  {
    to: '/outfit',
    label: 'Today',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
  },
  {
    to: '/profile',
    label: 'Profile',
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
]

export default function BottomNav() {
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white border-t border-brand-200 flex items-center z-50"
      style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
    >
      {tabs.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          className={({ isActive }) =>
            `relative flex-1 flex flex-col items-center justify-center py-2 text-xs font-medium transition-colors ${
              isActive ? 'text-brand-600' : 'text-brand-300'
            }`
          }
        >
          {({ isActive }) => (
            <>
              <div className={`absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 rounded-full transition-all duration-200 ${isActive ? 'bg-brand-500' : 'bg-transparent'}`} />
              {tab.icon}
              <span className="mt-1">{tab.label}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
