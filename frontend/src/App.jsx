import { Routes, Route, Navigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/admin/LoginPage'
import AdminLayout from './pages/admin/AdminLayout'
import DashboardPage from './pages/admin/DashboardPage'
import RequestsPage from './pages/admin/RequestsPage'
import UsersPage from './pages/admin/UsersPage'
import AnalyticsPage from './pages/admin/AnalyticsPage'
import TeacherWebApp from './pages/webapp/TeacherWebApp'
import StudentWebApp from './pages/webapp/StudentWebApp'
import StartWebApp from './pages/webapp/StartWebApp'

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/admin/login" replace />
}

export default function App() {
  return (
    <Routes>
      {/* Public landing */}
      <Route path="/" element={<LandingPage />} />

      {/* Admin auth */}
      <Route path="/admin/login" element={<LoginPage />} />

      {/* Admin panel */}
      <Route path="/admin" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="requests" element={<RequestsPage />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
      </Route>

      {/* Telegram WebApp Dashboards */}
      <Route path="/start" element={<StartWebApp />} />
      <Route path="/webapp/teacher" element={<TeacherWebApp />} />
      <Route path="/webapp/student" element={<StudentWebApp />} />
    </Routes>
  )
}

