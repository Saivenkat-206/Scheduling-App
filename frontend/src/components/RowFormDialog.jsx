import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import TextField from "@mui/material/TextField";
import React from "react";

export default function RowFormDialog({
  open,
  onClose,
  headers,
  initialData,
  onSubmit,
  dateColumns = []
}) {
  const [form, setForm] = React.useState(initialData || {});

  React.useEffect(() => {
    setForm(initialData || {});
  }, [initialData]);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{initialData ? "Edit Row" : "Add Row"}</DialogTitle>

      <DialogContent dividers>
        {headers.map(h => {
          const isDateColumn = dateColumns.includes(h);
          // Lock if it's a date column and already has a value (not NA)
          const locked = isDateColumn && initialData?.[h] && initialData?.[h] !== "NA";

          return (
            <TextField
              key={h}
              label={h}
              value={form[h] || ""}
              type={isDateColumn ? "date" : "text"}
              disabled={locked}
              onChange={e =>
                setForm({ ...form, [h]: e.target.value })
              }
              fullWidth
              margin="dense"
              InputLabelProps={isDateColumn ? { shrink: true } : {}}
            />
          );
        })}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={() => onSubmit(form)} variant="contained">
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}
