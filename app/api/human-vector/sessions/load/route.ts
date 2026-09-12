import { NextResponse } from "next/server";

function getHumanVectorApiUrl(): string {
  const value = process.env.HUMAN_VECTOR_API_URL?.trim();

  if (!value) {
    throw new Error("HUMAN_VECTOR_API_URL is not configured");
  }

  return value.replace(/\/+$/, "");
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const apiUrl = getHumanVectorApiUrl();

    const response = await fetch(`${apiUrl}/human-vector/sessions/load`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const text = await response.text();

    return new NextResponse(text, {
      status: response.status,
      headers: {
        "Content-Type":
          response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown proxy error";

    return NextResponse.json(
      {
        error: "HUMAN_VECTOR_SESSION_LOAD_PROXY_ERROR",
        detail: message,
      },
      { status: 503 },
    );
  }
}
