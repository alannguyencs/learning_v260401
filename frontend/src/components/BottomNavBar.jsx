import React from "react";
import { Link, useLocation } from "react-router-dom";

const tabs = [
  {
    label: "Slides",
    to: "/slides",
    match: (path) => path.startsWith("/slides"),
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
      </svg>
    ),
  },
  {
    label: "Voice",
    to: "/chat",
    match: (path) => path.startsWith("/chat"),
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path
          fillRule="evenodd"
          d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm-3 4a1 1 0 012 0 4 4 0 008 0 1 1 0 112 0 6 6 0 01-5 5.917V16h2a1 1 0 110 2H8a1 1 0 110-2h2v-2.083A6 6 0 014 8z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    label: "Dashboard",
    to: "/dashboard",
    match: (path) => path.startsWith("/dashboard"),
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        viewBox="0 0 20 20"
        fill="currentColor"
      >
        <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
      </svg>
    ),
  },
  {
    label: "Favorite",
    to: "/favorite",
    match: (path) => path.startsWith("/favorite"),
    icon: (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        className="h-6 w-6"
        viewBox="0 0 24 24"
        fill="currentColor"
      >
        <path d="M2 20h2V9H2v11zm20-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L13.17 0 6.59 6.59C6.22 6.95 6 7.45 6 8v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73V9z" />
      </svg>
    ),
  },
];

const BottomNavBar = () => {
  const location = useLocation();
  const currentPath = location.pathname;

  return (
    <nav className="bg-white border-t border-gray-200 shadow-lg">
      <div className="flex h-16 mx-auto max-w-4xl w-full">
        {tabs.map((tab) => {
          const isActive = tab.match(currentPath);
          return (
            <Link
              key={tab.to}
              to={tab.to}
              className={`flex-1 flex flex-col items-center justify-center transition-colors duration-200 ${
                isActive
                  ? "text-blue-600 bg-blue-50"
                  : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
              }`}
            >
              {tab.icon}
              <span className="text-xs mt-1 font-medium">{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNavBar;
