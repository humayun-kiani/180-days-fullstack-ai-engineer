// frontend/src/pages/BoardPage.jsx
import { useState, useEffect, useCallback } from "react";
import { Filter, RefreshCw } from "lucide-react";
import { listTasks } from "../api/tasks";
import TaskCard from "../components/TaskCard";
import TaskForm from "../components/TaskForm";
import AIPanel from "../components/AIPanel";
import NavBar from "../components/NavBar";
import { useWebSocket } from "../hooks/useWebSocket";
import toast from "react-hot-toast";

const STATUSES = ["pending", "in_progress", "done"];
const STATUS_LABELS = {
  pending: "To Do",
  in_progress: "In Progress",
  done: "Done",
};
const STATUS_COLORS = {
  pending: "border-gray-700",
  in_progress: "border-blue-700",
  done: "border-green-700",
};

export default function BoardPage() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({ status: "", priority: "" });

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (filter.status) params.status = filter.status;
      if (filter.priority) params.priority = filter.priority;
      const data = await listTasks(params);
      setTasks(data.tasks);
    } catch (err) {
      toast.error("Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchTasks();
  }, [fetchTasks]);

  // WebSocket for real-time updates
  useWebSocket(
    useCallback(
      (msg) => {
        if (
          msg.type === "task_created" ||
          msg.type === "task_updated" ||
          msg.type === "task_deleted"
        ) {
          fetchTasks();
        }
      },
      [fetchTasks],
    ),
  );

  const handleCreated = (task) => {
    setTasks((prev) => [task, ...prev]);
  };

  const handleUpdate = (updated) => {
    setTasks((prev) => prev.map((t) => (t.id === updated.id ? updated : t)));
  };

  const handleDelete = (id) => {
    setTasks((prev) => prev.filter((t) => t.id !== id));
  };

  const tasksByStatus = (status) => tasks.filter((t) => t.status === status);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <NavBar />

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-xl font-bold">Task Board</h1>
          <div className="flex items-center gap-3">
            {/* Priority filter */}
            <select
              value={filter.priority}
              onChange={(e) =>
                setFilter((f) => ({ ...f, priority: e.target.value }))
              }
              className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none"
            >
              <option value="">All priorities</option>
              {["urgent", "high", "medium", "low"].map((p) => (
                <option key={p} value={p} className="capitalize">
                  {p}
                </option>
              ))}
            </select>

            <button
              onClick={fetchTasks}
              className="flex items-center gap-1 text-gray-400 hover:text-white text-sm transition-colors"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left sidebar: form + AI */}
          <div className="lg:col-span-1 space-y-4">
            <TaskForm onCreated={handleCreated} />
            <AIPanel />
          </div>

          {/* Kanban columns */}
          <div className="lg:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-4">
            {STATUSES.map((status) => {
              const columnTasks = tasksByStatus(status);
              return (
                <div
                  key={status}
                  className={`bg-gray-900 rounded-xl p-4 border ${STATUS_COLORS[status]}`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-semibold text-sm text-gray-300">
                      {STATUS_LABELS[status]}
                    </h3>
                    <span className="text-xs bg-gray-700 text-gray-400 rounded-full px-2 py-0.5">
                      {columnTasks.length}
                    </span>
                  </div>

                  {loading && columnTasks.length === 0 ? (
                    <div className="text-center py-8 text-gray-600 text-sm">
                      Loading...
                    </div>
                  ) : columnTasks.length === 0 ? (
                    <div className="text-center py-8 text-gray-700 text-sm">
                      No tasks
                    </div>
                  ) : (
                    columnTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onUpdate={handleUpdate}
                        onDelete={handleDelete}
                      />
                    ))
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
