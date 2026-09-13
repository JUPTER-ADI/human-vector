"use client";

import { FormEvent, useEffect, useState } from "react";

type HealthStatus = "idle" | "loading" | "success" | "error";
type SaveStatus = "idle" | "saving" | "success" | "error";
type SessionsStatus = "loading" | "success" | "error";

type HealthResponse = {
  ok: boolean;
  status: string;
  databaseTime?: string;
};

type HumanVectorSession = {
  id: string;
  objective: string;
  aiAnalysis: string;
  humanDecision: string;
  createdAt: string;
};

type SessionsResponse = {
  ok: boolean;
  sessions?: HumanVectorSession[];
  session?: HumanVectorSession;
  status?: string;
};

const pillars = [
  {
    number: "01",
    title: "Human Direction",
    text: "Omul stabilește scopul, păstrează direcția și decide forma finală.",
  },
  {
    number: "02",
    title: "AI Force",
    text: "AI aduce viteză, masă de analiză, contrast și variante de acțiune.",
  },
  {
    number: "03",
    title: "Verified Action",
    text: "Nicio soluție nu devine acțiune înainte de verificare și decizie umană.",
  },
];

function formatDate(value: string) {
  return new Date(value).toLocaleString("ro-RO");
}

export default function Home() {
  const [healthStatus, setHealthStatus] =
    useState<HealthStatus>("idle");

  const [healthMessage, setHealthMessage] = useState(
    "Ready for live verification",
  );

  const [objective, setObjective] = useState("");
  const [aiAnalysis, setAiAnalysis] = useState("");
  const [humanDecision, setHumanDecision] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionResults, setSessionResults] = useState<unknown>(null);

  const [saveStatus, setSaveStatus] =
    useState<SaveStatus>("idle");

  const [saveMessage, setSaveMessage] = useState(
    "Completează obiectivul pentru a crea o sesiune.",
  );

  const [sessionsStatus, setSessionsStatus] =
    useState<SessionsStatus>("loading");

  const [sessions, setSessions] = useState<
    HumanVectorSession[]
  >([]);

  async function loadSessions() {
    setSessionsStatus("loading");

    try {
      const response = await fetch("/api/sessions", {
        cache: "no-store",
      });

      const data = (await response.json()) as SessionsResponse;

      if (!response.ok || !data.ok || !data.sessions) {
        throw new Error(data.status || "SESSIONS_READ_FAILED");
      }

      setSessions(data.sessions);
      setSessionsStatus("success");
    } catch (error) {
      console.error("Loading sessions failed:", error);
      setSessionsStatus("error");
    }
  }

  useEffect(() => {
    void loadSessions();
  }, []);

  async function verifyDatabase() {
    setHealthStatus("loading");
    setHealthMessage("Verifying CockroachDB connection...");

    try {
      const response = await fetch("/api/health", {
        cache: "no-store",
      });

      const data = (await response.json()) as HealthResponse;

      if (!response.ok || !data.ok) {
        throw new Error(data.status || "HEALTH_CHECK_FAILED");
      }

      const databaseTime = data.databaseTime
        ? new Date(data.databaseTime).toLocaleString("ro-RO")
        : "time confirmed";

      setHealthStatus("success");
      setHealthMessage(
        `CockroachDB connected · ${databaseTime}`,
      );
    } catch (error) {
      console.error("Health verification failed:", error);
      setHealthStatus("error");
      setHealthMessage("Connection failed — check Terminal");
    }
  }

  async function saveSession(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const cleanObjective = objective.trim();

    if (!cleanObjective) {
      setSaveStatus("error");
      setSaveMessage("Obiectivul uman este obligatoriu.");
      return;
    }

    setSaveStatus("saving");
    setSaveMessage("Saving verified HUMAN VECTOR session...");

    try {
      const response = await fetch("/api/human-vector/sessions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_id: "ui-local-human",
          actor_id: "ui-local-human",
          actor_role: "HUMAN",
        }),
      });

      const data = (await response.json()) as {
        ok?: boolean;
        session_id?: string;
        user_id?: string;
        actor_id?: string;
        actor_role?: string;
        state?: string;
        revision?: number;
        detail?: string;
      };

      if (!response.ok || !data.ok || !data.session_id) {
        throw new Error(data.detail || "HUMAN_VECTOR_SESSION_CREATE_FAILED");
      }

      setSessionId(data.session_id);
    await loadHumanVectorResults(data.session_id);
    setObjective("");
      setAiAnalysis("");
      setHumanDecision("");

      setSaveStatus("success");
      setSaveMessage(
        `Sesiune HUMAN VECTOR creată în CORE: ${data.session_id}`,
      );
    } catch (error) {
      console.error("Saving session failed:", error);
      setSaveStatus("error");
      setSaveMessage("Salvarea a eșuat — verifică Terminalul.");
    }
  }

  async function loadHumanVectorResults(targetSessionId?: string) {
    const activeSessionId = targetSessionId ?? sessionId;
    if (!activeSessionId) {
      return;
    }

    const response = await fetch(
      `/api/human-vector/sessions/${activeSessionId}/results?user_id=ui-local-human`,
      { cache: "no-store" }
    );

    if (!response.ok) {
      throw new Error("HUMAN_VECTOR_RESULTS_READ_FAILED");
    }

    const data = await response.json();
    setSessionResults(data);
    return data;
  }

  const healthButtonLabel =
    healthStatus === "loading"
      ? "Verifying..."
      : healthStatus === "success"
        ? "Verify Again"
        : healthStatus === "error"
          ? "Retry Verification"
          : "Verify CockroachDB";

  return (
    <main className="min-h-screen bg-[#07111f] text-white">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-8 sm:px-10 lg:px-16">
        <header className="flex items-center justify-between border-b border-white/10 pb-6">
          <div>
            <p className="text-sm font-semibold tracking-[0.35em] text-cyan-300">
              HUMAN VECTOR
            </p>

            <p className="mt-1 text-xs tracking-[0.2em] text-slate-400">
              HUMAN-IN-COMMAND PROTOCOL
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-4 py-2 text-xs text-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-400" />
            SYSTEM READY
          </div>
        </header>

        <section className="py-16">
          <p className="mb-5 text-sm font-medium tracking-[0.3em] text-cyan-300">
            DIRECTION BEFORE AUTOMATION
          </p>

          <h1 className="max-w-4xl text-5xl font-semibold leading-tight tracking-tight sm:text-6xl lg:text-7xl">
            The human sets the vector.
            <span className="block text-slate-400">
              AI amplifies the force.
            </span>
          </h1>

          <p className="mt-8 max-w-2xl text-lg leading-8 text-slate-300">
            HUMAN VECTOR păstrează omul în centrul analizei,
            coordonării și deciziei. AI este instrumentul de
            accelerare, nu autoritatea finală.
          </p>

          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {pillars.map((pillar) => (
              <article
                key={pillar.number}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-6"
              >
                <p className="text-sm font-semibold text-cyan-300">
                  {pillar.number}
                </p>

                <h2 className="mt-5 text-xl font-semibold">
                  {pillar.title}
                </h2>

                <p className="mt-3 leading-7 text-slate-400">
                  {pillar.text}
                </p>
              </article>
            ))}
          </div>

          <div className="mt-10 flex flex-col gap-4 sm:flex-row sm:items-center">
            <button
              type="button"
              onClick={verifyDatabase}
              disabled={healthStatus === "loading"}
              className="rounded-xl bg-cyan-300 px-7 py-4 font-semibold text-[#07111f] transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60"
            >
              {healthButtonLabel}
            </button>

            <div
              className={`rounded-xl border px-5 py-4 text-sm ${
                healthStatus === "success"
                  ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                  : healthStatus === "error"
                    ? "border-red-400/30 bg-red-400/10 text-red-300"
                    : healthStatus === "loading"
                      ? "border-cyan-300/30 bg-cyan-300/10 text-cyan-200"
                      : "border-white/10 text-slate-400"
              }`}
            >
              {healthMessage}
            </div>
          </div>
        </section>

        <section className="border-t border-white/10 py-14">
          <p className="text-sm font-medium tracking-[0.3em] text-cyan-300">
            HUMAN VECTOR SESSION
          </p>

          <h2 className="mt-4 text-3xl font-semibold">
            Human objective. AI analysis. Human decision.
          </h2>

          <form
            onSubmit={saveSession}
            className="mt-8 grid gap-6"
          >
            <label className="grid gap-2">
              <span className="text-sm font-semibold text-slate-200">
                1. Obiectivul stabilit de om
              </span>

              <textarea
                value={objective}
                onChange={(event) =>
                  setObjective(event.target.value)
                }
                rows={3}
                placeholder="Scrie obiectivul real al sesiunii..."
                className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
              />
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-semibold text-slate-200">
                2. Analiza și variantele furnizate de AI
              </span>

              <textarea
                value={aiAnalysis}
                onChange={(event) =>
                  setAiAnalysis(event.target.value)
                }
                rows={5}
                placeholder="Scrie analiza, contrastul și variantele de acțiune..."
                className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
              />
            </label>

            <label className="grid gap-2">
              <span className="text-sm font-semibold text-slate-200">
                3. Decizia verificată și asumată de om
              </span>

              <textarea
                value={humanDecision}
                onChange={(event) =>
                  setHumanDecision(event.target.value)
                }
                rows={4}
                placeholder="Scrie decizia finală verificată de om..."
                className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
              />
            </label>

            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
              <button
                type="submit"
                disabled={saveStatus === "saving"}
                className="rounded-xl bg-cyan-300 px-7 py-4 font-semibold text-[#07111f] transition hover:bg-cyan-200 disabled:cursor-wait disabled:opacity-60"
              >
                {saveStatus === "saving"
                  ? "Saving Session..."
                  : "Save Verified Session"}
              </button>

              <div
                className={`rounded-xl border px-5 py-4 text-sm ${
                  saveStatus === "success"
                    ? "border-emerald-400/30 bg-emerald-400/10 text-emerald-300"
                    : saveStatus === "error"
                      ? "border-red-400/30 bg-red-400/10 text-red-300"
                      : saveStatus === "saving"
                        ? "border-cyan-300/30 bg-cyan-300/10 text-cyan-200"
                        : "border-white/10 text-slate-400"
                }`}
              >
                {saveMessage}
              {sessionResults !== null && (
                <div className="mt-4 rounded-2xl border border-cyan-300/30 bg-cyan-300/10 p-4">
                  <p className="text-xs font-semibold tracking-[0.3em] text-cyan-300">
                    LIVE CORE SESSION RESULT
                  </p>
                  <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-xs text-slate-300">
                    {JSON.stringify(sessionResults, null, 2)}
                  </pre>
                </div>
              )}
              </div>
            </div>
          </form>
        </section>

        <section className="border-t border-white/10 py-14">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-sm font-medium tracking-[0.3em] text-cyan-300">
                VERIFIED MEMORY
              </p>

              <h2 className="mt-4 text-3xl font-semibold">
                Saved HUMAN VECTOR sessions
              </h2>
            </div>

            <button
              type="button"
              onClick={() => void loadSessions()}
              className="rounded-xl border border-white/10 px-5 py-3 text-sm text-slate-300 transition hover:border-cyan-300/40 hover:text-cyan-200"
            >
              Reload Sessions
            </button>
          </div>

          <div className="mt-8 grid gap-5">
            {sessionsStatus === "loading" && (
              <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 text-slate-400">
                Loading verified sessions...
              </div>
            )}

            {sessionsStatus === "error" && (
              <div className="rounded-2xl border border-red-400/30 bg-red-400/10 p-6 text-red-300">
                Sessions could not be loaded.
              </div>
            )}

            {sessionsStatus === "success" &&
              sessions.length === 0 && (
                <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-6 text-slate-400">
                  No session has been saved yet.
                </div>
              )}

            {sessions.map((session) => (
              <article
                key={session.id}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-6"
              >
                <div className="flex flex-col gap-2 border-b border-white/10 pb-4 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs tracking-[0.2em] text-cyan-300">
                    VERIFIED SESSION
                  </p>

                  <time className="text-xs text-slate-500">
                    {formatDate(session.createdAt)}
                  </time>
                </div>

                <div className="mt-5 grid gap-5">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Human objective
                    </p>

                    <p className="mt-2 leading-7 text-slate-200">
                      {session.objective}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      AI analysis
                    </p>

                    <p className="mt-2 whitespace-pre-wrap leading-7 text-slate-400">
                      {session.aiAnalysis || "No AI analysis recorded."}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
                      Human decision
                    </p>

                    <p className="mt-2 whitespace-pre-wrap leading-7 text-emerald-300">
                      {session.humanDecision ||
                        "No human decision recorded."}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        <footer className="border-t border-white/10 pt-6 text-xs tracking-[0.18em] text-slate-500">
          HUMAN DIRECTION · AI CAPABILITY · VERIFIED DECISION
        </footer>
      </div>
    </main>
  );
}