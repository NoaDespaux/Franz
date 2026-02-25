"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { LayoutDashboard, Ticket, AlertCircle, BarChart3 } from "lucide-react";

// API endpoints to our FastAPI backend
// In production, use NEXT_PUBLIC variables
const API_BASE = "http://localhost:8000/api";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"];

export default function Dashboard() {
  const [kpis, setKpis] = useState<any>(null);
  const [ticketsData, setTicketsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [kpiRes, ticketsRes] = await Promise.all([
          fetch(`${API_BASE}/kpis`),
          fetch(`${API_BASE}/tickets?limit=10`)
        ]);

        if (kpiRes.ok && ticketsRes.ok) {
          setKpis(await kpiRes.json());
          setTicketsData(await ticketsRes.json());
        }
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !kpis) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-white">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Fallback if APIs fail
  if (!kpis || !ticketsData) {
    return (
      <div className="flex h-screen w-full flex-col items-center justify-center bg-zinc-950 text-zinc-400">
        <AlertCircle className="mb-4 h-16 w-16 text-red-500" />
        <h1 className="text-2xl font-bold text-white">Cannot reach Dashboard API</h1>
        <p>Ensure the FastAPI service is running on port 8000.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8 font-sans">
      <div className="mb-8 flex items-center gap-3">
        <LayoutDashboard className="h-8 w-8 text-blue-500" />
        <h1 className="text-3xl font-bold tracking-tight">Franz Ticketing Dashboard</h1>
      </div>

      {/* KPI Cards */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-zinc-400">Total Tickets</CardTitle>
            <Ticket className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-white">{kpis.total_tickets}</div>
            <p className="text-xs text-zinc-500 mt-1">Processed by system</p>
          </CardContent>
        </Card>

        {kpis.by_priority.map((p: any) => (
          <Card key={p.name} className="bg-zinc-900 border-zinc-800">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">{p.name} Priority</CardTitle>
              <AlertCircle className="h-4 w-4 text-zinc-500" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-white">{p.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-8">
        {/* Category Breakdown */}
        <Card className="col-span-1 border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-zinc-100 flex items-center gap-2">
              <BarChart3 className="h-5 w-5" /> Tickets by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={kpis.by_category}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {kpis.by_category.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}
                    itemStyle={{ color: '#fff' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            {/* Custom Legend to ensure dark mode visibility */}
            <div className="flex flex-wrap justify-center gap-4 mt-4">
              {kpis.by_category.map((entry: any, index: number) => (
                <div key={entry.name} className="flex items-center gap-2 text-sm text-zinc-300">
                  <span className="h-3 w-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                  {entry.name}: {entry.value}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Origin Breakdown */}
        <Card className="col-span-2 border-zinc-800 bg-zinc-900">
          <CardHeader>
            <CardTitle className="text-zinc-100">Tickets by Origin (Discord vs Email)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={kpis.by_origin} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <XAxis dataKey="name" stroke="#71717a" />
                  <YAxis stroke="#71717a" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#fff' }}
                    cursor={{ fill: '#27272a' }}
                  />
                  <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Tickets Table */}
      <Card className="border-zinc-800 bg-zinc-900 overflow-hidden">
        <CardHeader>
          <CardTitle className="text-zinc-100">Recent Tickets Feed</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader className="bg-zinc-950">
              <TableRow className="border-zinc-800 hover:bg-zinc-900/50">
                <TableHead className="text-zinc-400">ID</TableHead>
                <TableHead className="text-zinc-400">Contact</TableHead>
                <TableHead className="text-zinc-400">Origin</TableHead>
                <TableHead className="text-zinc-400">Category</TableHead>
                <TableHead className="text-zinc-400">Priority</TableHead>
                <TableHead className="text-zinc-400">Snippet</TableHead>
                <TableHead className="text-right text-zinc-400">Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {ticketsData.tickets.map((t: any) => (
                <TableRow key={t.id} className="border-zinc-800 hover:bg-zinc-800/50">
                  <TableCell className="font-medium text-zinc-300">#{t.id}</TableCell>
                  <TableCell>{t.contact}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="border-zinc-700 text-zinc-300">
                      {t.origin}
                    </Badge>
                  </TableCell>
                  <TableCell>{t.category}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        t.priority === 'Critical' ? 'bg-red-500/10 text-red-500 hover:bg-red-500/20 shadow-none border-red-500/20' :
                          t.priority === 'High' ? 'bg-orange-500/10 text-orange-500 hover:bg-orange-500/20 shadow-none border-orange-500/20' :
                            'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20 shadow-none border-blue-500/20'
                      }
                      variant="outline"
                    >
                      {t.priority}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-[300px] truncate text-zinc-400">
                    {t.body.replace(/\n/g, ' ').substring(0, 60)}...
                  </TableCell>
                  <TableCell className="text-right text-zinc-500">
                    {new Date(t.date).toLocaleString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
