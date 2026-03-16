import { BrowserRouter, Navigate, Routes, Route, Outlet } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import TopNav from "./components/TopNav";

function DashboardLayout() {
  return (
    <>
      <TopNav />
      <Outlet />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/dashboard" element={<DashboardLayout />}>
          <Route index element={<Navigate to="analyze" replace />} />
          <Route path="analyze" element={<Dashboard view="analyze" />} />
          <Route path="reports" element={<Dashboard view="reports" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
