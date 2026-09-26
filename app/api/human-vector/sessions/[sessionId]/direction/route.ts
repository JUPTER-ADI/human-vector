import { NextRequest, NextResponse } from "next/server";

const API_BASE =
  process.env.HUMAN_VECTOR_API_BASE_URL ??
  process.env.HUMAN_VECTOR_API_URL ??
  "http://127.0.0.1:8000";

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ sessionId: string }> },
) {
  const { sessionId } = await context.params;
  const body = await request.json();

  const response = await fetch(
    `${API_BASE}/human-vector/sessions/${encodeURIComponent(sessionId)}/direction`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
    },
  );

  const text = await response.text();

  return new NextResponse(text, {
    status: response.status,
    headers: {
      "Content-Type":
        response.headers.get("content-type") ?? "application/json",
    },
  });
}
