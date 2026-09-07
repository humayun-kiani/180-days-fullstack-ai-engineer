// frontend/src/components/TaskForm.jsx
import { useState } from "react";
import { Plus, Sparkles, Loader } from "lucide-react";
import { createTask } from "../api/tasks";
import { analyzeTask, expandTask } from "../api/ai";
import toast from "react-hot-toast";

const PRIORITIES = ["urgent", "high", "medium", "low"];

export default function TaskForm({ onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [submitting, setSubmitting] = useState(false);
  const [expanding, setExpanding] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    try {
      const task = await createTask({ title, description, priority });
      onCreated?.(task);
      setTitle("");
      setDescription("");
      setPriority("medium");
      toast.success("Task created!");
    } catch (err) {
      toast.error("Failed to create task");
    } finally {
      setSubmitting(false);
    }
  };

  const handleExpand = async () => {
    if (!title.trim()) {
      toast.error("Enter a title first");
      return;
    }
    setExpanding(true);
    try {
      const result = await expandTask(title);
      setDescription(result.description);
      setPriority(result.suggested_priority);
      toast.success("AI expanded your task!");
    } catch (err) {
      toast.error("AI expansion failed");
    } finally {
      setExpanding(false);
    }
  };

  const handleAnalyze = async () => {
    if (!title.trim()) {
      toast.error("Enter a title first");
      return;
    }
    setAnalyzing(true);
    try {
      const result = await analyzeTask(title, description);
      setPriority(result.suggested_priority);
      toast.success(`AI suggests: ${result.suggested_priority} priority`);
    } catch (err) {
      toast.error("AI analysis failed");
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-gray-800 rounded-xl p-5 border border-gray-700 mb-6"
    >
      <h2 className="text-white font-semibold mb-4 flex items-center gap-2">
        <Plus size={18} className="text-blue-400" />
        New Task
      </h2>

      <div className="space-y-3">
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Task title..."
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />

        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Description (optional — or let AI write it)"
          rows={3}
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
        />

        {/* Priority select */}
        <div className="flex items-center gap-3">
          <label className="text-gray-400 text-sm shrink-0">Priority:</label>
          <div className="flex gap-2">
            {PRIORITIES.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => setPriority(p)}
                className={`text-xs px-3 py-1 rounded-full capitalize transition-colors ${
                  priority === p
                    ? p === "urgent"
                      ? "bg-red-600 text-white"
                      : p === "high"
                        ? "bg-orange-600 text-white"
                        : p === "medium"
                          ? "bg-blue-600 text-white"
                          : "bg-gray-600 text-white"
                    : "bg-gray-700 text-gray-400 hover:bg-gray-600"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        {/* AI Buttons */}
        <div className="flex items-center gap-3 pt-1">
          <button
            type="button"
            onClick={handleExpand}
            disabled={expanding}
            className="flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 disabled:opacity-50 transition-colors"
          >
            {expanding ? (
              <Loader size={12} className="animate-spin" />
            ) : (
              <Sparkles size={12} />
            )}
            AI Expand
          </button>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex items-center gap-1.5 text-xs text-purple-400 hover:text-purple-300 disabled:opacity-50 transition-colors"
          >
            {analyzing ? (
              <Loader size={12} className="animate-spin" />
            ) : (
              <Sparkles size={12} />
            )}
            AI Prioritize
          </button>
        </div>

        <button
          type="submit"
          disabled={submitting || !title.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
        >
          {submitting ? "Creating..." : "Create Task"}
        </button>
      </div>
    </form>
  );
}
