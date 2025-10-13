import React, { useState, useEffect } from "react";
import "./App.css";

// Usa REACT_APP_API_URL si existe; si no, localhost:8000
const API_URL = process.env.REACT_APP_API_URL || "http://127.0.0.1:8089";

function App() {
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [resultado, setResultado] = useState(null);
  const [historial, setHistorial] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  const calcularSuma = async () => {
    setError("");
    setCargando(true);
    try {
      // Convierte a número (vacío -> 0)
      const aNum = a === "" ? 0 : Number(a);
      const bNum = b === "" ? 0 : Number(b);

      const res = await fetch(`${API_URL}/calculadora/sum?a=${aNum}&b=${bNum}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setResultado(data.resultado);
      await obtenerHistorial(); // refresca tabla
    } catch (e) {
      console.error(e);
      setError("No se pudo calcular la suma. Revisa que el backend esté arriba y CORS habilitado.");
    } finally {
      setCargando(false);
    }
  };

  const obtenerHistorial = async () => {
    setError("");
    try {
      const res = await fetch(`${API_URL}/calculadora/historial`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      // Espera { historial: [...] }
      setHistorial(Array.isArray(data.historial) ? data.historial : []);
    } catch (e) {
      console.error(e);
      setError("No se pudo obtener el historial.");
    }
  };

  useEffect(() => {
    obtenerHistorial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const formatDate = (value) => {
    try {
      // soporta ISO/Date de Mongo (p.ej. 2025-09-08T...Z)
      const d = new Date(value);
      if (isNaN(d.getTime())) return String(value);
      return d.toLocaleString();
    } catch {
      return String(value);
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1><strong>Bienvenidos a la Calculadora en React con FastAPI y MongoDB </strong></h1>

        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <input
            type="number"
            value={a}
            onChange={(e) => setA(e.target.value)}
            placeholder="Número A"
          />
          <input
            type="number"
            value={b}
            onChange={(e) => setB(e.target.value)}
            placeholder="Número B"
          />
          <button onClick={calcularSuma} disabled={cargando}>
            {cargando ? "Calculando..." : "Calcular"}
          </button>
        </div>

        {resultado !== null && <p>Resultado: {resultado}</p>}
        {error && <p style={{ color: "salmon" }}>{error}</p>}

        <h3 style={{ marginTop: 24 }}>Historial</h3>
        <ul style={{ textAlign: "left", maxWidth: 520 }}>
          {historial.length === 0 && <li>Sin operaciones todavía.</li>}
          {historial.map((op, i) => (
            <li key={`${op._id || i}-${op.date}`}>
              {op.a} + {op.b} = <strong>{op.resultado}</strong>{" "}
              <small>({formatDate(op.date)})</small>
            </li>
          ))}
        </ul>
      </header>
    </div>
  );
}

export default App;

//Comentario para checar el workflow de Frontend 2