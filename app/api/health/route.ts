import { Client } from "pg";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const databaseUrl = process.env.DATABASE_URL;

  if (!databaseUrl) {
    return Response.json(
      {
        ok: false,
        status: "DATABASE_URL_MISSING",
      },
      { status: 500 },
    );
  }

  const url = new URL(databaseUrl);
  url.searchParams.set(
    "sslrootcert",
    `${process.env.HOME}/.postgresql/root.crt`,
  );

  const client = new Client({
    connectionString: url.toString(),
  });

  try {
    await client.connect();
    const result = await client.query(
      "SELECT current_timestamp AS database_time",
    );

    return Response.json({
      ok: true,
      status: "COCKROACHDB_CONNECTED",
      databaseTime: result.rows[0].database_time,
    });
  } catch (error) {
    console.error("Database health check failed:", error);

    return Response.json(
      {
        ok: false,
        status: "COCKROACHDB_CONNECTION_FAILED",
      },
      { status: 500 },
    );
  } finally {
    await client.end().catch(() => {});
  }
}