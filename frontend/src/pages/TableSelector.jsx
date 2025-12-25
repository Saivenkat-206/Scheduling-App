import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import "../styles/App.css";

const SHEET_TYPES = [
  "us_llc",
  "urgent",
  "regular",
  "doubtful",
  "domestic",
  "wabtec",
  "shutdown",
];

const MONTHS = [
  { value: "01", label: "January" },
  { value: "02", label: "February" },
  { value: "03", label: "March" },
  { value: "04", label: "April" },
  { value: "05", label: "May" },
  { value: "06", label: "June" },
  { value: "07", label: "July" },
  { value: "08", label: "August" },
  { value: "09", label: "September" },
  { value: "10", label: "October" },
  { value: "11", label: "November" },
  { value: "12", label: "December" },
];

const YEARS = ["25", "26", "27", "28", "29", "30"];

export default function TableSelector({ setTableData }) {
  const [sheetType, setSheetType] = useState("urgent");
  const [month, setMonth] = useState("01");
  const [year, setYear] = useState("25");
  const navigate = useNavigate();

  async function openTable() {
    const res = await api.post("/schedules/open_table", {
      sheet_type: sheetType,
      month,
      year,
    });

    setTableData(res.data);
    navigate("/table");
  }

  return (
    <div className="page">
      <div className="selector-vertical">
        <h2>Select Table</h2>

        <div className="field">
          <label>Sheet Type</label>
          <select value={sheetType} onChange={e => setSheetType(e.target.value)}>
            {SHEET_TYPES.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Month</label>
          <select value={month} onChange={e => setMonth(e.target.value)}>
            {MONTHS.map(m => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label>Year</label>
          <select value={year} onChange={e => setYear(e.target.value)}>
            {YEARS.map(y => (
              <option key={y} value={y}>20{y}</option>
            ))}
          </select>
        </div>

        <button className="button" onClick={openTable}>
          Open Table
        </button>
      </div>
    </div>
  );
}
