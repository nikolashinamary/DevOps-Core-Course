import {
	createExecutionContext,
	waitOnExecutionContext,
	SELF,
} from "cloudflare:test";
import { describe, it, expect } from "vitest";
import worker from "../src/index";

const IncomingRequest = Request<unknown, IncomingRequestCfProperties>;

class MemoryKV {
	private readonly store = new Map<string, string>();
	async get(key: string): Promise<string | null> {
		return this.store.has(key) ? this.store.get(key)! : null;
	}
	async put(key: string, value: string): Promise<void> {
		this.store.set(key, value);
	}
}

const unitEnv = {
	APP_NAME: "devops-core-edge-api",
	COURSE_NAME: "devops-core",
	DEPLOYMENT_STAGE: "test",
	API_TOKEN: "token-present",
	ADMIN_EMAIL: "admin@example.com",
	SETTINGS: new MemoryKV() as unknown as KVNamespace,
};

describe("Edge API worker", () => {
	it("returns app metadata on / (unit style)", async () => {
		const request = new IncomingRequest("http://example.com");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, unitEnv, ctx);
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(200);
		const body = (await response.json()) as Record<string, unknown>;
		expect(body.app).toBe("devops-core-edge-api");
		expect(body.routes).toBeTruthy();
	});

	it("increments KV-backed counter on /counter (unit style)", async () => {
		const request = new IncomingRequest("http://example.com/counter");
		const ctx = createExecutionContext();
		const first = await worker.fetch(request, unitEnv, ctx);
		const second = await worker.fetch(request, unitEnv, ctx);
		await waitOnExecutionContext(ctx);
		expect((await first.json()) as Record<string, unknown>).toMatchObject({ visits: 1 });
		expect((await second.json()) as Record<string, unknown>).toMatchObject({ visits: 2 });
	});

	it("returns not found for unknown route (unit style)", async () => {
		const request = new IncomingRequest("http://example.com/does-not-exist");
		const ctx = createExecutionContext();
		const response = await worker.fetch(request, unitEnv, ctx);
		await waitOnExecutionContext(ctx);
		expect(response.status).toBe(404);
	});

	it("responds with health payload (integration style)", async () => {
		const response = await SELF.fetch("https://example.com/health");
		expect(response.status).toBe(200);
		const body = (await response.json()) as Record<string, unknown>;
		expect(body.status).toBe("ok");
	});

	it("responds with edge payload (integration style)", async () => {
		const response = await SELF.fetch("https://example.com/edge");
		expect(response.status).toBe(200);
		const body = (await response.json()) as Record<string, unknown>;
		expect(body).toHaveProperty("country");
	});

	it("responds with route metadata (integration style)", async () => {
		const response = await SELF.fetch("https://example.com");
		expect(response.status).toBe(200);
		const body = (await response.json()) as Record<string, unknown>;
		expect(body).toHaveProperty("routes");
	});
});
