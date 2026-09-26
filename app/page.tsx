"use client";

import { FormEvent, useEffect, useState } from "react";

import HumanVectorResultSurface from "./components/HumanVectorResultSurface";
type HealthStatus = "idle" | "loading" | "success" | "error";
type SaveStatus = "idle" | "saving" | "success" | "error";
type HealthResponse = {
  ok: boolean;
  status: string;
  databaseTime?: string;
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

export default function Home() {
  const [healthStatus, setHealthStatus] =
    useState<HealthStatus>("idle");

  const [healthMessage, setHealthMessage] = useState(
    "Ready for live verification",
  );

  const [objective, setObjective] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [directionContext, setDirectionContext] = useState("");
  const [directionCriteria, setDirectionCriteria] = useState("");
  const [directionLimits, setDirectionLimits] = useState("");
  const [vectorRunStatus, setVectorRunStatus] = useState<
    "idle" | "running" | "success" | "error"
  >("idle");
  const [vectorRunMessage, setVectorRunMessage] = useState("");
  const [sessionResults, setSessionResults] = useState<unknown>(null);

  const [saveStatus, setSaveStatus] =
    useState<SaveStatus>("idle");

  const [saveMessage, setSaveMessage] = useState(
    "Completează obiectivul pentru a crea o sesiune.",
  );

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

    async function runHumanVectorDirection() {
    const cleanObjective = objective.trim();

    if (!cleanObjective) {
      setVectorRunStatus("error");
      setVectorRunMessage("Obiectivul HUMAN este obligatoriu.");
      return;
    }

    setSessionResults(null);
    setVectorRunStatus("running");
    setVectorRunMessage("Builder + Selector rulează...");

    try {
      const createResponse = await fetch("/api/human-vector/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "ui-local-human",
          actor_id: "ui-local-human",
          actor_role: "HUMAN",
        }),
      });

      const createData = await createResponse.json();

      if (!createResponse.ok || !createData?.session_id) {
        throw new Error(
          createData?.detail ||
            createData?.status ||
            "HUMAN_VECTOR_SESSION_CREATE_FAILED",
        );
      }

      const newSessionId = String(createData.session_id);
      setSessionId(newSessionId);

      const directionResponse = await fetch(
        `/api/human-vector/sessions/${newSessionId}/direction`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: "ui-local-human",
            objective: cleanObjective,
            context: directionContext.trim(),
            criteria: directionCriteria.trim(),
            limits: directionLimits.trim(),
          }),
        },
      );

      const directionData = await directionResponse.json();

      if (!directionResponse.ok) {
        throw new Error(
          directionData?.detail || "HUMAN_DIRECTION_RECORD_FAILED",
        );
      }

      const confirmResponse = await fetch(
        `/api/human-vector/sessions/${newSessionId}/direction/confirm`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: "ui-local-human",
          }),
        },
      );

      const confirmData = await confirmResponse.json();

      if (!confirmResponse.ok) {
        throw new Error(
          confirmData?.detail || "HUMAN_DIRECTION_CONFIRM_FAILED",
        );
      }

      const builderResponse = await fetch(
        `/api/human-vector/sessions/${newSessionId}/builder-v1`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: "ui-local-human",
          }),
        },
      );

      const builderData = await builderResponse.json();

      if (!builderResponse.ok) {
        throw new Error(
          builderData?.detail || "HUMAN_VECTOR_BUILDER_SELECTOR_FAILED",
        );
      }

      setSessionResults(builderData);
      setVectorRunStatus("success");

      const selectorDecision =
        typeof builderData?.selector_decision === "string"
          ? builderData.selector_decision
          : "COMPLETED";

      setVectorRunMessage(
        `Builder + Canonical Selector: ${selectorDecision}`,
      );
    } catch (error) {
      console.error("HUMAN VECTOR run failed:", error);
      setVectorRunStatus("error");
      setVectorRunMessage(
        error instanceof Error
          ? error.message
          : "HUMAN_VECTOR_RUN_FAILED",
      );
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

            <div className="grid gap-4">
        <label className="grid gap-2">
          <span className="text-sm font-semibold text-slate-200">
            2. Context HUMAN
          </span>
          <textarea
            value={directionContext}
            onChange={(event) => setDirectionContext(event.target.value)}
            rows={3}
            placeholder="Contextul relevant pentru această direcție..."
            className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-semibold text-slate-200">
            3. Criterii HUMAN
          </span>
          <textarea
            value={directionCriteria}
            onChange={(event) => setDirectionCriteria(event.target.value)}
            rows={3}
            placeholder="Criteriile pe care rezultatul trebuie să le respecte..."
            className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
          />
        </label>

        <label className="grid gap-2">
          <span className="text-sm font-semibold text-slate-200">
            4. Limite HUMAN
          </span>
          <textarea
            value={directionLimits}
            onChange={(event) => setDirectionLimits(event.target.value)}
            rows={3}
            placeholder="Limitele stabilite de HUMAN pentru execuția AI..."
            className="rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-4 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-300/60"
          />
        </label>

        <button
          type="button"
          onClick={() => void runHumanVectorDirection()}
          disabled={vectorRunStatus === "running"}
          className="rounded-2xl border border-cyan-300/50 bg-cyan-300/10 px-5 py-4 font-semibold text-white transition hover:bg-cyan-300/20 disabled:cursor-wait disabled:opacity-60"
        >
          {vectorRunStatus === "running"
            ? "Builder + Selector rulează..."
            : "Pornește HUMAN VECTOR"}
        </button>

        {vectorRunMessage && (
          <p role="status" className="text-sm text-slate-300">
            {vectorRunMessage}
          </p>
        )}
      </div>



            <div className="flex flex-col gap-4 sm:flex-row sm:items-center">


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
                  <HumanVectorResultSurface data={sessionResults} />
                </div>
              )}
              </div>
            </div>
          </form>
        </section>

        <footer className="border-t border-white/10 pt-6 text-xs tracking-[0.18em] text-slate-500">
          HUMAN DIRECTION · AI CAPABILITY · VERIFIED DECISION
        </footer>
      </div>
    </main>
  );
}