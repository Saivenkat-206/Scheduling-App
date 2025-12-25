import { Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import LoginPage from "./pages/LoginPage";
import TableSelector from "./pages/TableSelector";
import DataTable from "./components/DataTable";
import api from "./api/client";
import "./styles/App.css";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [tableData, setTableData] = useState(null);

  const refreshTable = async () => {
    if (!tableData) return;
    const res = await api.get(`/schedules/rows/${tableData.table_name}`);
    setTableData(prev => ({ ...prev, rows: res.data.rows }));
  };

  return (
    <Routes>
      {/* Always land on login */}
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route
        path="/login"
        element={<LoginPage setToken={setToken} />}
      />

      {token && (
        <>
          <Route
            path="/select"
            element={<TableSelector setTableData={setTableData} />}
          />

          <Route
            path="/table"
            element={
              tableData
                ? <DataTable tableData={tableData} refresh={refreshTable} />
                : <Navigate to="/select" replace />
            }
          />
        </>
      )}

      {/* Block everything else */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
