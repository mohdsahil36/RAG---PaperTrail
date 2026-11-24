const BACKEND = (process.env.API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/+$/, "");

// Route Handler so Next.js streams the SSE body instead of buffering it.
// The rewrite in next.config.ts would buffer the full response before forwarding;
// a Route Handler returns response.body directly, so tokens reach the browser live.
export async function POST(request: Request) {
  const payload = await request.json();
  const upstream = await fetch(`${BACKEND}/answer/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const { body } = upstream;
  if (!body) return new Response("No stream from backend.", { status: 502 });

  // Explicitly pipe so Next.js dev server doesn't buffer the body before sending
  const piped = new ReadableStream({
    async start(controller) {
      const reader = body.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } finally {
        controller.close();
      }
    },
  });

  return new Response(piped, {
    status: upstream.status,
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      "X-Accel-Buffering": "no",
    },
  });
}
