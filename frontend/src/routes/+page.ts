import type { PageLoad } from './$types';

export const prerender = true;

export interface BankAttempt {
	comment_id: string;
	method: string;
	success: boolean;
	timestamp: number;
}

export interface BankData {
	[bankName: string]: BankAttempt[];
}

export interface Metadata {
	lastUpdated: number;
}

export const load: PageLoad = async ({ fetch }) => {
	const [dataResponse, metadataResponse] = await Promise.all([
		fetch('/by_bank.json'),
		fetch('/metadata.json')
	]);
	const data: BankData = await dataResponse.json();
	const metadata: Metadata = await metadataResponse.json();
	return { banks: data, metadata };
};
