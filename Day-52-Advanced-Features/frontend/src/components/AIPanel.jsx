// frontend/src/components/AIPanel.jsx
import { useState } from "react";
import { Sparkles, BarChart3, List, Loader } from "lucide-react";
import { weeklySummary, breakdownTask } from "../api/ai";
import toast from "react-hot-toast";

export default function AIPanel() {
  const [summary, setSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [breakdownTitle, setBreakdownTitle] = useState("");
  const [breakdown, setBreakdown] = useState(null);
  const [loadingBreakdown, setLoadingBreakdown] = useState(false);

  const handleSummary = async () => {
    setLoadingSummary(true);
    try {
      const data = await weeklySummary();
      setSummary(data);
    } catch (err) {
      toast.error("Failed to generate summary");
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleBreakdown = async () => {
    if (!breakdownTitle.trim()) {
      toast.error("Enter a task title");
      return;
    }
    setLoadingBreakdown(true);
    try {
      const data = await breakdownTask(breakdownTitle);
      setBreakdown(data);
    } catch (err) {
      toast.error("Failed to break down task");
    } finally {
      setLoadingBreakdown(false);
    }
  };

  return (
    <div className="bg-gray-800 rounded-xl p-5 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={18} className="text-purple-400" />
        <h2 className="text-white font-semibold">AI Assistant</h2>
      </div>

      <div className="space-y-4">
        {/* Weekly Summary */}
        <div>
          <button
            onClick={handleSummary}
            disabled={loadingSummary}
            className="w-full flex items-center justify-center gap-2 bg-purple-900/50 hover:bg-purple-900/70 border border-purple-700 text-purple-300 text-sm py-2.5 rounded-lg transition-colors disabled:opacity-50"
          >
            {loadingSummary ? (
              <Loader size={14} className="animate-spin" />
            ) : (
              <BarChart3 size={14} />
            )}
            Generate Weekly Summary
          </button>

          {summary && (
            <div className="mt-3 bg-gray-900 rounded-lg p-3 border border-gray-700">
              <p className="text-gray-300 text-xs leading-relaxed">
                {summary.summary}
              </p>
              {summary.stats && (
                <div className="grid grid-cols-2 gap-2 mt-3">
                  {Object.entries(summary.stats)
                    .slice(0, 4)
                    .map(([k, v]) => (
                      <div
                        key={k}
                        className="bg-gray-800 rounded p-2 text-center"
                      >
                        <div className="text-white font-bold text-lg">{v}</div>
                        <div className="text-gray-500 text-xs capitalize">
                          {k.replace(/_/g, " ")}
                        </div>
                      </div>
                    ))}
                </div>
              )}
              {summary.recommendations?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500 mb-1">Recommendations:</p>
                  {summary.recommendations.map((r, i) => (
                    <p key={i} className="text-xs text-gray-400">
                      • {r}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Task Breakdown */}
        <div>
          <p className="text-xs text-gray-500 mb-2">
            Break a task into subtasks:
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={breakdownTitle}
              onChange={(e) => setBreakdownTitle(e.target.value)}
              placeholder="Task to break down..."
              className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white text-xs placeholder-gray-500 focus:outline-none focus:border-purple-500"
              onKeyDown={(e) => e.key === "Enter" && handleBreakdown()}
            />
            <button
              onClick={handleBreakdown}
              disabled={loadingBreakdown}
              className="shrink-0 bg-purple-700 hover:bg-purple-600 disabled:opacity-50 text-white px-3 py-2 rounded-lg transition-colors"
            >
              {loadingBreakdown ? (
                <Loader size={14} className="animate-spin" />
              ) : (
                <List size={14} />
              )}
            </button>
          </div>

          {breakdown && (
            <div className="mt-3 bg-gray-900 rounded-lg p-3 border border-gray-700">
              <p className="text-xs text-gray-500 mb-2">
                {breakdown.subtasks.length} subtasks · ~
                {breakdown.total_estimated_hours}h total
              </p>
              {breakdown.subtasks.map((st, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-1.5 border-b border-gray-800 last:border-0"
                >
                  <span className="text-xs text-gray-300">{st.title}</span>
                  <span className="text-xs text-gray-500 shrink-0 ml-2">
                    {st.estimated_hours}h
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
