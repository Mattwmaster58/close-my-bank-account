import type { BankAttempt } from '../routes/+page';

/** Per-method effort level (lower = easier). */
const EFFORT: Record<string, number> = {
	'on-platform': 1,
	'secure-message': 2,
	chat: 3,
	phone: 4,
	'in-branch': 5,
	'0-balance': 2,
	unknown: 3,
};

/**
 * Effort bias multiplier.
 * Easiest methods get ×1.5, hardest get ×1.0.
 * `0-balance` is explicitly set to ×1.0 despite being low-effort.
 */
export function effortBias(method: string): number {
	if (method === '0-balance') return 1.0;
	const effort = EFFORT[method] ?? 3;
	return 1.5 - (effort - 1) * (0.5 / 4);
}

/**
 * Confidence weight based on number of datapoints.
 * Prevents single-datapoint methods from unfairly outranking well-sampled ones.
 *   n=1 → 0.250, n=3 → 0.500, n=5 → 0.625, n=10 → 0.769, n=20+ → ~0.870
 */
export function confidenceWeight(n: number): number {
	const k = 3;
	return n / (n + k);
}

/**
 * Exponential recency decay from the bank's most recent datapoint.
 * τ = 1.5 years: after 1.5 years the weight decays to e⁻¹ ≈ 0.37.
 */
export function recencyDecay(timestamp: number, maxTimestamp: number, tauYears = 1.5): number {
	const ageSeconds = maxTimestamp - timestamp;
	const ageYears = ageSeconds / (365.25 * 24 * 3600);
	return Math.exp(-ageYears / tauYears);
}

export interface MethodScore {
	method: string;
	successCount: number;
	failCount: number;
	total: number;
	decayingMean: number;
	bias: number;
	confidence: number;
	score: number;
}

/**
 * Compute the intelligent score for a single method's datapoints.
 *
 * Each DP contributes:
 *   +decay_weight on success,  -decay_weight on failure
 *
 * The raw sum of decay-weighted votes is multiplied by:
 *   effortBias  (1.5× for easiest, 1.0× for hardest)
 *   confidenceWeight  (n/(n+3))
 *
 * An unnormalised sum is used (not a mean) so that old data naturally
 * contributes almost nothing — a method whose last DP was years ago
 * won't outrank a method with recent data, even if the old data is
 * all successes.
 */
export function computeMethodScore(attempts: BankAttempt[], maxBankTimestamp: number): MethodScore {
	const successes = attempts.filter((a) => a.success).length;
	const fails = attempts.length - successes;

	let rawSum = 0;

	for (const a of attempts) {
		const decay = recencyDecay(a.timestamp, maxBankTimestamp);
		const value = a.success ? 1 : -1;
		rawSum += value * decay;
	}

	const bias = effortBias(attempts[0].method);
	const confidence = confidenceWeight(attempts.length);
	const score = rawSum * bias * confidence;

	return {
		method: attempts[0].method,
		successCount: successes,
		failCount: fails,
		total: attempts.length,
		decayingMean: rawSum,
		bias,
		confidence,
		score,
	};
}

/**
 * Compute scores for all methods of a bank, sorted descending by score.
 */
export function computeAllMethodScores(attempts: BankAttempt[]): MethodScore[] {
	if (attempts.length === 0) return [];

	const maxBankTimestamp = Math.max(...attempts.map((a) => a.timestamp));

	const groups = new Map<string, BankAttempt[]>();
	for (const a of attempts) {
		const list = groups.get(a.method);
		if (list) list.push(a);
		else groups.set(a.method, [a]);
	}

	const scores: MethodScore[] = [];
	for (const [, groupAttempts] of groups) {
		scores.push(computeMethodScore(groupAttempts, maxBankTimestamp));
	}

	return scores.sort((a, b) => b.score - a.score);
}

/**
 * Get the best (highest) method score for a bank — useful for bank-level tiebreaking.
 */
export function getBestMethodScore(attempts: BankAttempt[]): number {
	const scores = computeAllMethodScores(attempts);
	if (scores.length === 0) return -Infinity;
	return scores[0].score;
}
