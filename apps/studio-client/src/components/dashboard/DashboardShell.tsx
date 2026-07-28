import React from "react";
import { DashboardLayout } from "./DashboardLayout";

interface DashboardShellProps {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
  isServerOnline: boolean;
  workspace: React.ReactNode;
}

export const DashboardShell: React.FC<DashboardShellProps> = ({
  theme,
  toggleTheme,
  isServerOnline,
  workspace
}) => {
  return (
    <DashboardLayout title="Dashboard">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Code Editor */}
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 overflow-hidden">
            <div className="bg-gray-800 dark:bg-slate-800 px-4 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="ml-4 text-sm font-medium text-gray-200">index.tsx</span>
              </div>
              <div className="flex space-x-2">
                <button className="text-gray-400 hover:text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                </button>
                <button className="text-gray-400 hover:text-white">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 0h-4m4 0l-5-5" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="bg-gray-900 dark:bg-slate-900 p-4 font-mono text-sm">
              <pre className="text-gray-200">{`function App() {
  return (
    <div className="app">
      <h1>Hello World!</h1>
    </div>
  );
}`}</pre>
            </div>
          </div>
          {workspace}
        </div>

        {/* Right Column - AI Assistant and Stats */}
        <div className="space-y-6">
          {/* AI Assistant Panel */}
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 overflow-hidden">
            <div className="bg-blue-50 dark:bg-blue-900/20 px-4 py-3 border-b border-gray-200 dark:border-slate-800">
              <h3 className="font-medium text-blue-800 dark:text-blue-200">AI Assistant</h3>
            </div>
            <div className="p-4 h-80 overflow-y-auto">
              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-blue-800 dark:text-blue-400 text-sm font-medium">U</span>
                  </div>
                  <div className="bg-white dark:bg-slate-800 rounded-lg p-3 max-w-[80%]">
                    <p className="text-gray-800 dark:text-slate-200">How can I optimize this function?</p>
                  </div>
                </div>
                <div className="flex items-start">
                  <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mr-3 flex-shrink-0">
                    <span className="text-green-800 dark:text-green-400 text-sm font-medium">AI</span>
                  </div>
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 max-w-[80%]">
                    <p className="text-gray-800 dark:text-slate-200">I recommend using memoization to optimize this function. Here's how you can implement it:</p>
                    <pre className="mt-2 bg-gray-800 dark:bg-slate-800 text-gray-200 p-2 rounded text-xs overflow-x-auto">
                      {`const optimizedFunc = useMemo(() => {
  return expensiveCalculation(props.data);
}, [props.data]);`}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
            <div className="border-t border-gray-200 dark:border-slate-800 p-3 bg-gray-50 dark:bg-slate-900">
              <div className="flex">
                <input
                  type="text"
                  placeholder="Ask AI anything..."
                  className="flex-1 border border-gray-300 dark:border-slate-700 rounded-l-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-slate-800 text-gray-900 dark:text-slate-200"
                />
                <button className="bg-blue-600 text-white px-4 py-2 rounded-r-lg hover:bg-blue-700 transition">
                  Send
                </button>
              </div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/30 dark:to-blue-900/10 rounded-xl p-4 border border-blue-200 dark:border-blue-900/30">
              <div className="text-blue-800 dark:text-blue-200 font-bold text-2xl">24</div>
              <div className="text-blue-600 dark:text-blue-400 text-sm">Active Projects</div>
            </div>
            <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/30 dark:to-green-900/10 rounded-xl p-4 border border-green-200 dark:border-green-900/30">
              <div className="text-green-800 dark:text-green-200 font-bold text-2xl">142</div>
              <div className="text-green-600 dark:text-green-400 text-sm">Tasks Completed</div>
            </div>
          </div>

          {/* Server Status */}
          <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-gray-200 dark:border-slate-800 p-4">
            <div className="flex items-center">
              <div className={`w-3 h-3 rounded-full mr-2 ${isServerOnline ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span className="text-sm font-medium text-gray-700 dark:text-slate-300">
                Server Status: {isServerOnline ? 'Online' : 'Offline'}
              </span>
            </div>
          </div>
        </div>
      </div>
      {/* বাংলা মন্তব্য: লেগ্যাসি ওয়ার্কস্পেস উপাদানগুলো ঠিকমতো রেন্ডার করার জন্য workspace প্রপ যোগ করা হলো */}
      {workspace}
    </DashboardLayout>
  );
};
