"use client";
import { useState, useEffect } from "react";

export default function Tasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("MEDIUM");
  const [duedate, setDuedate] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    fetch("http://localhost:8000/tasks", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then((data) => {
  	setTasks(Array.isArray(data) ? data : []);
        setLoading(false);
      });
  }, []);

  async function handleCreate() {
    const token = localStorage.getItem("token");
    await fetch("http://localhost:8000/tasks", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        title,
        description,
        status: "TODO",
        duedate,
        priority,
      }),
    });
    window.location.reload();
  }

  async function handleDelete(id: number) {
    const token = localStorage.getItem("token");
    await fetch(`http://localhost:8000/tasks/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    window.location.reload();
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-3xl font-bold text-blue-600 mb-6">My Tasks</h1>

      <div className="bg-white p-6 rounded shadow mb-8">
        <h2 className="text-xl font-semibold mb-4">Add New Task</h2>
        <input className="w-full border p-2 rounded mb-3" placeholder="Title" value={title} onChange={e => setTitle(e.target.value)} />
        <input className="w-full border p-2 rounded mb-3" placeholder="Description" value={description} onChange={e => setDescription(e.target.value)} />
        <input className="w-full border p-2 rounded mb-3" type="date" value={duedate} onChange={e => setDuedate(e.target.value)} />
        <select className="w-full border p-2 rounded mb-3" value={priority} onChange={e => setPriority(e.target.value)}>
          <option>HIGH</option>
          <option>MEDIUM</option>
          <option>LOW</option>
        </select>
        <button className="bg-blue-600 text-white px-4 py-2 rounded" onClick={handleCreate}>Add Task</button>
      </div>

      {loading ? <p>Loading...</p> : (
        <ul>
          {tasks.map((task: any) => (
            <li key={task.id} className="bg-white p-4 rounded shadow mb-3 flex justify-between items-center">
              <div>
                <p className="font-semibold">{task.title}</p>
                <p className="text-gray-500 text-sm">{task.description}</p>
                <p className="text-xs mt-1">Status: {task.status} | Priority: {task.priority} | Due: {task.duedate}</p>
              </div>
              <button className="bg-red-500 text-white px-3 py-1 rounded" onClick={() => handleDelete(task.id)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}