"use client";

import { useState } from "react";

type HealthStatus = "idle" | "loading" | "success" | "error";

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
      setHealthMessage(`CockroachDB connected · ${databaseTime}`);
    } catch (error) {
      console.error("Health verification failed:", error);
      setHealthStatus("error");
      setHealthMessage("Connection failed — check Terminal");
    }
  }

  const buttonLabel =
    healthStatus === "loading"
      ? "Verifying..."
      : healthStatus === "success"
        ? "Verify Again"
        : healthStatus === "error"
          ? "Retry Verification"
          : "Start Human Vector";

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

        <section className="flex flex-1 flex-col justify-center py-16">
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
              {buttonLabel}
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

        <footer className="border-t border-white/10 pt-6 text-xs tracking-[0.18em] text-slate-500">
          HUMAN DIRECTION · AI CAPABILITY · VERIFIED DECISION
        </footer>
      </div>
    </main>
  );
}