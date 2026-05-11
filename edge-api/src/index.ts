type JsonRecord = Record<string, unknown>;

function json(data: JsonRecord, status = 200): Response {
	return Response.json(data, {
		status,
		headers: {
			"cache-control": "no-store",
		},
	});
}

function getPath(request: Request): string {
	return new URL(request.url).pathname;
}

export interface Env {
	APP_NAME: string;
	COURSE_NAME: string;
	DEPLOYMENT_STAGE: string;
	API_TOKEN: string;
	ADMIN_EMAIL: string;
	SETTINGS: KVNamespace;
}

export default {
	async fetch(request: Request, env: Env): Promise<Response> {
		const url = new URL(request.url);
		const path = getPath(request);
		const now = new Date().toISOString();
		const cf = request.cf ?? {};

		// Required by lab task: example production log entry with edge metadata.
		console.log("request", {
			method: request.method,
			path,
			colo: cf.colo,
			country: cf.country,
			stage: env.DEPLOYMENT_STAGE,
		});

		if (path === "/health" && request.method === "GET") {
			return json({
				status: "ok",
				app: env.APP_NAME,
				stage: env.DEPLOYMENT_STAGE,
				timestamp: now,
			});
		}

		if (path === "/" && request.method === "GET") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				stage: env.DEPLOYMENT_STAGE,
				message: "Hello from Cloudflare Workers",
				routes: ["/", "/health", "/edge", "/counter", "/config"],
				timestamp: now,
			});
		}

		if (path === "/edge" && request.method === "GET") {
			return json({
				colo: cf.colo ?? null,
				country: cf.country ?? null,
				city: cf.city ?? null,
				asn: cf.asn ?? null,
				httpProtocol: cf.httpProtocol ?? null,
				tlsVersion: cf.tlsVersion ?? null,
				timestamp: now,
			});
		}

		if (path === "/config" && request.method === "GET") {
			return json({
				app: env.APP_NAME,
				course: env.COURSE_NAME,
				stage: env.DEPLOYMENT_STAGE,
				admin_email_configured: Boolean(env.ADMIN_EMAIL),
				api_token_configured: Boolean(env.API_TOKEN),
				// Never expose secret values; only expose presence.
			});
		}

		if (path === "/counter" && request.method === "GET") {
			const raw = await env.SETTINGS.get("visits");
			const visits = Number(raw ?? "0") + 1;
			await env.SETTINGS.put("visits", String(visits));
			return json({ visits, persisted: true, timestamp: now });
		}

		if (path === "/counter/reset" && request.method === "POST") {
			await env.SETTINGS.put("visits", "0");
			return json({ visits: 0, reset: true, timestamp: now });
		}

		return json(
			{
				error: "Not Found",
				path: url.pathname,
				method: request.method,
			},
			404,
		);
	},
} satisfies ExportedHandler<Env>;
