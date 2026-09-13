// frontend/src/components/TaskCard.jsx
import { useState } from "react";
import { Trash2, ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import clsx from "clsx";
import { updateTask, deleteTask } from "../api/tasks";
import { analyzeTask } from "../api/ai";
import toast from "react-hot-toast";

const PRIORITY_COLORS = {
  urgent: "bg-red-900/50 border-red-700 text-red-300",
  high: "bg-orange-900/50 border-orange-700 text-orange-300",
  medium: "bg-blue-900/50 border-blue-700 text-blue-300",
  low: "bg-gray-800 border-gray-700 text-gray-400",
};

const STATUS_OPTIONS = ["pending", "in_progress", "done"];
const STATUS_LABELS = {
  pending: "Pending",
  in_progress: "In Progress",
  done: "Done",
};

export default function TaskCard({ task, onUpdate, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiData, setAiData] = useState(null);

  const handleStatusChange = async (newStatus) => {
    try {
      const updated = await updateTask(task.id, { status: newStatus });
      onUpdate?.(updated);
      toast.success(`Status updated to ${STATUS_LABELS[newStatus]}`);
    } catch (err) {
      toast.error("Failed to update status");
    }
  };

  const handleDelete = async () => {
    if (!confirm("Delete this task?")) return;
    try {
      await deleteTask(task.id);
      onDelete?.(task.id);
      toast.success("Task deleted");
    } catch (err) {
      toast.error("Failed to delete task");
    }
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const analysis = await analyzeTask(task.title, task.description);
      setAiData(analysis);
      // Save AI data to task
      await updateTask(task.id, {
        ai_summary: analysis.summary,
        ai_priority: analysis.suggested_priority,
      });
      toast.success("AI analysis complete");
    } catch (err) {
      toast.error("AI analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div
      className={clsx(
        "rounded-lg border p-4 mb-3 transition-all",
        PRIORITY_COLORS[task.priority] || PRIORITY_COLORS.medium,
      )}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={clsx(
                "text-xs px-2 py-0.5 rounded-full font-medium uppercase tracking-wide",
                task.priority === "urgent"
                  ? "bg-red-600 text-white"
                  : task.priority === "high"
                    ? "bg-orange-600 text-white"
                    : task.priority === "medium"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-600 text-gray-200",
              )}
            >
              {task.priority}
            </span>
            <span className="text-xs text-gray-400">
              {STATUS_LABELS[task.status]}
            </span>
          </div>
          <h3 className="font-medium text-white text-sm leading-snug">
            {task.title}
          </h3>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
          <button
            onClick={handleDelete}
            className="p-1 text-gray-500 hover:text-red-400 transition-colors"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      {/* Expanded view */}
      {expanded && (
        <div className="mt-3 space-y-3">
          {task.description && (
            <p className="text-sm text-gray-400">{task.description}</p>
          )}

          {/* Status change */}
          <div className="flex gap-2">
            {STATUS_OPTIONS.map((s) => (
              <button
                key={s}
                onClick={() => handleStatusChange(s)}
                className={clsx(
                  "text-xs px-3 py-1 rounded-full transition-colors",
                  task.status === s
                    ? "bg-blue-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600",
                )}
              >
                {STATUS_LABELS[s]}
              </button>
            ))}
          </div>

          {/* AI Section */}
          {(task.ai_summary || aiData) && (
            <div className="bg-gray-900/50 rounded p-3 border border-gray-700">
              <div className="flex items-center gap-1 mb-1">
                <Sparkles size={12} className="text-purple-400" />
                <span className="text-xs text-purple-400 font-medium">
                  AI Analysis
                </span>
              </div>
              <p className="text-xs text-gray-300">
                {aiData?.summary || task.ai_summary}
              </p>
              {aiData && (
                <p className="text-xs text-gray-500 mt-1">
                  Suggested priority: {aiData.suggested_priority} (
                  {aiData.confidence} confidence)
                </p>
              )}
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300 disabled:opacity-50 transition-colors"
          >
            <Sparkles size={12} />
            {analyzing ? "Analyzing..." : "Ask AI to analyze"}
          </button>
        </div>
      )}
    </div>
  );
}
