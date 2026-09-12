import { NextResponse } from "next/server";

function getHumanVectorApiUrl(): string {
  const value = process.env.HUMAN_VECTOR_API_URL?.trim();

  if (!value) {
    throw new Error("HUMAN_VECTOR_API_URL is not configured");
  }

  return value.replace(/\/+$/, "");
}

export async function GET(
  request: Request,
  context: { params: Promise<{ sessionId: string }> },
) {
  try {
    const { sessionId } = await context.params;
    const { searchParams } = new URL(request.url);
    const userId = searchParams.get("user_id");

    if (!userId) {
      return NextResponse.json(
        {
          error: "HUMAN_VECTOR_USER_ID_REQUIRED",
          detail: "user_id is required",
        },
        { status: 400 },
      );
    }

    const apiUrl = getHumanVectorApiUrl();
    const target =
      `${apiUrl}/human-vector/sessions/${encodeURIComponent(sessionId)}` +
      `?user_id=${encodeURIComponent(userId)}`;

    const response = await fetch(target, {
      method: "GET",
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
        error: "HUMAN_VECTOR_SESSION_PROXY_ERROR",
        detail: message,
      },
      { status: 503 },
    );
  }
}
