import React, { useState, useEffect } from "react";
import "./App.css";


const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8089";

const OPS = [
  { value: "sum", label: "Sumar" },
  { value: "sub", label: "Restar" },
  { value: "mul", label: "Multiplicar" },
  { value: "div", label: "Dividir" },
];

function App() {

  const [op, setOp] = useState("sum");             
  const [numbers, setNumbers] = useState(["", ""]); 
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");


  const [fType, setFType] = useState(""); 
  const [orderBy, setOrderBy] = useState("date");   
  const [direction, setDirection] = useState("desc"); 
  const [dateFrom, setDateFrom] = useState(""); 
  const [dateTo, setDateTo] = useState("");     
  const [limit, setLimit] = useState(20);


  const toFloatArray = (arr) =>
    arr
      .filter((x) => x !== "" && x !== null && x !== undefined)
      .map((x) => Number(x));

  const formatDate = (value) => {
    try {
      const d = new Date(value);
      if (isNaN(d.getTime())) return String(value);
      return d.toLocaleString();
    } catch { return String(value); }
  };


  const calcular = async () => {
    setError("");
    setResultado(null);
    setCargando(true);
    try {
      const nums = toFloatArray(numbers);
      if (nums.length < 1) {
        setError("Agrega al menos un número.");
        return;
      }

      const res = await fetch(`${API_URL}/calculadora/${op}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ numbers: nums }),
      });

      const data = await res.json();
      if (!res.ok) {

        const detail = data?.detail || data;
        const msg = detail?.message || JSON.stringify(detail);
        setError(`Error ${res.status} — ${msg}`);
        return;
      }

      setResultado(data.result);
      await obtenerHistorial(); 
    } catch (e) {
      console.error(e);
      setError("No se pudo calcular. Revisa que el backend esté arriba y CORS habilitado.");
    } finally {
      setCargando(false);
    }
  };

  const obtenerHistorial = async () => {
    setError("");
    try {
      const params = new URLSearchParams();
      if (fType) params.append("type", fType);
      if (orderBy) params.append("order_by", orderBy);
      if (direction) params.append("direction", direction);
      if (dateFrom) params.append("date_from", dateFrom);
      if (dateTo) params.append("date_to", dateTo);
      if (limit) params.append("limit", String(limit));

      const url = `${API_URL}/calculadora/historial${params.toString() ? `?${params}` : ""}`;
      const res = await fetch(url);
      const data = await res.json();
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setHistorial(Array.isArray(data.historial) ? data.historial : []);
    } catch (e) {
      console.error(e);
      setError("No se pudo obtener el historial.");
    }
  };

  useEffect(() => {
    obtenerHistorial();

  }, []);


  const updateNumber = (idx, value) => {
    const next = [...numbers];
    next[idx] = value;
    setNumbers(next);
  };

  const addNumber = () => setNumbers((prev) => [...prev, ""]);
  const removeNumber = (idx) => setNumbers((prev) => prev.filter((_, i) => i !== idx));
  const clearNumbers = () => setNumbers(["", ""]);

  return (
    <div className="App">
      <header className="App-header">
        <h1><strong>Calculadora React + FastAPI + MongoDB</strong></h1>


        <div className="panel">
          <select value={op} onChange={(e) => setOp(e.target.value)}>
            {OPS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          <div className="numbers">
            {numbers.map((val, idx) => (
              <div key={idx} className="num-item">
                <input
                  type="number"
                  value={val}
                  onChange={(e) => updateNumber(idx, e.target.value)}
                  placeholder={`Número ${idx + 1}`}
                />
                {numbers.length > 2 && (
                  <button className="remove" onClick={() => removeNumber(idx)} title="Quitar">
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="actions">
            <button onClick={addNumber} className="secondary">+ Agregar número</button>
            <button onClick={clearNumbers} className="secondary">Limpiar</button>
            <button onClick={calcular} disabled={cargando}>
              {cargando ? "Calculando..." : "Calcular"}
            </button>
          </div>
        </div>

        {resultado !== null && (
          <p className="result">
            Resultado: <strong>{resultado}</strong>
          </p>
        )}
        {error && <p className="error">{error}</p>}


        <div className="filters">
          <h3>Historial</h3>
          <div className="filter-row">
            <label>Tipo:</label>
            <select value={fType} onChange={(e) => setFType(e.target.value)}>
              <option value="">Todos</option>
              {OPS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>

            <label>Ordenar por:</label>
            <select value={orderBy} onChange={(e) => setOrderBy(e.target.value)}>
              <option value="date">Fecha</option>
              <option value="result">Resultado</option>
            </select>

            <label>Dirección:</label>
            <select value={direction} onChange={(e) => setDirection(e.target.value)}>
              <option value="desc">Desc</option>
              <option value="asc">Asc</option>
            </select>

            <br/>
            <label>Desde:</label>
            <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />

            <label>Hasta:</label>
            <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />

            <label>Límite:</label>
            <input
              type="number"
              min="1"
              max="200"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value || 1))}
              style={{ width: 80 }}
            />
            <button className="secondary" onClick={obtenerHistorial}>Aplicar</button>
          </div>
        </div>


        <div className="table">
          {historial.length === 0 ? (
            <div className="empty">Sin operaciones todavía.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Números</th>
                  <th>Resultado</th>
                  <th>Fecha</th>
                </tr>
              </thead>
              <tbody>
                {historial.map((op, i) => (
                  <tr key={`${op._id || i}-${op.date}`}>
                    <td>{op.type}</td>
                    <td>{Array.isArray(op.numbers) ? op.numbers.join(", ") : ""}</td>
                    <td><strong>{op.result}</strong></td>
                    <td>{formatDate(op.date)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

      </header>
    </div>
  );
}

export default App;
