import { useEffect, useState } from "react";
import api from "./services/api";
import "./App.css";

const emptyProject = {
  name: "",
  target_url: "http://juice-shop:3000",
  description: "",
};

function App() {
  const [currentView, setCurrentView] = useState(
    localStorage.getItem("apuguard_token") ? "dashboard" : "home"
  );

  const [token, setToken] = useState(
    localStorage.getItem("apuguard_token")
  );

  const [loginForm, setLoginForm] = useState({
    email: "",
    password: "",
  });

  const [registerForm, setRegisterForm] = useState({
    full_name: "",
    email: "",
    password: "",
    confirm_password: "",
  });

  const [projectForm, setProjectForm] = useState(emptyProject);
  const [projects, setProjects] = useState([]);
  const [report, setReport] = useState(null);
  const [selectedScanId, setSelectedScanId] = useState(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [currentUser, setCurrentUser] = useState(null);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminProjects, setAdminProjects] = useState([]);
  const [adminSection, setAdminSection] = useState("users");

  useEffect(() => {
    if (token) {
      loadCurrentUser();
      loadProjects();
    }
  }, [token]);

  const clearFeedback = () => {
    setMessage("");
    setError("");
  };

  const getErrorMessage = (exception) => {
    const detail = exception.response?.data?.detail;

    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg)
        .filter(Boolean)
        .join(". ");
    }

    if (typeof detail === "string") {
      return detail;
    }

    if (detail && typeof detail === "object") {
      return detail.msg || "Ocurrió un error inesperado.";
    }

    return exception.message || "Ocurrió un error inesperado.";
  };

  const loadCurrentUser = async () => {
    try {
      const response = await api.get("/auth/me");
      setCurrentUser(response.data);

      return response.data;
    } catch (exception) {
      localStorage.removeItem("apuguard_token");
      setToken(null);
      setCurrentUser(null);
      setCurrentView("login");

      throw exception;
    }
  };

  const login = async (event) => {
    event.preventDefault();
    clearFeedback();
    setLoading(true);

    try {
      const body = new URLSearchParams();
      body.append("username", loginForm.email);
      body.append("password", loginForm.password);

      const response = await api.post("/auth/login", body, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      localStorage.setItem(
        "apuguard_token",
        response.data.access_token
      );

      setToken(response.data.access_token);
      setCurrentView("dashboard");
      setMessage("Inicio de sesión correcto.");
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  const register = async (event) => {
    event.preventDefault();
    clearFeedback();

    const passwordRegex =
      /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z\d]).{10,72}$/;

    if (!passwordRegex.test(registerForm.password)) {
      setError(
        "La contraseña debe tener entre 10 y 72 caracteres, una mayúscula, una minúscula, un número y un símbolo."
      );
      return;
    }

    if (registerForm.password !== registerForm.confirm_password) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);

    try {
      const registeredEmail = registerForm.email.trim();

      await api.post("/auth/register", {
        full_name: registerForm.full_name.trim(),
        email: registeredEmail,
        password: registerForm.password,
      });

      setRegisterForm({
        full_name: "",
        email: "",
        password: "",
        confirm_password: "",
      });

      setLoginForm({
        email: registeredEmail,
        password: "",
      });

      setCurrentView("login");
      setMessage(
        "Cuenta creada correctamente. Ahora puedes iniciar sesión."
      );
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem("apuguard_token");
    setToken(null);
    setCurrentUser(null);
    setProjects([]);
    setAdminUsers([]);
    setAdminProjects([]);
    setReport(null);
    setSelectedScanId(null);
    setMessage("");
    setError("");
    setCurrentView("home");
  };

  const loadAdminUsers = async () => {
  clearFeedback();
  setLoading(true);

  try {
    const response = await api.get("/admin/users");
    setAdminUsers(response.data);
  } catch (exception) {
    setError(getErrorMessage(exception));
  } finally {
    setLoading(false);
  }
};

const loadAdminProjects = async () => {
  clearFeedback();
  setLoading(true);

  try {
    const response = await api.get("/admin/projects");
    setAdminProjects(response.data);
  } catch (exception) {
    setError(getErrorMessage(exception));
  } finally {
    setLoading(false);
  }
};

const openAdminPanel = async () => {
  clearFeedback();
  setCurrentView("admin");
  setAdminSection("users");

  await loadAdminUsers();
};

const changeUserStatus = async (user) => {
  const action = user.is_active ? "desactivar" : "activar";

  const confirmed = window.confirm(
    `¿Deseas ${action} al usuario ${user.full_name}?`
  );

  if (!confirmed) {
    return;
  }

  clearFeedback();
  setLoading(true);

  try {
    await api.patch(`/admin/users/${user.id}/status`, {
      is_active: !user.is_active,
    });

    setMessage(`Usuario ${action === "activar" ? "activado" : "desactivado"} correctamente.`);
    await loadAdminUsers();
  } catch (exception) {
    setError(getErrorMessage(exception));
  } finally {
    setLoading(false);
  }
};

const deleteAdminUser = async (user) => {
  const confirmed = window.confirm(
    `¿Eliminar permanentemente al usuario ${user.full_name}?\n\n` +
      "Esta acción no se puede deshacer."
  );

  if (!confirmed) {
    return;
  }

  clearFeedback();
  setLoading(true);

  try {
    await api.delete(`/admin/users/${user.id}`);
    setMessage("Usuario eliminado correctamente.");
    await loadAdminUsers();
  } catch (exception) {
    setError(getErrorMessage(exception));
  } finally {
    setLoading(false);
  }
};

const deleteAdminProject = async (project) => {
  const confirmed = window.confirm(
    `¿Eliminar el proyecto "${project.name}"?\n\n` +
      "También podrían eliminarse sus escaneos y reportes relacionados."
  );

  if (!confirmed) {
    return;
  }

  clearFeedback();
  setLoading(true);

  try {
    await api.delete(`/admin/projects/${project.id}`);
    setMessage("Proyecto eliminado correctamente.");
    await loadAdminProjects();
  } catch (exception) {
    setError(getErrorMessage(exception));
  } finally {
    setLoading(false);
  }
};

  const loadProjects = async () => {
    clearFeedback();

    try {
      const response = await api.get("/projects");
      setProjects(response.data);
    } catch (exception) {
      setError(getErrorMessage(exception));
    }
  };

  const createProject = async (event) => {
    event.preventDefault();
    clearFeedback();
    setLoading(true);

    try {
      await api.post("/projects", projectForm);
      setProjectForm(emptyProject);
      setMessage("Proyecto creado correctamente.");
      await loadProjects();
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };
  
  const isDemoTarget = (targetUrl) => {
    try {
      const parsed = new URL(targetUrl);

      const hostname = parsed.hostname.toLowerCase();

      const port =
        parsed.port ||
        (parsed.protocol === "https:" ? "443" : "80");

      return (
        (hostname === "juice-shop" && port === "3000") ||
        (hostname === "localhost" && port === "3000") ||
        (hostname === "127.0.0.1" && port === "3000")
      );
    } catch {
      return false;
    }
  };

  const startScan = async (project) => {
    clearFeedback();

    const demoTarget = isDemoTarget(project.target_url);
    let authorizationConfirmed = false;

    if (demoTarget) {
      const confirmed = window.confirm(
        "El análisis del laboratorio puede tardar varios minutos. " +
          "¿Deseas continuar?"
      );

      if (!confirmed) {
        return;
      }
    } else {
      authorizationConfirmed = window.confirm(
        `ADVERTENCIA DE SEGURIDAD\n\n` +
          `Está a punto de analizar:\n${project.target_url}\n\n` +
          `Confirma que cuentas con autorización expresa del ` +
          `propietario para ejecutar pruebas de seguridad sobre ` +
          `este sistema.\n\n` +
          `El análisis puede generar tráfico y afectar el servicio.\n\n` +
          `¿Confirmas que tienes autorización?`
      );

      if (!authorizationConfirmed) {
        setError(
          "El análisis fue cancelado porque no se confirmó la autorización."
        );
        return;
      }
    }

    setLoading(true);
    setReport(null);

    try {
      const response = await api.post(
        `/scans/projects/${project.id}`,
        {
          authorization_confirmed: authorizationConfirmed,
        }
      );

      setSelectedScanId(response.data.id);

      setMessage(
        `Escaneo completado. Se identificaron ` +
          `${response.data.total_alerts} hallazgos.`
      );
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  const loadLatestScan = async (projectId) => {
    clearFeedback();
    setLoading(true);

    try {
      const response = await api.get(
        `/scans/projects/${projectId}`
      );

      if (!response.data.length) {
        throw new Error(
          "El proyecto todavía no tiene escaneos registrados."
        );
      }

      setSelectedScanId(response.data[0].id);
      setMessage(
        `Escaneo seleccionado: ${response.data[0].id}`
      );
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    if (!selectedScanId) {
      setError("Primero ejecuta o selecciona un escaneo.");
      return;
    }

    clearFeedback();
    setLoading(true);

    try {
      const response = await api.post(
        `/reports/scans/${selectedScanId}/generate`
      );

      setReport(response.data);
      setMessage("Reporte generado correctamente.");
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = async () => {
    if (!selectedScanId) {
      setError("Primero ejecuta o selecciona un escaneo.");
      return;
    }

    clearFeedback();
    setLoading(true);

    try {
      const response = await api.get(
        `/reports/scans/${selectedScanId}/pdf`,
        {
          responseType: "blob",
        }
      );

      const url = window.URL.createObjectURL(
        new Blob([response.data], {
          type: "application/pdf",
        })
      );

      const link = document.createElement("a");
      link.href = url;
      link.download = `ApuGuard_AI_Scan_${selectedScanId}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
      setMessage("PDF descargado correctamente.");
    } catch (exception) {
      setError(getErrorMessage(exception));
    } finally {
      setLoading(false);
    }
  };

  if (!token && currentView === "home") {
    return (
      <main className="landing-page">
        <nav className="landing-nav">
          <div className="landing-brand">
            <div className="brand-mark small">AG</div>

            <div>
              <strong>ApuGuard AI</strong>
              <span>Seguridad automatizada</span>
            </div>
          </div>

          <div className="landing-nav-actions">
            <button
              type="button"
              className="secondary"
              onClick={() => setCurrentView("register")}
            >
              Registrarse
            </button>

            <button
              type="button"
              onClick={() => setCurrentView("login")}
            >
              Iniciar sesión
            </button>
          </div>
        </nav>

        <section className="landing-hero">
          <div className="landing-content">
            <span className="eyebrow">
              PLATAFORMA INTELIGENTE DE CIBERSEGURIDAD
            </span>

            <h1>
              Detecta vulnerabilidades antes de que se conviertan en
              incidentes
            </h1>

            <p>
              ApuGuard AI integra OWASP ZAP, análisis automatizado,
              clasificación de riesgos y generación de informes
              profesionales en PDF.
            </p>

            <div className="landing-actions">
              <button
                type="button"
                onClick={() => setCurrentView("login")}
              >
                Comenzar análisis
              </button>
            </div>

            <div className="landing-features">
              <article>
                <span>01</span>
                <h3>Escaneo real</h3>
                <p>
                  Exploración automatizada mediante OWASP ZAP.
                </p>
              </article>

              <article>
                <span>02</span>
                <h3>Análisis inteligente</h3>
                <p>
                  Clasificación, consolidación y priorización de riesgos.
                </p>
              </article>

              <article>
                <span>03</span>
                <h3>Reporte profesional</h3>
                <p>
                  Resumen ejecutivo, recomendaciones y exportación PDF.
                </p>
              </article>
            </div>
          </div>

          <aside className="landing-visual">
            <div className="security-orbit">
              <div className="orbit-ring ring-one" />
              <div className="orbit-ring ring-two" />

              <div className="security-core">
                <span>AG</span>
                <small>SECURE</small>
              </div>

              <div className="orbit-item item-one">ZAP</div>
              <div className="orbit-item item-two">JWT</div>
              <div className="orbit-item item-three">PDF</div>
            </div>
          </aside>
        </section>

        <footer className="landing-footer">
          <span>© 2026 ApuGuard AI</span>
          <span>Uso exclusivo sobre objetivos autorizados</span>
        </footer>
      </main>
    );
  }

  if (!token && currentView === "register") {
    return (
      <main className="login-page">
        <section className="login-card register-card">
          <button
            type="button"
            className="back-home-button"
            onClick={() => {
              clearFeedback();
              setCurrentView("home");
            }}
          >
            ← Volver al inicio
          </button>

          <div className="brand-mark">AG</div>

          <h1>Crear cuenta</h1>

          <p className="subtitle">
            Registra un analista para utilizar ApuGuard AI
          </p>

          <form onSubmit={register}>
            <label>
              Nombre completo
              <input
                type="text"
                required
                minLength="3"
                value={registerForm.full_name}
                onChange={(event) =>
                  setRegisterForm({
                    ...registerForm,
                    full_name: event.target.value,
                  })
                }
                placeholder="Ingrese su nombre completo"
              />
            </label>

            <label>
              Correo electrónico
              <input
                type="email"
                required
                value={registerForm.email}
                onChange={(event) =>
                  setRegisterForm({
                    ...registerForm,
                    email: event.target.value,
                  })
                }
                placeholder="usuario@empresa.com"
              />
            </label>

            <label>
              Contraseña
              <input
                type="password"
                required
                minLength="10"
                value={registerForm.password}
                onChange={(event) =>
                  setRegisterForm({
                    ...registerForm,
                    password: event.target.value,
                  })
                }
                placeholder="Mínimo 10 caracteres"
              />
            </label>

            <label>
              Confirmar contraseña
              <input
                type="password"
                required
                minLength="10"
                value={registerForm.confirm_password}
                onChange={(event) =>
                  setRegisterForm({
                    ...registerForm,
                    confirm_password: event.target.value,
                  })
                }
                placeholder="Repite tu contraseña"
              />
            </label>

            {message && (
              <div className="alert success">{message}</div>
            )}

            {error && <div className="alert error">{error}</div>}

            <button disabled={loading} type="submit">
              {loading ? "Creando cuenta..." : "Registrarme"}
            </button>
          </form>

          <button
            type="button"
            className="login-switch-button"
            onClick={() => {
              clearFeedback();
              setCurrentView("login");
            }}
          >
            Ya tengo una cuenta
          </button>

          <p className="security-note">
            Contraseñas protegidas mediante BCrypt
          </p>
        </section>
      </main>
    );
  }

  if (!token && currentView === "login") {
    return (
      <main className="login-page">
        <section className="login-card">

          <button
            type="button"
            className="back-home-button"
            onClick={() => {
              clearFeedback();
              setCurrentView("home");
            }}
          >
            ← Volver al inicio
          </button>

          <div className="brand-mark">AG</div>

          <h1>ApuGuard AI</h1>

          <p className="subtitle">
            Pentesting inteligente y reportes OWASP
          </p>

          <form onSubmit={login}>
            <label>
              Correo electrónico
              <input
                type="email"
                required
                value={loginForm.email}
                onChange={(event) =>
                  setLoginForm({
                    ...loginForm,
                    email: event.target.value,
                  })
                }
                placeholder="analista@apuguard.com"
              />
            </label>

            <label>
              Contraseña
              <input
                type="password"
                required
                value={loginForm.password}
                onChange={(event) =>
                  setLoginForm({
                    ...loginForm,
                    password: event.target.value,
                  })
                }
                placeholder="••••••••"
              />
            </label>

            {error && <div className="alert error">{error}</div>}

            <button disabled={loading} type="submit">
              {loading ? "Ingresando..." : "Iniciar sesión"}
            </button>
             <button
              type="button"
              className="login-switch-button"
              onClick={() => {
                clearFeedback();
                setCurrentView("register");
              }}
            >
              ¿No tienes cuenta? Regístrate
            </button>
          </form>

          <p className="security-note">
            Acceso protegido mediante JWT y BCrypt
          </p>
        </section>
      </main>
    );
  }

  if (token && currentView === "admin") {
    return (
      <div className="app-shell">
        <header className="topbar">
          <div>
            <h1>Administración</h1>
            <p>Gestión centralizada de ApuGuard AI</p>
          </div>

          <div className="topbar-actions">
            <button
              type="button"
              className="secondary"
              onClick={() => {
                clearFeedback();
                setCurrentView("dashboard");
              }}
            >
              Volver al dashboard
            </button>

            <button
              type="button"
              className="secondary"
              onClick={logout}
            >
              Cerrar sesión
            </button>
          </div>
        </header>

        <main className="dashboard">
          {loading && (
            <div className="loading-banner">
              Procesando solicitud...
            </div>
          )}

          {message && (
            <div className="alert success">{message}</div>
          )}

          {error && <div className="alert error">{error}</div>}

          <section className="hero-panel">
            <div>
              <span className="eyebrow">
                ADMINISTRACIÓN DEL SISTEMA
              </span>

              <h2>Panel de control</h2>

              <p>
                Administra usuarios registrados y proyectos de análisis.
              </p>
            </div>

            <div className="hero-stat">
              <strong>
                {adminUsers.length + adminProjects.length}
              </strong>
              <span>Registros administrados</span>
            </div>
          </section>

          <section className="panel">
            <div className="admin-navigation">
              <button
                type="button"
                className={
                  adminSection === "users" ? "" : "secondary"
                }
                onClick={async () => {
                  setAdminSection("users");
                  await loadAdminUsers();
                }}
              >
                Usuarios
              </button>

              <button
                type="button"
                className={
                  adminSection === "projects" ? "" : "secondary"
                }
                onClick={async () => {
                  setAdminSection("projects");
                  await loadAdminProjects();
                }}
              >
                Proyectos
              </button>
            </div>
          </section>

          {adminSection === "users" && (
            <section className="panel">
              <div className="section-header">
                <div>
                  <h3>Usuarios registrados</h3>
                  <p>
                    Activa, desactiva o elimina cuentas del sistema.
                  </p>
                </div>

                <button
                  type="button"
                  className="secondary"
                  onClick={loadAdminUsers}
                >
                  Actualizar
                </button>
              </div>

              {!adminUsers.length ? (
                <div className="empty-state">
                  No existen usuarios registrados.
                </div>
              ) : (
                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Usuario</th>
                        <th>Correo</th>
                        <th>Rol</th>
                        <th>Estado</th>
                        <th>Registro</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>

                    <tbody>
                      {adminUsers.map((user) => (
                        <tr key={user.id}>
                          <td>{user.full_name}</td>
                          <td>{user.email}</td>
                          <td>{user.role}</td>

                          <td>
                            <span
                              className={
                                user.is_active
                                  ? "status-badge active"
                                  : "status-badge inactive"
                              }
                            >
                              {user.is_active
                                ? "Activo"
                                : "Inactivo"}
                            </span>
                          </td>

                          <td>
                            {new Date(
                              user.created_at
                            ).toLocaleDateString()}
                          </td>

                          <td>
                            <div className="table-actions">
                              <button
                                type="button"
                                className="secondary"
                                disabled={
                                  loading ||
                                  user.id === currentUser?.id
                                }
                                onClick={() =>
                                  changeUserStatus(user)
                                }
                              >
                                {user.is_active
                                  ? "Desactivar"
                                  : "Activar"}
                              </button>

                              <button
                                type="button"
                                className="danger-button"
                                disabled={
                                  loading ||
                                  user.id === currentUser?.id ||
                                  user.role === "ADMIN"
                                }
                                onClick={() =>
                                  deleteAdminUser(user)
                                }
                              >
                                Eliminar
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}

          {adminSection === "projects" && (
            <section className="panel">
              <div className="section-header">
                <div>
                  <h3>Proyectos registrados</h3>
                  <p>
                    Consulta los objetivos creados por todos los
                    analistas.
                  </p>
                </div>

                <button
                  type="button"
                  className="secondary"
                  onClick={loadAdminProjects}
                >
                  Actualizar
                </button>
              </div>

              {!adminProjects.length ? (
                <div className="empty-state">
                  No existen proyectos registrados.
                </div>
              ) : (
                <div className="admin-table-wrapper">
                  <table className="admin-table">
                    <thead>
                      <tr>
                        <th>Proyecto</th>
                        <th>Objetivo</th>
                        <th>Propietario</th>
                        <th>Correo</th>
                        <th>Registro</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>

                    <tbody>
                      {adminProjects.map((project) => (
                        <tr key={project.id}>
                          <td>{project.name}</td>
                          <td>{project.target_url}</td>
                          <td>{project.owner_name}</td>
                          <td>{project.owner_email}</td>

                          <td>
                            {new Date(
                              project.created_at
                            ).toLocaleDateString()}
                          </td>

                          <td>
                            <button
                              type="button"
                              className="danger-button"
                              disabled={loading}
                              onClick={() =>
                                deleteAdminProject(project)
                              }
                            >
                              Eliminar
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <h1>ApuGuard AI</h1>
          <p>Centro de análisis de seguridad</p>
        </div>

        <div className="topbar-actions">
          {currentUser?.role === "ADMIN" && (
            <button
              type="button"
              className="secondary"
              onClick={openAdminPanel}
            >
              Panel administrativo
            </button>
          )}

          <button
            type="button"
            className="secondary"
            onClick={logout}
          >
            Cerrar sesión
          </button>
        </div>
      </header>

      <main className="dashboard">
        {loading && (
          <div className="loading-banner">
            Procesando solicitud. No cierres esta ventana.
          </div>
        )}

        {message && (
          <div className="alert success">{message}</div>
        )}

        {error && <div className="alert error">{error}</div>}

        <section className="hero-panel">
          <div>
            <span className="eyebrow">OWASP SECURITY PLATFORM</span>
            <h2>Analiza, prioriza y documenta riesgos</h2>
            <p>
              Ejecuta escaneos reales con OWASP ZAP y genera
              informes técnicos y ejecutivos automáticamente.
            </p>
          </div>

          <div className="hero-stat">
            <strong>{projects.length}</strong>
            <span>Proyectos registrados</span>
          </div>
        </section>

        <section className="grid-two">
          <article className="panel">
            <h3>Nuevo proyecto</h3>

            <form onSubmit={createProject}>
              <label>
                Nombre
                <input
                  required
                  minLength="3"
                  value={projectForm.name}
                  onChange={(event) =>
                    setProjectForm({
                      ...projectForm,
                      name: event.target.value,
                    })
                  }
                  placeholder="OWASP Juice Shop"
                />
              </label>

              <label>
                URL autorizada
                <input
                  required
                  value={projectForm.target_url}
                  onChange={(event) =>
                    setProjectForm({
                      ...projectForm,
                      target_url: event.target.value,
                    })
                  }
                />
              </label>

              <label>
                Descripción
                <textarea
                  value={projectForm.description}
                  onChange={(event) =>
                    setProjectForm({
                      ...projectForm,
                      description: event.target.value,
                    })
                  }
                  placeholder="Laboratorio autorizado..."
                />
              </label>

              <button disabled={loading} type="submit">
                Crear proyecto
              </button>
            </form>
          </article>

          <article className="panel report-actions">
            <h3>Reporte de seguridad</h3>

            <p>
              Escaneo seleccionado:{" "}
              <strong>{selectedScanId || "Ninguno"}</strong>
            </p>

            <button
              disabled={loading || !selectedScanId}
              onClick={generateReport}
            >
              Generar reporte
            </button>

            <button
              className="secondary"
              disabled={loading || !selectedScanId}
              onClick={downloadPdf}
            >
              Descargar PDF
            </button>
          </article>
        </section>

        <section className="panel">
          <div className="section-header">
            <div>
              <h3>Mis proyectos</h3>
              <p>Objetivos autorizados para análisis</p>
            </div>

            <button className="secondary" onClick={loadProjects}>
              Actualizar
            </button>
          </div>

          {!projects.length ? (
            <div className="empty-state">
              Todavía no tienes proyectos registrados.
            </div>
          ) : (
            <div className="project-grid">
              {projects.map((project) => (
                <article className="project-card" key={project.id}>
                  <span className="project-id">
                    PROYECTO #{project.id}
                  </span>

                  <h4>{project.name}</h4>

                  <p className="target-url">
                    {project.target_url}
                  </p>

                  <p>
                    {project.description ||
                      "Sin descripción registrada."}
                  </p>

                  <div className="card-actions">
                    <button
                      disabled={loading}
                      onClick={() => startScan(project)}
                    >
                      Ejecutar escaneo
                    </button>

                    <button
                      className="secondary"
                      disabled={loading}
                      onClick={() =>
                        loadLatestScan(project.id)
                      }
                    >
                      Último escaneo
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        {report && (
          <section className="panel report-panel">
            <div className="section-header">
              <div>
                <span className="eyebrow">
                  REPORTE GENERADO
                </span>
                <h3>{report.project_name}</h3>
              </div>

              <span
                className={`risk-badge ${report.overall_risk.toLowerCase()}`}
              >
                Riesgo {report.overall_risk}
              </span>
            </div>

            <div className="severity-grid">
              <div>
                <strong>
                  {report.risk_distribution.critical}
                </strong>
                <span>Críticas</span>
              </div>

              <div>
                <strong>{report.risk_distribution.high}</strong>
                <span>Altas</span>
              </div>

              <div>
                <strong>{report.risk_distribution.medium}</strong>
                <span>Medias</span>
              </div>

              <div>
                <strong>{report.risk_distribution.low}</strong>
                <span>Bajas</span>
              </div>

              <div>
                <strong>
                  {report.risk_distribution.informational}
                </strong>
                <span>Informativas</span>
              </div>
            </div>

            <h4>Resumen ejecutivo</h4>
            <p>{report.executive_summary}</p>

            <h4>Resumen técnico</h4>
            <p>{report.technical_summary}</p>

            <h4>Acciones priorizadas</h4>
            <ol>
              {report.prioritized_actions.map(
                (action, index) => (
                  <li key={`${action}-${index}`}>{action}</li>
                )
              )}
            </ol>

            <h4>Conclusiones</h4>
            <p>{report.conclusions}</p>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;