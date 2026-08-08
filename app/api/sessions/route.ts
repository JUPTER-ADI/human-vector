import { Client } from "pg";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type SessionInput = {
  objective?: unknown;
  analysis?: unknown;
  decision?: unknown;
};

function createClient() {
  const databaseUrl = process.env.DATABASE_URL;

  if (!databaseUrl) {
    throw new Error("DATABASE_URL_MISSING");
  }

  const url = new URL(databaseUrl);

  url.searchParams.set(
    "sslrootcert",
    `${process.env.HOME}/.postgresql/root.crt`,
  );

  return new Client({
    connectionString: url.toString(),
  });
}

async function ensureSessionsTable(client: Client) {
  await client.query(`
    CREATE TABLE IF NOT EXISTS public.human_vector_sessions (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      objective STRING NOT NULL,
      ai_analysis STRING NOT NULL DEFAULT '',
      human_decision STRING NOT NULL DEFAULT '',
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
  `);
}

export async function GET() {
  let client: Client | null = null;

  try {
    client = createClient();
    await client.connect();
    await ensureSessionsTable(client);

    const result = await client.query(`
      SELECT
        id,
        objective,
        ai_analysis AS "aiAnalysis",
        human_decision AS "humanDecision",
        created_at AS "createdAt"
      FROM public.human_vector_sessions
      ORDER BY created_at DESC
      LIMIT 20
    `);

    return Response.json({
      ok: true,
      sessions: result.rows,
    });
  } catch (error) {
    console.error("Reading sessions failed:", error);

    return Response.json(
      {
        ok: false,
        status: "SESSIONS_READ_FAILED",
      },
      { status: 500 },
    );
  } finally {
    await client?.end().catch(() => {});
  }
}

export async function POST(request: Request) {
  let client: Client | null = null;

  try {
    const body = (await request.json()) as SessionInput;

    const objective =
      typeof body.objective === "string"
        ? body.objective.trim()
        : "";

    const analysis =
      typeof body.analysis === "string"
        ? body.analysis.trim()
        : "";

    const decision =
      typeof body.decision === "string"
        ? body.decision.trim()
        : "";

    if (!objective) {
      return Response.json(
        {
          ok: false,
          status: "OBJECTIVE_REQUIRED",
        },
        { status: 400 },
      );
    }

    client = createClient();
    await client.connect();
    await ensureSessionsTable(client);

    const result = await client.query(
      `
        INSERT INTO public.human_vector_sessions (
          objective,
          ai_analysis,
          human_decision
        )
        VALUES ($1, $2, $3)
        RETURNING
          id,
          objective,
          ai_analysis AS "aiAnalysis",
          human_decision AS "humanDecision",
          created_at AS "createdAt"
      `,
      [objective, analysis, decision],
    );

    return Response.json(
      {
        ok: true,
        session: result.rows[0],
      },
      { status: 201 },
    );
  } catch (error) {
    console.error("Saving session failed:", error);

    return Response.json(
      {
        ok: false,
        status: "SESSION_SAVE_FAILED",
      },
      { status: 500 },
    );
  } finally {
    await client?.end().catch(() => {});
  }
}