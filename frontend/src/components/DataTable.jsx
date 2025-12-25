import { useState } from "react";
import { DataGrid } from "@mui/x-data-grid";
import EditIcon from "@mui/icons-material/Edit";
import DeleteIcon from "@mui/icons-material/Delete";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import IconButton from "@mui/material/IconButton";
import { useNavigate } from "react-router-dom";

import "../styles/App.css";
import api from "../api/client";
import RowFormDialog from "./RowFormDialog";

// Define date columns for each sheet type
const GROUP_A_DATE_COLS = [
  "EDD", "REVISED EDD", "CASE", "HUB", "SHAFT", "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE"
];

const SHUTDOWN_DATE_COLS = [
  "EDD", "REVISED EDD", "CASE", "HUB", "SHAFT", "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE"
];

function getDateColumnsForTable(tableName) {
  if (tableName && tableName.toLowerCase().startsWith("shutdown")) {
    return SHUTDOWN_DATE_COLS;
  }
  return GROUP_A_DATE_COLS;
}

export default function DataTable({ tableData, refresh }) {
  const navigate = useNavigate();
  const { table_name, headers = [], rows = [] } = tableData || {};

  const [openForm, setOpenForm] = useState(false);
  const [editingRow, setEditingRow] = useState(null);

  const dateColumns = getDateColumnsForTable(table_name);

  /* =========================
     ADD / EDIT
     ========================= */
  function openAdd() {
    setEditingRow(null);
    setOpenForm(true);
  }

  function openEdit(row) {
    setEditingRow(row);
    setOpenForm(true);
  }

  async function saveRow(data) {
    const cleaned = {};
    headers.forEach((h) => {
      cleaned[h] =
        data[h] === "" || data[h] === null || data[h] === undefined
          ? "NA"
          : data[h];
    });

    try {
      if (editingRow?.id) {
        await api.put(
          `/schedules/rows/${table_name}/${editingRow.id}`,
          cleaned
        );
      } else {
        await api.post(`/schedules/rows/${table_name}`, cleaned);
      }
      setOpenForm(false);
      refresh();
    } catch (err) {
      console.error("Failed to save row", err);
    }
  }

  async function deleteRow(id) {
    if (!window.confirm("Delete this row?")) return;
    try {
      await api.delete(`/schedules/rows/${table_name}/${id}`);
      refresh();
    } catch (err) {
      console.error("Failed to delete row", err);
    }
  }

  /* =========================
     EXPORT / IMPORT
     ========================= */
  async function exportExcel() {
    try {
      const res = await api.get(
        `/schedules/export/${table_name}`,
        { responseType: "blob" }
      );

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${table_name}.xlsx`;
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error("Export failed", err);
    }
  }

  async function importExcel(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post(
        `/schedules/import/${table_name}`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      refresh();
    } catch (err) {
      console.error("Import failed", err);
      alert("Import failed. Check Excel headers.");
    }
  }

  /* =========================
     TABLE COLUMNS
     ========================= */
  const columns = headers.map((h) => ({
    field: h,
    headerName: h,
    flex: 1,
    editable: false,
    cellClassName: (params) => {
      // Green background for date columns with non-NA values
      if (dateColumns.includes(h) && params.value && params.value !== "NA") {
        return "cell-date-filled";
      }
      // Existing styles
      if (params.value && h.includes("DATE")) return "cell-date";
      if (h === "REMARKS" && params.value) return "cell-remarks";
      return "";
    },
  }));

  columns.push({
    field: "__actions__",
    headerName: "Actions",
    width: 120,
    sortable: false,
    renderCell: (params) => (
      <>
        <IconButton onClick={() => openEdit(params.row)} title="Edit">
          <EditIcon color="primary" />
        </IconButton>
        <IconButton onClick={() => deleteRow(params.row.id)} title="Delete">
          <DeleteIcon color="error" />
        </IconButton>
      </>
    ),
  });

  /* =========================
     RENDER
     ========================= */
  return (
    <div className="page">
      <div className="table-container">

        {/* HEADER BAR */}
        <div
          className="table-header"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 12,
          }}
        >
          {/* LEFT: BACK + TITLE */}
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <IconButton onClick={() => navigate("/select")} title="Back">
              <ArrowBackIcon />
            </IconButton>
            <div className="table-title">{table_name}</div>
          </div>

          {/* RIGHT: ACTION BUTTONS */}
          <div className="header-actions" style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-add" onClick={openAdd}>
              + Add Row
            </button>

            <button className="btn btn-refresh" onClick={refresh}>
              Refresh
            </button>

            <button className="btn btn-export" onClick={exportExcel}>
              Export
            </button>

            <label className="btn btn-import">
              Import
              <input
                type="file"
                accept=".xlsx"
                hidden
                onChange={importExcel}
              />
            </label>
          </div>
        </div>

        {/* TABLE */}
        <div style={{ height: 500 }}>
          <DataGrid
            rows={rows}
            columns={columns}
            getRowId={(row) => row.id}
            disableRowSelectionOnClick
            pageSizeOptions={[50, 100]}
          />
        </div>

        {/* ADD / EDIT FORM */}
        <RowFormDialog
          open={openForm}
          onClose={() => setOpenForm(false)}
          headers={headers}
          initialData={editingRow}
          onSubmit={saveRow}
          dateColumns={dateColumns}
        />
      </div>
    </div>
  );
}
